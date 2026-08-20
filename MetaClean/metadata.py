from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import PRIVACY_SENSITIVE_KEYS, DetectedFile
from .dependencies import ToolStatus


@dataclass
class MetadataSnapshot:
    source: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    groups: dict[str, dict[str, str]] = field(default_factory=dict)
    privacy_sensitive: dict[str, str] = field(default_factory=dict)
    warning: str | None = None
    error: str | None = None
    raw: Any = None


def is_privacy_sensitive(key: str) -> bool:
    if not key:
        return False
    normalized = key.lower().strip()
    for needle in PRIVACY_SENSITIVE_KEYS:
        if needle in normalized:
            return True
    if "gps" in normalized or "location" in normalized:
        return True
    if "serial" in normalized:
        return True
    if "author" in normalized or "creator" in normalized or "owner" in normalized:
        return True
    if "camera" in normalized or "make" in normalized or "model" in normalized:
        return True
    if "datetimeoriginal" in normalized or "createdate" in normalized or "modifydate" in normalized:
        return True
    if normalized.startswith("date:") or normalized in {"datetaken", "datemodified", "datecreated"}:
        return True
    return False


def run_exiftool_inspect(path: Path, exiftool_executable: str) -> MetadataSnapshot:
    snapshot = MetadataSnapshot(source="exiftool")
    try:
        result = subprocess.run(
            [exiftool_executable, "-G", "-j", "-n", "-q", "-q", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        snapshot.error = "ExifTool inspection timed out"
        return snapshot
    except OSError as exc:
        snapshot.error = f"ExifTool failed: {exc}"
        return snapshot
    if result.returncode != 0:
        snapshot.error = result.stderr.strip() or f"ExifTool exit code {result.returncode}"
        return snapshot
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        snapshot.error = f"ExifTool returned invalid JSON: {exc}"
        return snapshot
    if not isinstance(parsed, list) or not parsed:
        snapshot.error = "ExifTool returned empty result"
        return snapshot
    record = parsed[0]
    snapshot.raw = record
    for full_key, value in record.items():
        if full_key in ("SourceFile", "ExifToolVersion", "FileName", "Directory", "FilePermissions"):
            continue
        if ":" in full_key:
            group, _, field_name = full_key.partition(":")
        else:
            group, field_name = "Other", full_key
        text_value = _stringify_value(value)
        if text_value is None:
            continue
        snapshot.fields[full_key] = text_value
        snapshot.groups.setdefault(group, {})[field_name] = text_value
        if is_privacy_sensitive(full_key) or is_privacy_sensitive(field_name):
            snapshot.privacy_sensitive[full_key] = text_value
    return snapshot


def _stringify_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        parts = [_stringify_value(v) for v in value]
        joined = ", ".join(p for p in parts if p)
        return joined or None
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        if value != value:
            return None
    return str(value)


def run_ffprobe_inspect(path: Path, ffprobe_executable: str) -> MetadataSnapshot:
    snapshot = MetadataSnapshot(source="ffprobe")
    try:
        result = subprocess.run(
            [
                ffprobe_executable,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        snapshot.error = "ffprobe inspection timed out"
        return snapshot
    except OSError as exc:
        snapshot.error = f"ffprobe failed: {exc}"
        return snapshot
    if result.returncode != 0:
        snapshot.error = result.stderr.strip() or f"ffprobe exit code {result.returncode}"
        return snapshot
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        snapshot.error = f"ffprobe returned invalid JSON: {exc}"
        return snapshot
    snapshot.raw = parsed
    fmt = parsed.get("format", {}) if isinstance(parsed, dict) else {}
    for key, value in fmt.items():
        if key in ("filename", "nb_streams", "nb_programs", "format_name", "format_long_name", "duration", "size", "bit_rate", "probe_score"):
            continue
        if key == "tags" and isinstance(value, dict):
            for tag_key, tag_value in value.items():
                text_value = _stringify_value(tag_value)
                if text_value is None:
                    continue
                full_key = f"Format:tags:{tag_key}"
                snapshot.fields[full_key] = text_value
                snapshot.groups.setdefault("Format:tags", {})[tag_key] = text_value
                if is_privacy_sensitive(tag_key):
                    snapshot.privacy_sensitive[full_key] = text_value
            continue
        text_value = _stringify_value(value)
        if text_value is None:
            continue
        snapshot.fields[f"Format:{key}"] = text_value
        snapshot.groups.setdefault("Format", {})[key] = text_value
        if is_privacy_sensitive(key):
            snapshot.privacy_sensitive[f"Format:{key}"] = text_value
    streams = parsed.get("streams", []) if isinstance(parsed, dict) else []
    for idx, stream in enumerate(streams):
        if not isinstance(stream, dict):
            continue
        for key, value in stream.items():
            if key in ("index", "codec_name", "codec_long_name", "codec_type", "profile", "level", "pix_fmt", "sample_rate", "channels", "channel_layout", "width", "height", "r_frame_rate", "avg_frame_rate", "duration", "bit_rate", "nb_frames", "codec_tag", "codec_tag_string", "time_base", "start_pts", "start_time", "duration_ts", "disposition"):
                continue
            if key == "tags" and isinstance(value, dict):
                for tag_key, tag_value in value.items():
                    text_value = _stringify_value(tag_value)
                    if text_value is None:
                        continue
                    full_key = f"Stream{idx}:tags:{tag_key}"
                    snapshot.fields[full_key] = text_value
                    snapshot.groups.setdefault(f"Stream{idx}:tags", {})[tag_key] = text_value
                    if is_privacy_sensitive(tag_key):
                        snapshot.privacy_sensitive[full_key] = text_value
                continue
            text_value = _stringify_value(value)
            if text_value is None:
                continue
            full_key = f"Stream{idx}:{key}"
            snapshot.fields[full_key] = text_value
            snapshot.groups.setdefault(f"Stream{idx}", {})[key] = text_value
            if is_privacy_sensitive(key):
                snapshot.privacy_sensitive[full_key] = text_value
    return snapshot


def inspect_filesystem_metadata(path: Path) -> dict[str, str]:
    info: dict[str, str] = {}
    try:
        stat = path.stat()
    except OSError as exc:
        return {"error": str(exc)}
    info["size_bytes"] = str(stat.st_size)
    info["mtime"] = str(stat.st_mtime)
    info["ctime"] = str(stat.st_ctime)
    try:
        info["atime"] = str(stat.st_atime)
    except (AttributeError, OSError):
        pass
    info["mode"] = oct(stat.st_mode)
    try:
        import pwd
        import grp
        info["owner_user"] = pwd.getpwuid(stat.st_uid).pw_name
        info["owner_group"] = grp.getgrgid(stat.st_gid).gr_name
    except (KeyError, ImportError, OSError):
        info["owner_uid"] = str(stat.st_uid)
        info["owner_gid"] = str(stat.st_gid)
    info["inode"] = str(stat.st_ino)
    info["device"] = str(stat.st_dev)
    return info


def inspect_metadata(detected: DetectedFile, exiftool: ToolStatus, ffmpeg: ToolStatus) -> MetadataSnapshot:
    fmt = detected.detected_format
    if fmt in {"jpeg", "png", "gif", "bmp", "tiff", "webp", "heic", "heif", "avif", "cr2", "cr3", "nef", "arw", "dng", "raf", "rw2", "orf", "psd", "pdf"}:
        if exiftool.functional:
            return run_exiftool_inspect(detected.path, exiftool.executable)
        return MetadataSnapshot(error="ExifTool not available for metadata inspection of this format")
    if fmt in {"mp4", "mov", "m4v", "matroska", "avi", "webm", "3gp", "3g2", "mts", "flv", "wmv", "mp3", "flac", "wave", "aac", "m4a", "ogg", "opus", "wma", "aiff"}:
        ffprobe_path = _find_ffprobe(ffmpeg)
        if ffprobe_path:
            return run_ffprobe_inspect(detected.path, ffprobe_path)
        if exiftool.functional:
            return run_exiftool_inspect(detected.path, exiftool.executable)
        return MetadataSnapshot(error="Neither ffprobe nor ExifTool available for media metadata inspection")
    if fmt == "pdf" and exiftool.functional:
        return run_exiftool_inspect(detected.path, exiftool.executable)
    if _is_text_source_format(fmt):
        return MetadataSnapshot(warning="Text and source files do not carry embedded metadata requiring inspection.", fields={})
    if fmt in {"unknown", "binary", "zip"}:
        if exiftool.functional:
            snapshot = run_exiftool_inspect(detected.path, exiftool.executable)
            if not snapshot.error:
                return snapshot
        return MetadataSnapshot(warning=f"No metadata inspection strategy registered for format '{fmt}'.", fields={})
    return MetadataSnapshot(warning=f"No embedded metadata inspection available for format '{fmt}'.", fields={})


def _is_text_source_format(fmt: str) -> bool:
    from .detector import SOURCE_FORMATS
    return fmt in SOURCE_FORMATS or fmt == "text"


def _find_ffprobe(ffmpeg_tool: ToolStatus) -> str | None:
    if not ffmpeg_tool.executable:
        return None
    candidate = Path(ffmpeg_tool.executable).with_name("ffprobe")
    if candidate.exists():
        return str(candidate)
    import shutil
    return shutil.which("ffprobe")


def filter_preview(snapshot: MetadataSnapshot, max_fields: int = 20) -> dict[str, str]:
    items = list(snapshot.fields.items())[:max_fields]
    return dict(items)


def summarize_privacy(snapshot: MetadataSnapshot) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for key in snapshot.privacy_sensitive:
        if ":" in key:
            group, _, field = key.partition(":")
        else:
            group, field = "Other", key
        grouped.setdefault(group, []).append(field)
    return grouped


def snapshot_to_json(snapshot: MetadataSnapshot, detected: DetectedFile) -> dict[str, Any]:
    return {
        "file": {
            "path": str(detected.path),
            "format": detected.detected_format,
            "mime": detected.mime_type,
            "size": detected.size_bytes,
            "extension_matches": detected.extension_matches,
        },
        "metadata": {
            "source": snapshot.source,
            "fields": snapshot.fields,
            "privacy_sensitive": snapshot.privacy_sensitive,
            "warning": snapshot.warning,
            "error": snapshot.error,
        },
    }
