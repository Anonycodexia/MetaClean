from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..config import DetectedFile, RuntimeOptions, ToolStatus
from ..metadata import MetadataSnapshot, run_exiftool_inspect
from .base import CleanerBase, CleanResult


EXIFTOOL_IMAGE_FORMATS = (
    "jpeg",
    "png",
    "gif",
    "bmp",
    "tiff",
    "webp",
    "heic",
    "heif",
    "avif",
    "cr2",
    "cr3",
    "nef",
    "arw",
    "dng",
    "raf",
    "rw2",
    "orf",
    "psd",
    "ico",
)


class ExifToolCleaner(CleanerBase):
    name = "ExifTool"
    supported_formats = EXIFTOOL_IMAGE_FORMATS + ("pdf",)
    can_write_formats = (
        "jpeg",
        "png",
        "tiff",
        "webp",
        "heic",
        "heif",
        "avif",
        "psd",
        "cr2",
        "cr3",
        "nef",
        "arw",
        "dng",
        "raf",
        "rw2",
        "orf",
        "bmp",
        "gif",
    )
    required_tools = ("exiftool",)

    REMOVAL_TAGS = (
        "-all=",
    )

    PRESERVE_GROUPS = (
        "-tagsfromfile",
        "@",
        "-unsafe",
    )

    def clean(self, detected: DetectedFile, output_path: Path, before_snapshot: MetadataSnapshot) -> CleanResult:
        result = CleanResult(cleaner_name=self.name, method="exiftool_rewrite")
        tool = self.tools.get("exiftool")
        if not tool or not tool.executable:
            result.errors.append("ExifTool executable unavailable")
            return result
        if detected.detected_format not in self.can_write_formats:
            result.errors.append(f"ExifTool cannot write {detected.detected_format} format")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            tool.executable,
            "-overwrite_original_in_place",
            "-overwrite_original",
            "-all=",
            "-tagsfromfile",
            "@",
            "-unsafe",
            "-icc_profile:all",
            "-make=",
            "-model=",
            "-software=",
            "-comment=",
            "-title=",
            "-author=",
            "-artist=",
            "-copyright=",
            "-ownername=",
            "-serialnumber=",
            "-gps:all=",
            "-xmp:all=",
            "-iptc:all=",
            "-exif:all=",
            "-photoshop:all=",
            str(detected.path),
            "-o",
            str(output_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            result.errors.append("ExifTool timed out")
            return result
        except OSError as exc:
            result.errors.append(f"ExifTool execution failed: {exc}")
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            if "Can't write" in stderr or "not writable" in stderr.lower():
                result.errors.append(f"ExifTool reports format not writable: {stderr}")
            else:
                result.errors.append(f"ExifTool exit code {completed.returncode}: {stderr}")
            return result
        if not output_path.exists():
            result.errors.append("ExifTool did not produce output file")
            return result
        if output_path.stat().st_size == 0:
            result.errors.append("ExifTool produced empty output file")
            return result
        after_snapshot = run_exiftool_inspect(output_path, tool.executable)
        if after_snapshot.error:
            result.warnings.append(f"Could not re-inspect output: {after_snapshot.error}")
        else:
            before_keys = set(before_snapshot.fields.keys())
            after_keys = set(after_snapshot.fields.keys())
            result.removed_fields = sorted(before_keys - after_keys)
            result.retained_fields = sorted(before_keys & after_keys)
        result.success = True
        result.output_path = output_path
        return result

    def describe_action(self, detected: DetectedFile, output_path: Path) -> str:
        return f"ExifTool will strip all metadata tags into {output_path.name}"
