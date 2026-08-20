from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..config import DetectedFile, RuntimeOptions, ToolStatus
from ..metadata import MetadataSnapshot, run_ffprobe_inspect
from .base import CleanerBase, CleanResult


VIDEO_FORMATS = (
    "mp4",
    "mov",
    "m4v",
    "matroska",
    "avi",
    "webm",
    "3gp",
    "3g2",
    "mts",
    "flv",
    "wmv",
)

AUDIO_FORMATS = (
    "mp3",
    "flac",
    "wave",
    "aac",
    "m4a",
    "ogg",
    "opus",
    "wma",
    "aiff",
)


FFMPEG_CONTAINER_DEFAULTS: dict[str, str] = {
    "mp4": "mp4",
    "mov": "mov",
    "m4v": "mp4",
    "matroska": "matroska",
    "avi": "avi",
    "webm": "webm",
    "3gp": "3gp",
    "3g2": "3gp",
    "mts": "mpegts",
    "flv": "flv",
    "wmv": "asf",
    "mp3": "mp3",
    "flac": "flac",
    "wave": "wav",
    "aac": "adts",
    "m4a": "ipod",
    "ogg": "ogg",
    "opus": "ogg",
    "wma": "asf",
    "aiff": "aiff",
}


class FFmpegCleaner(CleanerBase):
    name = "FFmpeg"
    supported_formats = VIDEO_FORMATS + AUDIO_FORMATS
    can_write_formats = VIDEO_FORMATS + AUDIO_FORMATS
    required_tools = ("ffmpeg",)

    def clean(self, detected: DetectedFile, output_path: Path, before_snapshot: MetadataSnapshot) -> CleanResult:
        result = CleanResult(cleaner_name=self.name, method="ffmpeg_stream_copy")
        tool = self.tools.get("ffmpeg")
        if not tool or not tool.executable:
            result.errors.append("FFmpeg executable unavailable")
            return result
        container = FFMPEG_CONTAINER_DEFAULTS.get(detected.detected_format)
        if not container:
            result.errors.append(f"No FFmpeg container mapping for {detected.detected_format}")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        command = [
            tool.executable,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(detected.path),
            "-map_metadata", "-1",
            "-map_chapters", "-1",
            "-codec", "copy",
            "-map", "0",
        ]
        if detected.detected_format in {"mp4", "mov", "m4v", "3gp", "3g2"}:
            command.extend(["-movflags", "+faststart"])
        command.extend(["-f", container, str(output_path)])
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            result.errors.append("FFmpeg timed out")
            return result
        except OSError as exc:
            result.errors.append(f"FFmpeg execution failed: {exc}")
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            if "could not find tag" in stderr.lower() or "codec" in stderr.lower() and "not currently supported" in stderr.lower():
                result.errors.append(f"FFmpeg cannot stream-copy into this container without transcoding: {stderr}")
                result.warnings.append("Transcoding was deliberately NOT attempted to preserve media quality.")
            else:
                result.errors.append(f"FFmpeg exit code {completed.returncode}: {stderr}")
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
            return result
        if not output_path.exists():
            result.errors.append("FFmpeg did not produce output file")
            return result
        if output_path.stat().st_size == 0:
            output_path.unlink()
            result.errors.append("FFmpeg produced empty output file")
            return result
        ffprobe_path = self._find_ffprobe(tool.executable)
        if ffprobe_path:
            after_snapshot = run_ffprobe_inspect(output_path, ffprobe_path)
            if not after_snapshot.error:
                before_keys = set(before_snapshot.fields.keys())
                after_keys = set(after_snapshot.fields.keys())
                result.removed_fields = sorted(before_keys - after_keys)
                result.retained_fields = sorted(before_keys & after_keys)
            else:
                result.warnings.append("Could not re-inspect output metadata")
        else:
            result.warnings.append("ffprobe not available to verify cleaned metadata")
        result.success = True
        result.output_path = output_path
        return result

    def describe_action(self, detected: DetectedFile, output_path: Path) -> str:
        return f"FFmpeg will rewrite {detected.detected_format} container without metadata into {output_path.name}"

    def _find_ffprobe(self, ffmpeg_executable: str) -> str | None:
        candidate = Path(ffmpeg_executable).with_name("ffprobe")
        if candidate.exists():
            return str(candidate)
        return shutil.which("ffprobe")
