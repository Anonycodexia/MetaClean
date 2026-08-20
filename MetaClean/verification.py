from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cleaners import CleanResult
from .config import DetectedFile
from .detector import detect_file
from .metadata import MetadataSnapshot, inspect_metadata
from .dependencies import ToolStatus


@dataclass
class VerificationReport:
    output_exists: bool = False
    output_readable: bool = False
    output_non_empty: bool = False
    format_preserved: bool = False
    detected_output_format: str = "unknown"
    remaining_privacy_fields: list[str] = field(default_factory=list)
    removed_privacy_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_exists": self.output_exists,
            "output_readable": self.output_readable,
            "output_non_empty": self.output_non_empty,
            "format_preserved": self.format_preserved,
            "detected_output_format": self.detected_output_format,
            "remaining_privacy_fields": self.remaining_privacy_fields,
            "removed_privacy_fields": self.removed_privacy_fields,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def verify_output(
    detected_input: DetectedFile,
    clean_result: CleanResult,
    before_snapshot: MetadataSnapshot,
    tools: dict[str, ToolStatus],
) -> VerificationReport:
    report = VerificationReport()
    if not clean_result.output_path:
        report.errors.append("Cleaner did not produce an output path")
        return report
    output_path = clean_result.output_path
    report.output_exists = output_path.exists()
    if not report.output_exists:
        report.errors.append("Output file does not exist")
        return report
    try:
        with output_path.open("rb") as handle:
            handle.read(1)
        report.output_readable = True
    except OSError as exc:
        report.errors.append(f"Output file is not readable: {exc}")
    try:
        size = output_path.stat().st_size
        report.output_non_empty = size > 0
    except OSError as exc:
        report.errors.append(f"Cannot stat output: {exc}")
    output_detected = detect_file(str(output_path))
    if output_detected.error:
        report.warnings.append(f"Could not re-detect output format: {output_detected.error}")
    report.detected_output_format = output_detected.detected_format
    report.format_preserved = (
        output_detected.detected_format == detected_input.detected_format
        or (detected_input.detected_format == "mp4_family" and output_detected.detected_format == "mp4")
    )
    if not report.format_preserved:
        report.warnings.append(
            f"Output format '{output_detected.detected_format}' differs from input '{detected_input.detected_format}'"
        )
    after_snapshot = inspect_metadata(output_detected, tools.get("exiftool", ToolStatus(name="exiftool")), tools.get("ffmpeg", ToolStatus(name="ffmpeg")))
    if after_snapshot.error:
        report.warnings.append(f"Could not re-inspect output metadata: {after_snapshot.error}")
    else:
        before_keys = set(before_snapshot.privacy_sensitive.keys())
        after_keys = set(after_snapshot.privacy_sensitive.keys())
        report.removed_privacy_fields = sorted(before_keys - after_keys)
        report.remaining_privacy_fields = sorted(before_keys & after_keys)
    if report.remaining_privacy_fields:
        report.warnings.append("Some privacy-sensitive metadata still present in output.")
    return report
