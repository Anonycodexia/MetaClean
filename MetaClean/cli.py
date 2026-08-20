from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .cleaners import CleanerBase
from .config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DetectedFile,
    RuntimeOptions,
    default_output_path,
    is_ci_environment,
)
from .dependencies import (
    DependencyResult,
    attempt_install,
    check_all_tools,
    recheck_tool,
)
from .detector import detect_file, is_supported_format
from .metadata import (
    MetadataSnapshot,
    inspect_metadata,
    snapshot_to_json,
)
from .platform import detect_environment
from .router import RoutingDecision, route
from .ui import ColorPalette, Output, should_enable_color
from .verification import verify_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME.lower(),
        description=f"{APP_NAME} - {APP_TAGLINE}",
        add_help=True,
    )
    parser.add_argument("file", nargs="?", default=None, help="Path to the file to inspect/clean.")
    parser.add_argument("--scan", action="store_true", help="Only scan metadata; do not prompt to clean.")
    parser.add_argument("--clean", action="store_true", help="Clean metadata without interactive prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen; do not write anything.")
    parser.add_argument("--output", "-o", default=None, help="Explicit output file path.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes.")
    parser.add_argument("--no-animation", action="store_true", help="Disable spinners and progress bars.")
    parser.add_argument("--verbose", action="store_true", help="Show all metadata fields.")
    parser.add_argument("--debug", action="store_true", help="Show technical error details.")
    parser.add_argument("--yes", "-y", action="store_true", help="Answer yes to all prompts (non-interactive).")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process a directory recursively (preview only).")
    parser.add_argument("--install-deps", action="store_true", help="Offer to install missing dependencies automatically.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{APP_VERSION}")
    return parser


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, RuntimeOptions]:
    parser = build_parser()
    namespace = parser.parse_args(argv)
    options = RuntimeOptions(
        no_color=namespace.no_color,
        no_animation=namespace.no_animation,
        verbose=namespace.verbose,
        debug=namespace.debug,
        dry_run=namespace.dry_run,
        json_output=namespace.json,
        yes=namespace.yes,
        scan_only=namespace.scan,
        clean_only=namespace.clean,
        install_deps=namespace.install_deps,
        output_path=namespace.output,
        recursive=namespace.recursive,
        input_path=namespace.file,
    )
    return namespace, options


