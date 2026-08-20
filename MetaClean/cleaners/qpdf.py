from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import DetectedFile, RuntimeOptions, ToolStatus
from ..metadata import MetadataSnapshot, run_exiftool_inspect
from .base import CleanerBase, CleanResult


class QpdfCleaner(CleanerBase):
    name = "qpdf"
    supported_formats = ("pdf",)
    can_write_formats = ("pdf",)
    required_tools = ("qpdf",)

    def clean(self, detected: DetectedFile, output_path: Path, before_snapshot: MetadataSnapshot) -> CleanResult:
        result = CleanResult(cleaner_name=self.name, method="qpdf_linearize")
        tool = self.tools.get("qpdf")
        if not tool or not tool.executable:
            result.errors.append("qpdf executable unavailable")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        warnings = self._pre_clean_warnings(detected, before_snapshot)
        if warnings:
            result.warnings.extend(warnings)
        command = [
            tool.executable,
            "--linearize",
            "--remove-unreferenced-resources=yes",
            "--object-streams=generate",
            "--recompress-flate",
            "--compression-level=9",
            str(detected.path),
            str(output_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            result.errors.append("qpdf timed out")
            return result
        except OSError as exc:
            result.errors.append(f"qpdf execution failed: {exc}")
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            result.errors.append(f"qpdf exit code {completed.returncode}: {stderr}")
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
            return result
        if not output_path.exists() or output_path.stat().st_size == 0:
            result.errors.append("qpdf did not produce valid output")
            if output_path.exists():
                output_path.unlink()
            return result
        exiftool = self.tools.get("exiftool")
        if exiftool and exiftool.functional:
            after_snapshot = run_exiftool_inspect(output_path, exiftool.executable)
            if not after_snapshot.error:
                before_keys = set(before_snapshot.fields.keys())
                after_keys = set(after_snapshot.fields.keys())
                result.removed_fields = sorted(before_keys - after_keys)
                result.retained_fields = sorted(before_keys & after_keys)
            else:
                result.warnings.append("Could not re-inspect output metadata")
        else:
            result.warnings.append("ExifTool unavailable for output verification")
        result.success = True
        result.output_path = output_path
        return result

    def _pre_clean_warnings(self, detected: DetectedFile, before_snapshot: MetadataSnapshot) -> list[str]:
        warnings: list[str] = []
        joined = "\n".join(before_snapshot.fields.keys()).lower()
        if "javascript" in joined or "js" in joined:
            warnings.append("PDF appears to contain JavaScript; qpdf rewrite does not guarantee its removal.")
        if "embeddedfile" in joined or "attachment" in joined:
            warnings.append("PDF may contain embedded files or attachments; qpdf rewrite does not remove them.")
        if "annot" in joined:
            warnings.append("PDF contains annotations; qpdf rewrite does not remove annotations.")
        if "acroform" in joined or "form" in joined:
            warnings.append("PDF may contain interactive forms; qpdf rewrite does not remove form definitions.")
        warnings.append("Metadata cleaning is not equivalent to full PDF sanitization.")
        return warnings

    def describe_action(self, detected: DetectedFile, output_path: Path) -> str:
        return f"qpdf will rewrite and linearize PDF into {output_path.name}"
