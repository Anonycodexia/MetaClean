from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .colors import ColorPalette, should_enable_animation
from .animation import FlowBar, Spinner
from ..config import (
    APP_VERSION,
    DetectedFile,
    EnvironmentInfo,
    RuntimeOptions,
    ToolStatus,
)
from ..metadata import MetadataSnapshot


class Output:
    def __init__(self, options: RuntimeOptions, palette: ColorPalette | None = None):
        self.options = options
        self.palette = palette or ColorPalette(enabled=True)
        self.animation_enabled = should_enable_animation(options.no_animation)
        self._suppress = options.json_output

    def write(self, message: str = "", stream=None, end: str = "\n"):
        if self._suppress:
            return
        stream = stream or sys.stdout
        try:
            stream.write(message + end)
            stream.flush()
        except (OSError, ValueError):
            pass

    def banner(self):
        if self._suppress:
            return
        from .banner import render_logo
        logo = render_logo(self.palette)
        self.write(logo)
        title = self.palette.bold(self.palette.aqua_bright("METACLEAN"))
        tagline = self.palette.blue("Universal Metadata Sanitizer")
        version = self.palette.aqua(f"v{APP_VERSION}")
        self.write(f"  {title} {self.palette.gray('/')} {tagline} {self.palette.gray('/')} {version}")
        self.write()

    def section(self, title: str):
        pass

    def separator(self, width: int = 50):
        pass

    def ok(self, message: str):
        self.write(f"  {self.palette.neon('+')} {self.palette.neon(message)}")

    def info(self, message: str):
        self.write(f"  {self.palette.aqua('>')} {self.palette.blue(message)}")

    def warn(self, message: str):
        self.write(f"  {self.palette.yellow('!')} {self.palette.yellow(message)}")

    def error(self, message: str):
        self.write(f"  {self.palette.red('x')} {self.palette.red(message)}")

    def note(self, message: str):
        self.write(f"  {self.palette.gray('-')} {self.palette.gray(message)}")

    def key_value(self, key: str, value: str, indent: int = 0):
        prefix = "  " * indent
        self.write(f"{prefix}{self.palette.label(key)} {self.palette.value(value)}")

    def pair(self, key: str, value: str, status: str = "info"):
        color_fn = {
            "info": self.palette.aqua,
            "ok": self.palette.neon,
            "warn": self.palette.yellow,
            "error": self.palette.red,
            "neutral": self.palette.gray,
        }.get(status, self.palette.aqua)
        self.write(f"  {self.palette.label(key)} {color_fn(value)}")

    def labeled(self, label: str, value: str, color_fn=None):
        self.write(f"  {self.palette.label(label)} {self.palette.value(value)}")

    def field(self, label: str, value: str):
        val = value if len(value) <= 65 else value[:62] + "..."
        self.write(f"  {self.palette.label(label)} {self.palette.aqua(val)}")

    def start_flow(self, message: str, target: float = 100.0) -> FlowBar:
        bar = FlowBar(self.palette, enabled=self.animation_enabled)
        bar.start(message, target=target)
        return bar

    def update_flow(self, bar: FlowBar, target: float = None, message: str = None):
        bar.update(target=target, message=message)

    def complete_flow(self, bar: FlowBar, message: str = None):
        bar.complete(final_message=message)

    def start_spinner(self, message: str) -> Spinner:
        sp = Spinner(self.palette, enabled=self.animation_enabled)
        sp.start(message)
        return sp

    def stop_spinner(self, sp: Spinner, final_message: str | None = None, success: bool = True):
        sp.stop(final_message=final_message, success=success)

    def progress(self, percent: float, label: str = ""):
        pass

    def prompt(self, message: str) -> str:
        if self._suppress:
            return "n"
        prompt_text = f"  {self.palette.aqua('>')} {self.palette.blue(message)} : "
        sys.stdout.write(prompt_text)
        sys.stdout.flush()
        try:
            line = sys.stdin.readline()
        except (KeyboardInterrupt, EOFError):
            return "n"
        return line.strip()

    def confirm(self, message: str, default: bool = False) -> bool:
        if self.options.yes:
            self.write(f"  {self.palette.aqua('>')} {self.palette.blue(message)} {self.palette.gray('(y/n)')} : {self.palette.neon('y')}")
            return True
        raw = self.prompt(f"{message} (y/n)")
        if not raw:
            return default
        return raw[0].lower() in ("y", "1", "t")

    def environment_block(self, env: EnvironmentInfo):
        self.info(f"env  {env.platform_name}  {env.architecture}  py{env.python_version}")
        if env.package_managers:
            self.info(f"pkg  {env.package_managers[0]}")
        else:
            self.warn("no package manager")

    def dependencies_block(self, tools: list[ToolStatus]):
        for tool in tools:
            if tool.functional:
                self.write(f"  {self.palette.neon('+')} {self.palette.aqua_bright(tool.name)}")
            elif tool.available:
                self.write(f"  {self.palette.yellow('!')} {self.palette.yellow(tool.name)}")
            else:
                self.write(f"  {self.palette.red('x')} {self.palette.red(tool.name)}")

    def file_block(self, detected: DetectedFile):
        self.info(f"file  {detected.path}")
        self.info(f"size  {_format_bytes(detected.size_bytes)}  type  {detected.detected_format}  mime  {detected.mime_type}")
        if detected.magic_description:
            desc = detected.magic_description
            if len(desc) > 70:
                desc = desc[:67] + "..."
            self.info(f"desc  {desc}")
        if not detected.extension_matches:
            self.warn(f"ext mismatch  {detected.extension or 'none'} != {detected.detected_format}")
        if detected.is_symlink:
            self.warn("symlink  target resolved")

    def metadata_block(self, snapshot: MetadataSnapshot, verbose: bool = False):
        if snapshot.error:
            self.error(snapshot.error)
            return
        if snapshot.warning:
            self.warn(snapshot.warning)
        if not snapshot.fields:
            self.note("no metadata")
            return
        if snapshot.privacy_sensitive:
            self.write(f"  {self.palette.yellow('!')} {self.palette.yellow('privacy fields')}")
            for group, fields in _group_by(snapshot.privacy_sensitive).items():
                self.write(f"      {self.palette.aqua(group)}  {self.palette.gray(', '.join(fields))}")
            self.write()
        limit = None if verbose else 20
        shown = list(snapshot.fields.items())[:limit] if limit else list(snapshot.fields.items())
        for key, value in shown:
            display_value = value if len(value) <= 65 else value[:62] + "..."
            k_display = key if len(key) <= 38 else key[:35] + "..."
            self.write(f"  {self.palette.label(k_display):<40} {self.palette.aqua(display_value)}")
        if verbose and snapshot.groups:
            self.write()
            for group, fields in snapshot.groups.items():
                self.write(f"  {self.palette.aqua(group)}")
                for k, v in fields.items():
                    self.write(f"    {self.palette.label(k)} {self.palette.aqua(v[:55])}")
        if not verbose and len(snapshot.fields) > 20:
            self.note(f"+{len(snapshot.fields) - 20} more  use --verbose")

    def cleaning_block(self):
        pass

    def verification_block(self, results: dict[str, Any]):
        for key, value in results.items():
            display_key = key.replace("_", " ")
            if isinstance(value, bool):
                if value:
                    self.write(f"  {self.palette.neon('+')} {self.palette.blue(display_key)}")
                else:
                    self.write(f"  {self.palette.red('x')} {self.palette.red(display_key)}")
            elif isinstance(value, list):
                if value:
                    for item in value[:5]:
                        item_str = str(item).replace("_", " ")
                        if len(item_str) > 50:
                            item_str = item_str[:47] + "..."
                        self.write(f"  {self.palette.yellow('!')} {self.palette.yellow(item_str)}")
                    if len(value) > 5:
                        self.write(f"  {self.palette.gray(f'+{len(value) - 5} more')}")
                else:
                    self.write(f"  {self.palette.neon('+')} {self.palette.blue(display_key)} {self.palette.gray('ok')}")
            else:
                val_str = str(value)
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                self.write(f"  {self.palette.blue(display_key)}  {self.palette.aqua(val_str)}")

    def complete_block(self, original: Path, cleaned: Path | None, success: bool):
        self.write()
        if success and cleaned:
            self.ok("done")
            self.write()
            self.write(f"  {self.palette.label('in')}   {original}")
            self.write(f"  {self.palette.neon('out')}  {cleaned}")
            self.write()
            self.ok("original kept")
        else:
            self.error("failed")
            self.write()
            self.write(f"  {self.palette.label('in')}   {original}")
            if cleaned:
                self.write(f"  {self.palette.label('out')}  {cleaned}")

    def failure_block(self, reason: str, details: str | None = None):
        self.error(reason)
        if details and self.options.debug:
            self.write(f"  {self.palette.gray(details)}")
        else:
            self.write(f"  {self.palette.gray('use --debug')}")

    def json_block(self, payload: dict[str, Any]):
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
        sys.stdout.flush()


def _format_bytes(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}" if unit != "B" else f"{num}B"
        num /= 1024.0
    return f"{num:.1f}PB"


def _group_by(fields: dict[str, str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for key in fields:
        if ":" in key:
            group, _, name = key.partition(":")
        else:
            group, name = "other", key
        grouped.setdefault(group, []).append(name)
    return grouped