class MetaCleanApp:
    def __init__(self, options: RuntimeOptions):
        self.options = options
        color_enabled = should_enable_color(options.no_color)
        self.palette = ColorPalette(enabled=color_enabled)
        self.output = Output(options, self.palette)
        self.env = detect_environment()
        self.tools: dict[str, Any] = {}

    def run(self) -> int:
        if self.options.json_output:
            return self._run_json()
        self.output.banner()
        self.output.environment_block(self.env)
        deps_ok = self._handle_dependencies()
        if not deps_ok:
            return 2
        if not self.options.input_path:
            path = self._prompt_for_path()
            if not path:
                return 1
            self.options.input_path = path
        if self.options.recursive and Path(self.options.input_path).expanduser().is_dir():
            return self._run_directory_mode()
        detected = self._detect_input_file()
        if not detected or not detected.is_regular:
            self.output.failure_block(detected.error if detected else "File is not usable.")
            return 3
        self.output.file_block(detected)
        if not detected.extension_matches:
            self.output.warn("using detected format")
        if self.options.scan_only:
            self._run_scan_only(detected)
            return 0
        snapshot = self._inspect_metadata(detected)
        self.output.metadata_block(snapshot, verbose=self.options.verbose)
        decision = route(detected, self.tools, self.options)
        self.output.info(f"cleaner  {decision.cleaner_name}  write  {'yes' if decision.can_write else 'no'}")
        if decision.missing_tools:
            self.output.warn(f"missing  {', '.join(decision.missing_tools)}")
        for w in decision.warnings:
            self.output.warn(w)
        if not decision.can_write:
            if self.options.dry_run:
                self.output.info(f"dry run  {detected.detected_format}")
                if decision.missing_tools:
                    self.output.warn(f"need  {', '.join(decision.missing_tools)}")
                else:
                    self.output.warn(decision.reason)
                self.output.note("no changes")
                return 0
            self.output.error(decision.reason)
            self.output.note("text/source: no embedded metadata")
            self.output.note("unsupported: cannot verify")
            return 4
        cleaner = decision.cleaner_cls(self.tools, self.options)
        if self.options.dry_run:
            self.output.info(f"dry run  {decision.cleaner_name}")
            self.output.info(f"out  {default_output_path(detected.path, self.options)}")
            self.output.note("no changes")
            return 0
        if not self.options.clean_only and not self.options.yes:
            confirmed = self.output.confirm("Do you want to delete Metadata", default=False)
            if not confirmed:
                self.output.note("cancelled")
                return 0
        output_path = default_output_path(detected.path, self.options)
        self.output.info(f"{cleaner.name} -> {output_path.name}")
        bar = self.output.start_flow("cleaning", target=95.0)
        result = cleaner.clean(detected, output_path, snapshot)
        self.output.complete_flow(bar, message=f"  {self.palette.neon('+')} {self.palette.neon('cleaning done')}")
        if not result.success:
            self.output.failure_block(result.errors[0] if result.errors else "cleaning failed", details="; ".join(result.errors))
            return 5
        for warning in result.warnings:
            self.output.warn(warning)
        vbar = self.output.start_flow("verifying", target=95.0)
        report = verify_output(detected, result, snapshot, self.tools)
        self.output.complete_flow(vbar, message=f"  {self.palette.neon('+')} {self.palette.neon('verify done')}")
        self.output.verification_block(report.as_dict())
        self.output.complete_block(detected.path, result.output_path, success=True)
        if report.remaining_privacy_fields:
            self.output.warn("some metadata remains")
        return 0

    def _run_json(self) -> int:
        if not self.options.input_path:
            return 1
        detected = detect_file(self.options.input_path)
        if not detected.is_regular:
            self.output.json_block({"error": detected.error or "file not usable"})
            return 3
        snapshot = inspect_metadata(detected, self._check_tools_for_json(), self._check_tools_for_json_ffmpeg())
        payload = snapshot_to_json(snapshot, detected)
        payload["routing"] = {
            "format": detected.detected_format,
            "supported": is_supported_format(detected.detected_format),
        }
        if self.options.clean_only or self.options.yes:
            decision = route(detected, self.tools, self.options)
            payload["cleaner"] = decision.cleaner_name
            payload["can_clean"] = decision.can_write
        self.output.json_block(payload)
        return 0

    def _check_tools_for_json(self):
        if not self.tools:
            statuses = check_all_tools(self.env)
            self.tools = {s.name: s for s in statuses}
        return self.tools.get("exiftool")

    def _check_tools_for_json_ffmpeg(self):
        if not self.tools:
            self._check_tools_for_json()
        return self.tools.get("ffmpeg")

    def _handle_dependencies(self) -> bool:
        statuses = check_all_tools(self.env)
        self.tools = {s.name: s for s in statuses}
        self.output.dependencies_block(statuses)
        missing = [s for s in statuses if not s.functional]
        if not missing:
            self.output.ok("all tools operational")
            return True
        if not self.env.package_managers:
            self.output.warn("no package manager detected  cannot auto-install")
            for s in missing:
                self.output.note(f"missing  {s.name}")
            self.output.note("continuing with available tools only")
            return True
        pm = self.env.package_managers[0]
        self.output.info(f"package manager  {pm}")
        self.output.info(f"missing  {', '.join(s.name for s in missing)}")
        if not self.options.yes and not self.options.install_deps:
            if self.options.json_output:
                self.output.note("auto-install skipped in json mode")
                return True
            confirmed = self.output.confirm(
                f"auto-install {len(missing)} missing tool(s)?",
                default=True,
            )
            if not confirmed:
                self.output.warn("auto-install declined  continuing with available tools")
                return True
        for s in missing:
            self.output.info(f"installing {s.name}")
            bar = self.output.start_flow(f"install {s.name}", target=90.0)
            installed = self._try_install(s.name)
            self.output.complete_flow(bar, message=f"  {self.palette.green('\u2713') if installed else self.palette.red('\u2717')} {s.name} {'installed' if installed else 'failed'}")
            if installed:
                new_status = recheck_tool(s.name)
                self.tools[s.name] = new_status
                if new_status.functional:
                    self.output.ok(f"{s.name} verified  {new_status.version}")
                else:
                    self.output.warn(f"{s.name} installed but not functional")
                    self.output.note(f"may need a new terminal or manual install")
            else:
                self.output.warn(f"{s.name} install failed")
                if s.install_command:
                    self.output.note(f"try manually  {s.install_command}")
        still_missing = [s for s in self.tools.values() if not s.functional]
        if still_missing:
            self.output.warn(f"still missing  {', '.join(s.name for s in still_missing)}")
            self.output.note("continuing  routing will skip operations needing missing tools")
        else:
            self.output.ok("all tools operational")
        return True

    def _try_install(self, name: str) -> bool:
        def runner(parts, shell=False):
            try:
                if shell:
                    completed = subprocess.run(
                        parts,
                        shell=True,
                        stdin=sys.stdin,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        timeout=600,
                    )
                else:
                    completed = subprocess.run(
                        parts,
                        stdin=sys.stdin,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        timeout=600,
                    )
                if completed.stdout and self.options.debug:
                    sys.stderr.write(f"\n[debug] {name} install stdout:\n{completed.stdout[:500]}\n")
                if completed.stderr and self.options.debug:
                    sys.stderr.write(f"\n[debug] {name} install stderr:\n{completed.stderr[:500]}\n")
                return completed.returncode == 0
            except subprocess.TimeoutExpired:
                return False
            except OSError as exc:
                if self.options.debug:
                    sys.stderr.write(f"\n[debug] {name} install OSError: {exc}\n")
                return False
        return attempt_install(name, self.env, runner)

    def _prompt_for_path(self) -> str | None:
        self.output.section("FILE")
        raw = self.output.prompt("Enter the Path of the file")
        if not raw:
            return None
        candidate = raw.strip().strip('"').strip("'")
        if not candidate:
            return None
        return candidate

    def _detect_input_file(self) -> DetectedFile | None:
        bar = self.output.start_flow("analyzing", target=90.0)
        try:
            detected = detect_file(self.options.input_path or "")
        finally:
            self.output.complete_flow(bar, message=f"  {self.palette.neon('+')} {self.palette.neon('analyzed')}")
        return detected

    def _inspect_metadata(self, detected: DetectedFile) -> MetadataSnapshot:
        bar = self.output.start_flow("reading", target=90.0)
        try:
            snapshot = inspect_metadata(
                detected,
                self.tools.get("exiftool"),
                self.tools.get("ffmpeg"),
            )
        finally:
            self.output.complete_flow(bar, message=f"  {self.palette.neon('+')} {self.palette.neon('metadata read')}")
        return snapshot

    def _run_scan_only(self, detected: DetectedFile):
        snapshot = self._inspect_metadata(detected)
        self.output.metadata_block(snapshot, verbose=self.options.verbose)
        decision = route(detected, self.tools, self.options)
        self.output.info(f"cleaner  {decision.cleaner_name}  write  {'yes' if decision.can_write else 'no'}")
        if decision.missing_tools:
            self.output.warn(f"missing  {', '.join(decision.missing_tools)}")
        if decision.reason:
            self.output.note(decision.reason)
        for w in decision.warnings:
            self.output.warn(w)
        if decision.cleaner_cls is not None and decision.can_write:
            cleaner = decision.cleaner_cls(self.tools, self.options)
            self.output.note(f"action  {cleaner.name} -> {default_output_path(detected.path, self.options).name}")
        self.output.note("scan done  use --clean")

    def _explain_unsupported(self, decision: RoutingDecision):
        self.output.error(decision.reason)
        if decision.missing_tools:
            self.output.warn(f"missing tools  {', '.join(decision.missing_tools)}")
            for name in decision.missing_tools:
                tool = self.tools.get(name)
                if tool and tool.install_command:
                    self.output.note(f"install with  {tool.install_command}")
        for w in decision.warnings:
            self.output.warn(w)
        self.output.note("for text/source files  no embedded metadata to clean")
        self.output.note("for unsupported binaries  do not trust generic metadata commands")
        self.output.note("metaclean never claims anonymization for formats it cannot verify")

    def _run_directory_mode(self) -> int:
        directory = Path(self.options.input_path or "").expanduser()
        if not directory.is_dir():
            self.output.error("not a directory")
            return 3
        bar = self.output.start_flow("scanning directory", target=90.0)
        try:
            files = [p for p in directory.rglob("*") if p.is_file()]
        finally:
            self.output.complete_flow(bar, message=f"  {self.palette.green('\u2713')} directory scanned")
        supported = 0
        unsupported = 0
        details: list[dict[str, str]] = []
        for path in files:
            detected = detect_file(str(path))
            decision = route(detected, self.tools, self.options)
            if decision.can_write:
                supported += 1
                details.append({"path": str(path), "status": "supported", "cleaner": decision.cleaner_name})
            else:
                unsupported += 1
                details.append({"path": str(path), "status": "unsupported", "reason": decision.reason})
        self.output.info(f"files  {len(files)}  supported  {supported}  unsupported  {unsupported}")
        if self.options.json_output:
            self.output.json_block({"directory": str(directory), "files": details})
        if not self.options.yes:
            self.output.warn("recursive cleaning is preview-only in this version")
            self.output.note("use --yes with --recursive to proceed")
            return 0
        return 0


def main(argv: list[str] | None = None) -> int:
    try:
        namespace, options = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    app = MetaCleanApp(options)
    try:
        return app.run()
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        return 130
    except Exception as exc:
        if options.debug:
            raise
        sys.stderr.write(f"\n{ColorPalette(enabled=not options.no_color).red('Error:')} {exc}\n")
        sys.stderr.write("Run with --debug for technical details.\n")
        return 1
