#!/usr/bin/env python3
"""Standalone single-file build of MetaClean.
This file is generated from the modular metaclean package.
The modular package is the canonical source; this single-file build is provided for portability.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import threading
import time
import zlib
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


APP_NAME = "MetaClean"
APP_TAGLINE = "Universal Metadata Inspection & Sanitization"
APP_VERSION = "1.0.0"
DEFAULT_OUTPUT_SUFFIX = "cleaned"
DEFAULT_OUTPUT_PATTERN = "{stem}.{suffix}{ext}"
DEFAULT_OUTPUT_PATTERN_INDEXED = "{stem}.{suffix}-{index}{ext}"

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
C_AQUA = "\x1b[38;2;0;255;200m"
C_AQUA_BRIGHT = "\x1b[38;2;80;255;220m"
C_BLUE = "\x1b[38;2;80;160;255m"
C_BLUE_BRIGHT = "\x1b[38;2;120;200;255m"
C_BLUE_DIM = "\x1b[38;2;40;100;180m"
C_NEON = "\x1b[38;2;0;255;180m"
C_GREEN = "\x1b[38;2;0;255;100m"
C_YELLOW = "\x1b[38;2;255;220;80m"
C_RED = "\x1b[38;2;255;80;100m"
C_GRAY = "\x1b[38;2;120;140;160m"
GREEN = C_NEON
BLUE = C_BLUE
CYAN = C_AQUA
YELLOW = C_YELLOW
RED = C_RED
MAGENTA = C_NEON
GRAY = C_GRAY

SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]

LOGO_LINES = [
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⢀⣤⡶⠁⣠⣴⣾⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⢀⣴⣿⣿⣴⣿⠿⠋⣁⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⣰⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⣠⣾⣿⡿⠟⠋⠉⠀⣀⣀⣀⣨⣭⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⣤⣤⣤⣴⠂",
    "⠈⠉⠁⠀⠀⣀⣴⣾⣿⣿⡿⠟⠛⠉⠉⠉⠉⠉⠛⠻⠿⠿⠿⠿⠿⠿⠟⠋⠁⠀",
    "⠀⠀⠀⢀⣴⣿⣿⣿⡿⠁⠀⢀⣀⣤⣤⣤⣤⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⣾⣿⣿⣿⡿⠁⢀⣴⣿⠋⠉⠉⠉⠉⠛⣿⣿⣶⣤⣤⣤⣤⣶⠖⠀⠀⠀",
    "⠀⠀⢸⣿⣿⣿⣿⡇⢀⣿⣿⣇⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀",
    "⠀⠀⠸⣿⣿⣿⣿⡇⠈⢿⣿⣿⠇⠀⠀⠀⠀⠀⢠⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⢿⣿⣿⣿⣷⡀⠀⠉⠉⠀⠀⠀⠀⠀⢀⣾⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠙⢿⣿⣿⣷⣄⡀⠀⠀⠀⠀⣀⣴⣿⣿⣿⣋⣠⡤⠄⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠈⠙⠛⠛⠿⠿⠿⠿⠿⠿⠟⠛⠛⠛⠉⠁",
]

PRIVACY_SENSITIVE_KEYS = (
    "gps", "gpslatitude", "gpslongitude", "make", "model", "serialnumber",
    "ownername", "artist", "author", "creator", "software", "encoder",
    "comment", "description", "datetimeoriginal", "createdate", "modifydate",
    "composer", "copyright", "xmp", "iptc", "exif", "icc_profile",
    "thumbnailimage", "previewimage", "title", "subject", "keywords",
    "producer", "creator_tool",
)


def detect_termux() -> bool:
    if os.environ.get("TERMUX_VERSION"):
        return True
    if os.environ.get("PREFIX") == "/data/data/com.termux/files/usr":
        return True
    if os.path.isdir("/data/data/com.termux/files/usr"):
        return True
    return False


def detect_macos() -> bool:
    return sys.platform == "darwin"


def detect_windows() -> bool:
    return sys.platform in ("win32", "cygwin", "msys")


def detect_linux() -> bool:
    return sys.platform.startswith("linux") and not detect_termux()


def detect_architecture() -> str:
    import platform
    return platform.machine() or platform.processor() or "unknown"


def detect_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def detect_platform_name() -> str:
    import platform
    if detect_termux():
        version = os.environ.get("TERMUX_VERSION", "")
        return f"Termux {version}" if version else "Termux"
    if detect_macos():
        return f"macOS {platform.mac_ver()[0]}"
    if detect_windows():
        return f"Windows {platform.release()}"
    if detect_linux():
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as handle:
                data = handle.read()
            for line in data.splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
        return "Linux"
    return f"{platform.system()} {platform.release()}"


def detect_package_managers() -> list[str]:
    found: list[str] = []
    if detect_termux():
        if shutil.which("pkg"):
            found.append("pkg")
        return found
    if detect_macos():
        if shutil.which("brew"):
            found.append("brew")
        return found
    if detect_windows():
        for c in ("winget", "choco", "scoop"):
            if shutil.which(c):
                found.append(c)
        return found
    if detect_linux():
        for c in ("apt", "apt-get", "dnf", "yum", "pacman", "zypper", "apk"):
            if shutil.which(c):
                found.append(c)
        return found
    return found


def detect_shell() -> str:
    return os.environ.get("SHELL") or os.environ.get("COMSPEC") or "unknown"


@dataclass
class EnvironmentInfo:
    platform_name: str = "Unknown"
    platform_kind: str = "unknown"
    architecture: str = "unknown"
    python_version: str = ""
    is_termux: bool = False
    is_linux: bool = False
    is_windows: bool = False
    is_macos: bool = False
    package_managers: list[str] = field(default_factory=list)
    shell: str = ""


def detect_environment() -> EnvironmentInfo:
    info = EnvironmentInfo(
        platform_name=detect_platform_name(),
        architecture=detect_architecture(),
        python_version=detect_python_version(),
        shell=detect_shell(),
        package_managers=detect_package_managers(),
    )
    if detect_termux():
        info.is_termux = True
        info.platform_kind = "termux"
    elif detect_linux():
        info.is_linux = True
        info.platform_kind = "linux"
    elif detect_macos():
        info.is_macos = True
        info.platform_kind = "macos"
    elif detect_windows():
        info.is_windows = True
        info.platform_kind = "windows"
    return info


@dataclass
class ToolStatus:
    name: str
    executable: str | None = None
    version: str | None = None
    available: bool = False
    functional: bool = False
    install_command: str | None = None
    last_error: str | None = None


@dataclass
class RuntimeOptions:
    no_color: bool = False
    no_animation: bool = False
    verbose: bool = False
    debug: bool = False
    dry_run: bool = False
    json_output: bool = False
    yes: bool = False
    scan_only: bool = False
    clean_only: bool = False
    install_deps: bool = False
    output_path: str | None = None
    recursive: bool = False
    input_path: str | None = None


@dataclass
class DetectedFile:
    path: Path
    exists: bool
    is_regular: bool
    is_symlink: bool
    size_bytes: int
    extension: str
    mime_type: str
    mime_short: str
    magic_description: str
    signature_format: str
    detected_format: str
    extension_matches: bool
    readable: bool
    error: str | None = None


@dataclass
class MetadataSnapshot:
    source: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    groups: dict[str, dict[str, str]] = field(default_factory=dict)
    privacy_sensitive: dict[str, str] = field(default_factory=dict)
    warning: str | None = None
    error: str | None = None
    raw: Any = None


@dataclass
class CleanResult:
    success: bool = False
    output_path: Path | None = None
    cleaner_name: str = ""
    method: str = ""
    removed_fields: list[str] = field(default_factory=list)
    retained_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_output: str = ""
    exit_code: int = 0
    did_transcode: bool = False


EXTENSION_TO_FORMAT: dict[str, str] = {
    ".jpg": "jpeg", ".jpeg": "jpeg", ".jpe": "jpeg", ".jfif": "jpeg",
    ".png": "png", ".gif": "gif", ".bmp": "bmp", ".tiff": "tiff", ".tif": "tiff",
    ".webp": "webp", ".heic": "heic", ".heif": "heic", ".avif": "avif",
    ".cr2": "cr2", ".cr3": "cr3", ".nef": "nef", ".arw": "arw", ".dng": "dng",
    ".psd": "psd", ".mp4": "mp4", ".m4v": "m4v", ".mov": "mov", ".mkv": "matroska",
    ".avi": "avi", ".webm": "webm", ".3gp": "3gp", ".3g2": "3g2", ".mts": "mts",
    ".flv": "flv", ".wmv": "wmv", ".mp3": "mp3", ".flac": "flac", ".wav": "wave",
    ".aac": "aac", ".m4a": "m4a", ".ogg": "ogg", ".opus": "opus", ".wma": "wma",
    ".aiff": "aiff", ".pdf": "pdf", ".py": "python_source", ".js": "javascript_source",
    ".ts": "typescript_source", ".java": "java_source", ".c": "c_source",
    ".cpp": "cpp_source", ".h": "c_header", ".rs": "rust_source", ".go": "go_source",
    ".rb": "ruby_source", ".sh": "shell_source", ".ps1": "powershell_source",
    ".bat": "batch_source", ".cmd": "batch_source", ".txt": "plain_text",
    ".md": "markdown", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".xml": "xml", ".html": "html", ".htm": "html", ".css": "css", ".csv": "csv",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini", ".log": "log_text",
}

SOURCE_FORMATS = {
    "python_source", "javascript_source", "typescript_source", "java_source",
    "c_source", "cpp_source", "c_header", "cpp_header", "rust_source",
    "go_source", "ruby_source", "shell_source", "powershell_source",
    "batch_source", "plain_text", "markdown", "json", "yaml", "xml",
    "html", "css", "csv", "toml", "ini", "log_text", "text", "rst_text", "scss", "tsv",
}

EXTENSION_BY_FORMAT: dict[str, str] = {
    "jpeg": ".jpg", "png": ".png", "gif": ".gif", "bmp": ".bmp",
    "tiff": ".tiff", "webp": ".webp", "heic": ".heic", "avif": ".avif",
    "psd": ".psd", "mp4": ".mp4", "m4v": ".m4v", "mov": ".mov",
    "matroska": ".mkv", "avi": ".avi", "webm": ".webm", "3gp": ".3gp",
    "3g2": ".3g2", "mts": ".mts", "flv": ".flv", "wmv": ".wmv",
    "mp3": ".mp3", "flac": ".flac", "wave": ".wav", "aac": ".aac",
    "m4a": ".m4a", "ogg": ".ogg", "opus": ".opus", "wma": ".wma",
    "aiff": ".aiff", "pdf": ".pdf",
}


def is_privacy_sensitive(key: str) -> bool:
    if not key:
        return False
    k = key.lower().strip()
    for n in PRIVACY_SENSITIVE_KEYS:
        if n in k:
            return True
    if "gps" in k or "location" in k:
        return True
    if "serial" in k:
        return True
    if "author" in k or "creator" in k or "owner" in k:
        return True
    if "camera" in k or "make" in k or "model" in k:
        return True
    if "datetimeoriginal" in k or "createdate" in k or "modifydate" in k:
        return True
    return False


def _stringify_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        parts = [_stringify_value(v) for v in value]
        return ", ".join(p for p in parts if p) or None
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float) and value != value:
        return None
    return str(value)


def detect_signature_format(path: Path) -> tuple[str, str]:
    try:
        with path.open("rb") as handle:
            head = handle.read(64)
    except OSError:
        return "unknown", "application/octet-stream"
    if not head:
        return "unknown", "application/octet-stream"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg", "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "gif", "image/gif"
    if head.startswith(b"BM"):
        return "bmp", "image/bmp"
    if head.startswith(b"II*\x00") or head.startswith(b"MM\x00*"):
        return "tiff", "image/tiff"
    if head.startswith(b"RIFF") and len(head) >= 12:
        fc = head[8:12]
        if fc == b"WEBP": return "webp", "image/webp"
        if fc == b"WAVE": return "wave", "audio/wav"
        if fc == b"AVI ": return "avi", "video/x-msvideo"
        return "riff", "application/octet-stream"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        sub = head[4:8] if len(head) >= 8 else b""
        if sub.startswith(b"B2"): return "webm", "video/webm"
        return "matroska", "video/x-matroska"
    if head.startswith(b"\x00\x00\x00") and len(head) >= 12 and head[4:8] == b"ftyp":
        return "mp4_family", "video/mp4"
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06"):
        return "zip", "application/zip"
    if head.startswith(b"%PDF"):
        return "pdf", "application/pdf"
    if head.startswith(b"OggS"):
        return "ogg", "audio/ogg"
    if head.startswith(b"ID3") or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xfa"):
        return "mp3", "audio/mpeg"
    if head.startswith(b"fLaC"):
        return "flac", "audio/flac"
    if head.startswith(b"FORM") and len(head) >= 12 and head[8:12] in (b"AIFF", b"AIFC"):
        return "aiff", "audio/aiff"
    if head.startswith(b"FLV"):
        return "flv", "video/x-flv"
    if head.startswith(b"\x30\x26\xb2\x75"):
        return "wmv", "video/x-ms-wmv"
    text_chars = set(range(9, 14)) | set(range(32, 127)) | {0}
    non_text = sum(1 for b in head if b not in text_chars)
    if non_text / max(len(head), 1) < 0.10:
        return "text", "text/plain"
    return "binary", "application/octet-stream"


def probe_magic(path: Path) -> tuple[str, str]:
    try:
        result = subprocess.run(["file", "-b", "--mime-type", str(path)], capture_output=True, text=True, check=False, timeout=10)
        mime = result.stdout.strip() if result.returncode == 0 else "application/octet-stream"
        result_desc = subprocess.run(["file", "-b", str(path)], capture_output=True, text=True, check=False, timeout=10)
        desc = result_desc.stdout.strip() if result_desc.returncode == 0 else ""
        return mime, desc
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "application/octet-stream", ""


def detect_format_from_mime(mime: str) -> str:
    if not mime:
        return "unknown"
    m = mime.lower()
    mapping = {
        "image/jpeg": "jpeg", "image/jpg": "jpeg", "image/png": "png",
        "image/gif": "gif", "image/bmp": "bmp", "image/tiff": "tiff",
        "image/webp": "webp", "image/heic": "heic", "image/heif": "heic",
        "image/avif": "avif", "image/vnd.adobe.photoshop": "psd",
        "video/mp4": "mp4", "video/quicktime": "mov", "video/x-m4v": "m4v",
        "video/x-matroska": "matroska", "video/webm": "webm",
        "video/x-msvideo": "avi", "video/3gpp": "3gp", "video/mp2t": "mts",
        "video/x-flv": "flv", "video/x-ms-wmv": "wmv", "audio/mpeg": "mp3",
        "audio/flac": "flac", "audio/wav": "wave", "audio/x-wav": "wave",
        "audio/aac": "aac", "audio/mp4": "m4a", "audio/x-m4a": "m4a",
        "audio/ogg": "ogg", "audio/opus": "opus", "audio/x-ms-wma": "wma",
        "audio/aiff": "aiff", "application/pdf": "pdf", "text/plain": "text",
        "text/html": "html", "text/css": "css", "application/json": "json",
        "application/xml": "xml", "text/xml": "xml", "application/yaml": "yaml",
        "application/zip": "zip",
    }
    if m in mapping:
        return mapping[m]
    if m.startswith("text/"):
        return "text"
    return "unknown"


def detect_format_from_extension(ext: str) -> str:
    return EXTENSION_TO_FORMAT.get(ext.lower(), "unknown") if ext else "unknown"


def detect_file(path_str: str) -> DetectedFile:
    raw_path = Path(path_str).expanduser()
    detected = DetectedFile(
        path=raw_path, exists=raw_path.exists(), is_regular=False,
        is_symlink=raw_path.is_symlink(), size_bytes=0,
        extension=raw_path.suffix.lower(), mime_type="application/octet-stream",
        mime_short="binary", magic_description="", signature_format="unknown",
        detected_format="unknown", extension_matches=True, readable=False,
    )
    if not detected.exists:
        detected.error = "File does not exist"
        return detected
    if detected.is_symlink:
        target = raw_path.resolve()
        if not target.exists():
            detected.error = "Symlink target does not exist"
            return detected
    if not raw_path.is_file():
        detected.error = "Path is not a regular file"
        return detected
    try:
        detected.size_bytes = raw_path.stat().st_size
    except OSError as exc:
        detected.error = f"Cannot stat file: {exc}"
        return detected
    if detected.size_bytes == 0:
        detected.error = "File is empty"
        return detected
    try:
        with raw_path.open("rb") as handle:
            handle.read(1)
        detected.readable = True
    except OSError as exc:
        detected.error = f"File is not readable: {exc}"
        return detected
    detected.is_regular = True
    sig_format, sig_mime = detect_signature_format(raw_path)
    detected.signature_format = sig_format
    magic_mime, magic_desc = probe_magic(raw_path)
    detected.mime_type = magic_mime if magic_mime and magic_mime != "application/octet-stream" else sig_mime
    detected.mime_short = detected.mime_type.split("/", 1)[-1] if "/" in detected.mime_type else detected.mime_type
    detected.magic_description = magic_desc
    ext_format = detect_format_from_extension(detected.extension)
    mime_format = detect_format_from_mime(detected.mime_type)
    for candidate in [mime_format, sig_format, ext_format]:
        if candidate and candidate != "unknown":
            detected.detected_format = candidate
            break
    if detected.detected_format == "mp4_family":
        detected.detected_format = "mp4"
    if detected.detected_format == "text" and ext_format != "unknown" and ext_format != "text":
        detected.detected_format = ext_format
    if detected.detected_format == "unknown" and ext_format != "unknown":
        detected.detected_format = ext_format
    if ext_format != "unknown" and ext_format != detected.detected_format:
        if ext_format in SOURCE_FORMATS and detected.detected_format == "text":
            detected.extension_matches = True
        elif detected.detected_format == "mp4" and ext_format in {"mp4", "m4v"}:
            detected.extension_matches = True
        else:
            detected.extension_matches = False
    elif ext_format == "unknown" and detected.extension:
        detected.extension_matches = False
    else:
        detected.extension_matches = True
    return detected


def run_exiftool_inspect(path: Path, exe: str) -> MetadataSnapshot:
    snap = MetadataSnapshot(source="exiftool")
    try:
        result = subprocess.run([exe, "-G", "-j", "-n", "-q", "-q", str(path)], capture_output=True, text=True, check=False, timeout=60)
    except (subprocess.TimeoutExpired, OSError) as exc:
        snap.error = str(exc)
        return snap
    if result.returncode != 0:
        snap.error = result.stderr.strip() or f"Exit {result.returncode}"
        return snap
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        snap.error = f"Invalid JSON: {exc}"
        return snap
    if not isinstance(parsed, list) or not parsed:
        snap.error = "Empty result"
        return snap
    record = parsed[0]
    snap.raw = record
    for k, v in record.items():
        if k in ("SourceFile", "ExifToolVersion", "FileName", "Directory", "FilePermissions"):
            continue
        group = k.split(":", 1)[0] if ":" in k else "Other"
        name = k.split(":", 1)[1] if ":" in k else k
        text = _stringify_value(v)
        if text is None:
            continue
        snap.fields[k] = text
        snap.groups.setdefault(group, {})[name] = text
        if is_privacy_sensitive(k) or is_privacy_sensitive(name):
            snap.privacy_sensitive[k] = text
    return snap


def run_ffprobe_inspect(path: Path, exe: str) -> MetadataSnapshot:
    snap = MetadataSnapshot(source="ffprobe")
    try:
        result = subprocess.run([exe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)], capture_output=True, text=True, check=False, timeout=60)
    except (subprocess.TimeoutExpired, OSError) as exc:
        snap.error = str(exc)
        return snap
    if result.returncode != 0:
        snap.error = result.stderr.strip() or f"Exit {result.returncode}"
        return snap
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        snap.error = f"Invalid JSON: {exc}"
        return snap
    snap.raw = parsed
    fmt = parsed.get("format", {}) if isinstance(parsed, dict) else {}
    for k, v in fmt.items():
        if k in ("filename", "nb_streams", "nb_programs", "format_name", "format_long_name", "duration", "size", "bit_rate", "probe_score"):
            continue
        if k == "tags" and isinstance(v, dict):
            for tk, tv in v.items():
                text = _stringify_value(tv)
                if text is None:
                    continue
                full_key = f"Format:tags:{tk}"
                snap.fields[full_key] = text
                snap.groups.setdefault("Format:tags", {})[tk] = text
                if is_privacy_sensitive(tk):
                    snap.privacy_sensitive[full_key] = text
            continue
        text = _stringify_value(v)
        if text is None:
            continue
        snap.fields[f"Format:{k}"] = text
        snap.groups.setdefault("Format", {})[k] = text
        if is_privacy_sensitive(k):
            snap.privacy_sensitive[f"Format:{k}"] = text
    streams = parsed.get("streams", []) if isinstance(parsed, dict) else []
    for idx, stream in enumerate(streams):
        if not isinstance(stream, dict):
            continue
        for k, v in stream.items():
            if k in ("index", "codec_name", "codec_long_name", "codec_type", "profile", "level", "pix_fmt", "sample_rate", "channels", "channel_layout", "width", "height", "r_frame_rate", "avg_frame_rate", "duration", "bit_rate", "nb_frames", "codec_tag", "codec_tag_string", "time_base", "start_pts", "start_time", "duration_ts", "disposition"):
                continue
            if k == "tags" and isinstance(v, dict):
                for tk, tv in v.items():
                    text = _stringify_value(tv)
                    if text is None:
                        continue
                    full_key = f"Stream{idx}:tags:{tk}"
                    snap.fields[full_key] = text
                    snap.groups.setdefault(f"Stream{idx}:tags", {})[tk] = text
                    if is_privacy_sensitive(tk):
                        snap.privacy_sensitive[full_key] = text
                continue
            text = _stringify_value(v)
            if text is None:
                continue
            full = f"Stream{idx}:{k}"
            snap.fields[full] = text
            snap.groups.setdefault(f"Stream{idx}", {})[k] = text
            if is_privacy_sensitive(k):
                snap.privacy_sensitive[full] = text
    return snap


def inspect_metadata(detected: DetectedFile, exiftool: ToolStatus | None, ffmpeg: ToolStatus | None) -> MetadataSnapshot:
    fmt = detected.detected_format
    if fmt in {"jpeg", "png", "gif", "bmp", "tiff", "webp", "heic", "heif", "avif", "cr2", "nef", "arw", "dng", "psd", "pdf"}:
        if exiftool and exiftool.functional:
            return run_exiftool_inspect(detected.path, exiftool.executable)
        return MetadataSnapshot(error="ExifTool not available for this format")
    if fmt in {"mp4", "mov", "m4v", "matroska", "avi", "webm", "3gp", "3g2", "mts", "flv", "wmv", "mp3", "flac", "wave", "aac", "m4a", "ogg", "opus", "wma", "aiff"}:
        probe = _find_ffprobe(ffmpeg)
        if probe:
            return run_ffprobe_inspect(detected.path, probe)
        if exiftool and exiftool.functional:
            return run_exiftool_inspect(detected.path, exiftool.executable)
        return MetadataSnapshot(error="Neither ffprobe nor ExifTool available")
    if fmt == "unknown" or fmt == "binary":
        if exiftool and exiftool.functional:
            snap = run_exiftool_inspect(detected.path, exiftool.executable)
            if not snap.error:
                return snap
        return MetadataSnapshot(warning="No metadata inspection available", fields={})
    return MetadataSnapshot(warning="No embedded metadata inspection for text/source files", fields={})


def _find_ffprobe(ffmpeg_tool: ToolStatus | None) -> str | None:
    if not ffmpeg_tool or not ffmpeg_tool.executable:
        return None
    candidate = Path(ffmpeg_tool.executable).with_name("ffprobe")
    if candidate.exists():
        return str(candidate)
    return shutil.which("ffprobe")


def find_executable(name: str) -> str | None:
    return shutil.which(name)


def run_version_command(exe: str, args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run([exe, *args], capture_output=True, text=True, check=False, timeout=15)
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and output:
            return True, output
        return False, output or f"Exit {result.returncode}"
    except FileNotFoundError:
        return False, "Not found"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)


def verify_tool_functional(exe: str, name: str) -> tuple[bool, str | None]:
    if name == "exiftool":
        ok, out = run_version_command(exe, ["-ver"])
        if ok and any(c.isdigit() for c in out):
            return True, out.splitlines()[0] if out else out
        return False, out
    if name == "ffmpeg":
        ok, out = run_version_command(exe, ["-version"])
        if ok and "ffmpeg version" in out.lower():
            return True, out.splitlines()[0]
        return False, out
    if name == "qpdf":
        ok, out = run_version_command(exe, ["--version"])
        if ok and "qpdf version" in out.lower():
            return True, out.splitlines()[0]
        return False, out
    return False, "Unknown"


REQUIRED_TOOLS = [
    {"name": "exiftool", "executables": ["exiftool"]},
    {"name": "ffmpeg", "executables": ["ffmpeg"]},
    {"name": "qpdf", "executables": ["qpdf"]},
]


def get_install_command(name: str, env: EnvironmentInfo) -> str | None:
    if not env.package_managers:
        return None
    pm = env.package_managers[0]
    table = {
        ("exiftool", "pkg"): "pkg install -y perl && cpan -f -i Image::ExifTool",
        ("ffmpeg", "pkg"): "pkg install -y ffmpeg",
        ("qpdf", "pkg"): "pkg install -y qpdf",
        ("exiftool", "apt"): "sudo -n apt install -y libimage-exiftool-perl 2>/dev/null || sudo apt install -y libimage-exiftool-perl || apt install -y libimage-exiftool-perl",
        ("ffmpeg", "apt"): "sudo -n apt install -y ffmpeg 2>/dev/null || sudo apt install -y ffmpeg || apt install -y ffmpeg",
        ("qpdf", "apt"): "sudo -n apt install -y qpdf 2>/dev/null || sudo apt install -y qpdf || apt install -y qpdf",
        ("exiftool", "apt-get"): "sudo -n apt-get install -y libimage-exiftool-perl 2>/dev/null || sudo apt-get install -y libimage-exiftool-perl || apt-get install -y libimage-exiftool-perl",
        ("ffmpeg", "apt-get"): "sudo -n apt-get install -y ffmpeg 2>/dev/null || sudo apt-get install -y ffmpeg || apt-get install -y ffmpeg",
        ("qpdf", "apt-get"): "sudo -n apt-get install -y qpdf 2>/dev/null || sudo apt-get install -y qpdf || apt-get install -y qpdf",
        ("exiftool", "dnf"): "sudo -n dnf install -y perl-Image-ExifTool 2>/dev/null || sudo dnf install -y perl-Image-ExifTool || dnf install -y perl-Image-ExifTool",
        ("ffmpeg", "dnf"): "sudo -n dnf install -y ffmpeg 2>/dev/null || sudo dnf install -y ffmpeg || dnf install -y ffmpeg",
        ("qpdf", "dnf"): "sudo -n dnf install -y qpdf 2>/dev/null || sudo dnf install -y qpdf || dnf install -y qpdf",
        ("exiftool", "pacman"): "sudo -n pacman -S --noconfirm perl-image-exiftool 2>/dev/null || sudo pacman -S --noconfirm perl-image-exiftool || pacman -S --noconfirm perl-image-exiftool",
        ("ffmpeg", "pacman"): "sudo -n pacman -S --noconfirm ffmpeg 2>/dev/null || sudo pacman -S --noconfirm ffmpeg || pacman -S --noconfirm ffmpeg",
        ("qpdf", "pacman"): "sudo -n pacman -S --noconfirm qpdf 2>/dev/null || sudo pacman -S --noconfirm qpdf || pacman -S --noconfirm qpdf",
        ("exiftool", "zypper"): "sudo -n zypper --non-interactive install perl-Image-ExifTool 2>/dev/null || sudo zypper --non-interactive install perl-Image-ExifTool || zypper --non-interactive install perl-Image-ExifTool",
        ("ffmpeg", "zypper"): "sudo -n zypper --non-interactive install ffmpeg 2>/dev/null || sudo zypper --non-interactive install ffmpeg || zypper --non-interactive install ffmpeg",
        ("qpdf", "zypper"): "sudo -n zypper --non-interactive install qpdf 2>/dev/null || sudo zypper --non-interactive install qpdf || zypper --non-interactive install qpdf",
        ("exiftool", "apk"): "doas apk add --no-cache exiftool 2>/dev/null || sudo -n apk add --no-cache exiftool 2>/dev/null || apk add --no-cache exiftool",
        ("ffmpeg", "apk"): "doas apk add --no-cache ffmpeg 2>/dev/null || sudo -n apk add --no-cache ffmpeg 2>/dev/null || apk add --no-cache ffmpeg",
        ("qpdf", "apk"): "doas apk add --no-cache qpdf 2>/dev/null || sudo -n apk add --no-cache qpdf 2>/dev/null || apk add --no-cache qpdf",
        ("exiftool", "brew"): "brew install exiftool",
        ("ffmpeg", "brew"): "brew install ffmpeg",
        ("qpdf", "brew"): "brew install qpdf",
        ("exiftool", "winget"): "winget install --silent --accept-source-agreements --accept-package-agreements Oliver.Bettenworth.ExifTool",
        ("ffmpeg", "winget"): "winget install --silent --accept-source-agreements --accept-package-agreements Gyan.FFmpeg",
        ("qpdf", "winget"): "winget install --silent --accept-source-agreements --accept-package-agreements QPDF.QPDF",
        ("exiftool", "choco"): "choco install exiftool -y",
        ("ffmpeg", "choco"): "choco install ffmpeg -y",
        ("qpdf", "choco"): "choco install qpdf -y",
        ("exiftool", "scoop"): "scoop install exiftool",
        ("ffmpeg", "scoop"): "scoop install ffmpeg",
        ("qpdf", "scoop"): "scoop install qpdf",
    }
    return table.get((name, pm))


def check_tool(spec: dict) -> ToolStatus:
    status = ToolStatus(name=str(spec["name"]))
    for exe_name in spec["executables"]:
        path = find_executable(str(exe_name))
        if path:
            status.executable = path
            status.available = True
            ok, info = verify_tool_functional(path, status.name)
            status.functional = ok
            if ok:
                status.version = info
            else:
                status.last_error = info
            break
    return status


def check_all_tools(env: EnvironmentInfo) -> list[ToolStatus]:
    statuses = [check_tool(spec) for spec in REQUIRED_TOOLS]
    for s in statuses:
        if not s.available:
            s.install_command = get_install_command(s.name, env)
    return statuses


def recheck_tool(name: str) -> ToolStatus:
    for spec in REQUIRED_TOOLS:
        if str(spec["name"]) == name:
            return check_tool(spec)
    return ToolStatus(name=name)


class CleanerBase(ABC):
    name: str = "Base"
    supported_formats: tuple = ()
    required_tools: tuple = ()
    can_write_formats: tuple = ()

    def __init__(self, tools: dict, options: RuntimeOptions):
        self.tools = tools
        self.options = options

    @classmethod
    def supports(cls, fmt): return fmt in cls.supported_formats
    @classmethod
    def can_write(cls, fmt): return fmt in (cls.can_write_formats or cls.supported_formats)
    @classmethod
    def is_available(cls, tools):
        return all(tools.get(t) and tools.get(t).functional for t in cls.required_tools)

    @abstractmethod
    def clean(self, detected, output_path, before_snapshot): raise NotImplementedError

    def describe_action(self, detected, output_path):
        return f"{self.name} -> {output_path.name}"


class ExifToolCleaner(CleanerBase):
    name = "ExifTool"
    supported_formats = ("jpeg", "png", "gif", "bmp", "tiff", "webp", "heic", "heif", "avif", "cr2", "cr3", "nef", "arw", "dng", "raf", "rw2", "orf", "psd", "ico", "pdf")
    can_write_formats = supported_formats
    required_tools = ("exiftool",)

    def clean(self, detected, output_path, before_snapshot):
        result = CleanResult(cleaner_name=self.name, method="exiftool_rewrite")
        tool = self.tools.get("exiftool")
        if not tool or not tool.executable:
            result.errors.append("ExifTool unavailable")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            tool.executable, "-overwrite_original", "-all=",
            "-tagsfromfile", "@", "-unsafe",
            "-icc_profile:all", "-make=", "-model=", "-software=",
            "-comment=", "-title=", "-author=", "-artist=",
            "-copyright=", "-ownername=", "-serialnumber=",
            "-gps:all=", "-xmp:all=", "-iptc:all=", "-exif:all=",
            "-photoshop:all=", str(detected.path), "-o", str(output_path),
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        except (subprocess.TimeoutExpired, OSError) as exc:
            result.errors.append(str(exc))
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            result.errors.append(f"Exit {completed.returncode}: {completed.stderr.strip()}")
            return result
        if not output_path.exists() or output_path.stat().st_size == 0:
            result.errors.append("No valid output produced")
            return result
        after = run_exiftool_inspect(output_path, tool.executable)
        if not after.error:
            before_keys = set(before_snapshot.fields.keys())
            after_keys = set(after.fields.keys())
            result.removed_fields = sorted(before_keys - after_keys)
            result.retained_fields = sorted(before_keys & after_keys)
        result.success = True
        result.output_path = output_path
        return result


class FFmpegCleaner(CleanerBase):
    name = "FFmpeg"
    supported_formats = ("mp4", "mov", "m4v", "matroska", "avi", "webm", "3gp", "3g2", "mts", "flv", "wmv", "mp3", "flac", "wave", "aac", "m4a", "ogg", "opus", "wma", "aiff")
    can_write_formats = supported_formats
    required_tools = ("ffmpeg",)
    CONTAINERS = {
        "mp4": "mp4", "mov": "mov", "m4v": "mp4", "matroska": "matroska",
        "avi": "avi", "webm": "webm", "3gp": "3gp", "3g2": "3gp",
        "mts": "mpegts", "flv": "flv", "wmv": "asf", "mp3": "mp3",
        "flac": "flac", "wave": "wav", "aac": "adts", "m4a": "ipod",
        "ogg": "ogg", "opus": "ogg", "wma": "asf", "aiff": "aiff",
    }

    def clean(self, detected, output_path, before_snapshot):
        result = CleanResult(cleaner_name=self.name, method="ffmpeg_stream_copy")
        tool = self.tools.get("ffmpeg")
        if not tool or not tool.executable:
            result.errors.append("FFmpeg unavailable")
            return result
        container = self.CONTAINERS.get(detected.detected_format)
        if not container:
            result.errors.append(f"No container mapping for {detected.detected_format}")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        command = [
            tool.executable, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(detected.path),
            "-map_metadata", "-1", "-map_chapters", "-1",
            "-codec", "copy", "-map", "0",
        ]
        if detected.detected_format in {"mp4", "mov", "m4v", "3gp", "3g2"}:
            command.extend(["-movflags", "+faststart"])
        command.extend(["-f", container, str(output_path)])
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
        except (subprocess.TimeoutExpired, OSError) as exc:
            result.errors.append(str(exc))
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            result.errors.append(f"FFmpeg exit {completed.returncode}: {completed.stderr.strip()}")
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
            return result
        if not output_path.exists() or output_path.stat().st_size == 0:
            if output_path.exists():
                output_path.unlink()
            result.errors.append("Empty output")
            return result
        ffprobe = _find_ffprobe(tool)
        if ffprobe:
            after = run_ffprobe_inspect(output_path, ffprobe)
            if not after.error:
                before_keys = set(before_snapshot.fields.keys())
                after_keys = set(after.fields.keys())
                result.removed_fields = sorted(before_keys - after_keys)
                result.retained_fields = sorted(before_keys & after_keys)
        result.success = True
        result.output_path = output_path
        return result


class QpdfCleaner(CleanerBase):
    name = "qpdf"
    supported_formats = ("pdf",)
    can_write_formats = ("pdf",)
    required_tools = ("qpdf",)

    def clean(self, detected, output_path, before_snapshot):
        result = CleanResult(cleaner_name=self.name, method="qpdf_linearize")
        tool = self.tools.get("qpdf")
        if not tool or not tool.executable:
            result.errors.append("qpdf unavailable")
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        result.warnings.append("Metadata cleaning is not equivalent to full PDF sanitization.")
        command = [
            tool.executable, "--linearize",
            "--remove-unreferenced-resources=yes",
            "--object-streams=generate", "--recompress-flate",
            "--compression-level=9", str(detected.path), str(output_path),
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=180)
        except (subprocess.TimeoutExpired, OSError) as exc:
            result.errors.append(str(exc))
            return result
        result.raw_output = (completed.stdout + "\n" + completed.stderr).strip()
        result.exit_code = completed.returncode
        if completed.returncode != 0:
            result.errors.append(f"qpdf exit {completed.returncode}: {completed.stderr.strip()}")
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
            return result
        if not output_path.exists() or output_path.stat().st_size == 0:
            if output_path.exists():
                output_path.unlink()
            result.errors.append("Empty output")
            return result
        exiftool = self.tools.get("exiftool")
        if exiftool and exiftool.functional:
            after = run_exiftool_inspect(output_path, exiftool.executable)
            if not after.error:
                before_keys = set(before_snapshot.fields.keys())
                after_keys = set(after.fields.keys())
                result.removed_fields = sorted(before_keys - after_keys)
                result.retained_fields = sorted(before_keys & after_keys)
        result.success = True
        result.output_path = output_path
        return result


class UnsupportedCleaner(CleanerBase):
    name = "Unsupported"
    supported_formats = ()
    required_tools = ()

    @classmethod
    def supports(cls, fmt): return False
    @classmethod
    def is_available(cls, tools): return True

    def clean(self, detected, output_path, before_snapshot):
        result = CleanResult(cleaner_name=self.name, method="none")
        result.errors.append(f"Format '{detected.detected_format}' not supported for cleaning.")
        return result


CLEANER_REGISTRY = [ExifToolCleaner, QpdfCleaner, FFmpegCleaner, UnsupportedCleaner]


def select_cleaner(fmt, tools):
    matches = [c for c in CLEANER_REGISTRY if c.supports(fmt) and c.is_available(tools)]
    if not matches:
        return None
    if UnsupportedCleaner in matches and len(matches) > 1:
        matches = [m for m in matches if m is not UnsupportedCleaner]
    return matches[0]


def route(detected, tools, options):
    fmt = detected.detected_format
    warnings = []
    if not detected.extension_matches:
        warnings.append(f"Extension '{detected.extension or '(none)'}' disagrees with detected format '{fmt}'.")
    cleaner_cls = select_cleaner(fmt, tools)
    if cleaner_cls is None:
        if fmt in SOURCE_FORMATS:
            return type("D", (), {
                "detected_format": fmt, "cleaner_cls": UnsupportedCleaner,
                "cleaner_name": "Unsupported", "can_write": False,
                "required_tools_present": True, "missing_tools": [],
                "reason": "Text and source files do not carry embedded metadata requiring cleaning.",
                "warnings": warnings,
            })()
        return type("D", (), {
            "detected_format": fmt, "cleaner_cls": UnsupportedCleaner,
            "cleaner_name": "Unsupported", "can_write": False,
            "required_tools_present": False, "missing_tools": [],
            "reason": f"No registered cleaner supports format '{fmt}'.",
            "warnings": warnings,
        })()
    missing = [t for t in cleaner_cls.required_tools if not (tools.get(t) and tools.get(t).functional)]
    if missing:
        return type("D", (), {
            "detected_format": fmt, "cleaner_cls": UnsupportedCleaner,
            "cleaner_name": "Unsupported", "can_write": False,
            "required_tools_present": False, "missing_tools": missing,
            "reason": f"Cleaner '{cleaner_cls.name}' requires missing tools: {', '.join(missing)}",
            "warnings": warnings,
        })()
    return type("D", (), {
        "detected_format": fmt, "cleaner_cls": cleaner_cls,
        "cleaner_name": cleaner_cls.name, "can_write": True,
        "required_tools_present": True, "missing_tools": [],
        "reason": f"Cleaner '{cleaner_cls.name}' selected.",
        "warnings": warnings,
    })()


class ColorPalette:
    def __init__(self, enabled=True):
        self.enabled = enabled
    def _w(self, code, text):
        return f"{code}{text}{RESET}" if self.enabled else text
    def green(self, t): return self._w(C_NEON, t)
    def blue(self, t): return self._w(C_BLUE, t)
    def cyan(self, t): return self._w(C_AQUA, t)
    def yellow(self, t): return self._w(C_YELLOW, t)
    def red(self, t): return self._w(C_RED, t)
    def gray(self, t): return self._w(C_GRAY, t)
    def bold(self, t): return self._w(BOLD, t)
    def aqua(self, t): return self._w(C_AQUA, t)
    def aqua_bright(self, t): return self._w(C_AQUA_BRIGHT, t)
    def aqua_dim(self, t): return self._w(C_BLUE_DIM, t)
    def blue_bright(self, t): return self._w(C_BLUE_BRIGHT, t)
    def blue_dim(self, t): return self._w(C_BLUE_DIM, t)
    def neon(self, t): return self._w(C_NEON, t)
    def label(self, t): return self._w(C_BLUE_DIM, t)
    def value(self, t): return self._w(C_AQUA, t)
    def success(self, t): return self._w(C_NEON, t)


def should_enable_color(no_color_flag):
    if no_color_flag: return False
    if os.environ.get("NO_COLOR"): return False
    if os.environ.get("CLICOLOR_FORCE") and os.environ.get("CLICOLOR_FORCE") != "0": return True
    if os.environ.get("CLICOLOR") == "0": return False
    if not sys.stdout.isatty() and not sys.stderr.isatty(): return False
    if os.environ.get("TERM") == "dumb": return False
    return True


def should_enable_animation(no_animation_flag):
    if no_animation_flag: return False
    if os.environ.get("METACLEAN_NO_ANIMATION"): return False
    if os.environ.get("CLICOLOR_FORCE") and os.environ.get("CLICOLOR_FORCE") != "0":
        pass
    elif not sys.stdout.isatty():
        return False
    if os.environ.get("CI") or os.environ.get("CONTINUOUS_INTEGRATION"): return False
    if os.environ.get("TERM") == "dumb": return False
    return True


def is_ci_environment():
    return any(os.environ.get(n) for n in ("CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "CIRCLECI", "TRAVIS", "BUILD_NUMBER"))


def _visible_len(text):
    import re
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))


def _terminal_width():
    try:
        import shutil
        return shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        return 80


def _logo_max_width():
    return max(_visible_len(line) for line in LOGO_LINES)


def _center_line(text, target_width):
    visible = _visible_len(text)
    if visible >= target_width:
        return text
    padding = (target_width - visible) // 2
    return " " * padding + text


def _gradient_color(t, enabled):
    if not enabled:
        return ""
    t = max(0.0, min(1.0, float(t)))
    r = int(0 + (80 - 0) * t)
    g = int(180 + (255 - 180) * t)
    b = int(160 + (220 - 160) * t)
    return f"\x1b[38;2;{r};{g};{b}m"


def _colorize_line_gradient(line, index, total, enabled, bold=False):
    if not enabled:
        return line
    if not line:
        return line
    t = index / max(total - 1, 1)
    color = _gradient_color(t, enabled)
    prefix = "\x1b[1m" if bold else ""
    return f"{prefix}{color}{line}{RESET}"


def render_logo_gradient(palette):
    total = len(LOGO_LINES)
    term_width = _terminal_width()
    logo_width = _logo_max_width()
    target_width = min(term_width, max(logo_width, 60))
    colored = [
        _colorize_line_gradient(line, idx, total, palette.enabled, bold=True)
        for idx, line in enumerate(LOGO_LINES)
    ]
    centered = [_center_line(line, target_width) for line in colored]
    return "\n".join(centered)


def render_header(palette, version=APP_VERSION):
    logo = render_logo_gradient(palette)
    term_width = _terminal_width()
    title = palette.bold(palette.aqua_bright(APP_NAME.upper())) if hasattr(palette, 'aqua_bright') else palette.bold(palette.green(APP_NAME.upper()))
    tagline = palette.blue("Universal Metadata Sanitizer") if hasattr(palette, 'blue') else palette.gray("Universal Metadata Sanitizer")
    version_line = palette.aqua(f"v{version}") if hasattr(palette, 'aqua') else palette.green(f"v{version}")
    sep = palette.gray('/') if hasattr(palette, 'gray') else palette.green('/')
    header_line = f"{title} {sep} {tagline} {sep} {version_line}"
    centered_header = _center_line(header_line, term_width)
    return f"{logo}\n\n{centered_header}\n"


def render_section_header(palette, title, width=50):
    title_text = f" {title} "
    padding = max(0, width - len(title_text))
    left = "-" * (padding // 2)
    right = "-" * (padding - len(left))
    top = palette.cyan(f"+{left}{title_text}{right}+")
    bottom = palette.cyan(f"+{'-' * width}+")
    return f"{top}\n{bottom}"


def default_output_path(source, options):
    if options.output_path:
        return Path(options.output_path).expanduser()
    parent = source.parent
    stem, ext = source.stem, source.suffix
    candidate = parent / f"{stem}.{DEFAULT_OUTPUT_SUFFIX}{ext}"
    if not candidate.exists():
        return candidate
    idx = 2
    while True:
        candidate = parent / f"{stem}.{DEFAULT_OUTPUT_SUFFIX}-{idx}{ext}"
        if not candidate.exists():
            return candidate
        idx += 1


def snapshot_to_json(snapshot, detected):
    return {
        "file": {"path": str(detected.path), "format": detected.detected_format, "mime": detected.mime_type, "size": detected.size_bytes},
        "metadata": {"source": snapshot.source, "fields": snapshot.fields, "privacy_sensitive": snapshot.privacy_sensitive, "warning": snapshot.warning, "error": snapshot.error},
    }


def verify_output(detected_input, clean_result, before_snapshot, tools):
    class R:
        def __init__(self):
            self.output_exists = False
            self.output_readable = False
            self.output_non_empty = False
            self.format_preserved = False
            self.detected_output_format = "unknown"
            self.remaining_privacy_fields = []
            self.removed_privacy_fields = []
            self.warnings = []
            self.errors = []
        def as_dict(self):
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
    report = R()
    if not clean_result.output_path:
        report.errors.append("No output path")
        return report
    out = clean_result.output_path
    report.output_exists = out.exists()
    if not report.output_exists:
        report.errors.append("Output does not exist")
        return report
    try:
        with out.open("rb") as h: h.read(1)
        report.output_readable = True
    except OSError as e:
        report.errors.append(f"Not readable: {e}")
    try:
        report.output_non_empty = out.stat().st_size > 0
    except OSError as e:
        report.errors.append(f"Cannot stat: {e}")
    out_detected = detect_file(str(out))
    report.detected_output_format = out_detected.detected_format
    report.format_preserved = out_detected.detected_format == detected_input.detected_format
    after = inspect_metadata(out_detected, tools.get("exiftool"), tools.get("ffmpeg"))
    if not after.error:
        before_keys = set(before_snapshot.privacy_sensitive.keys())
        after_keys = set(after.privacy_sensitive.keys())
        report.removed_privacy_fields = sorted(before_keys - after_keys)
        report.remaining_privacy_fields = sorted(before_keys & after_keys)
    if report.remaining_privacy_fields:
        report.warnings.append("Some privacy-sensitive metadata remains.")
    return report


def build_parser():
    parser = argparse.ArgumentParser(prog="metaclean", description=f"{APP_NAME} - {APP_TAGLINE}")
    parser.add_argument("file", nargs="?", default=None, help="Path to the file to inspect/clean.")
    parser.add_argument("--scan", action="store_true", help="Only scan metadata.")
    parser.add_argument("--clean", action="store_true", help="Clean without interactive prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen.")
    parser.add_argument("--output", "-o", default=None, help="Explicit output file path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--no-color", action="store_true", help="Disable colors.")
    parser.add_argument("--no-animation", action="store_true", help="Disable animations.")
    parser.add_argument("--verbose", action="store_true", help="Show all metadata.")
    parser.add_argument("--debug", action="store_true", help="Show debug info.")
    parser.add_argument("--yes", "-y", action="store_true", help="Yes to all prompts.")
    parser.add_argument("--recursive", "-r", action="store_true", help="Directory preview.")
    parser.add_argument("--install-deps", action="store_true", help="Install missing deps.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{APP_VERSION}")
    return parser


def parse_args(argv=None):
    ns = build_parser().parse_args(argv)
    return ns, RuntimeOptions(
        no_color=ns.no_color, no_animation=ns.no_animation, verbose=ns.verbose,
        debug=ns.debug, dry_run=ns.dry_run, json_output=ns.json, yes=ns.yes,
        scan_only=ns.scan, clean_only=ns.clean, install_deps=ns.install_deps,
        output_path=ns.output, recursive=ns.recursive, input_path=ns.file,
    )


class FlowBar:
    def __init__(self, palette, enabled=True, stream=None, width=28):
        self.palette = palette
        self.enabled = enabled
        self.stream = stream or sys.stdout
        self.width = width
        self._thread = None
        self._stop = threading.Event()
        self._message = ""
        self._target = 100.0
        self._current = 0.0
        self._last_visible_len = 0

    def _gradient_color(self, t):
        if not self.palette.enabled:
            return ""
        t = max(0.0, min(1.0, float(t)))
        r = int(0 + (80 - 0) * t)
        g = int(180 + (255 - 180) * t)
        b = int(160 + (220 - 160) * t)
        return f"\x1b[38;2;{r};{g};{b}m"

    def _render_bar(self, pct):
        filled = int(self.width * pct / 100)
        if not self.palette.enabled:
            return "\u2588" * filled + "\u2591" * (self.width - filled)
        parts = []
        for i in range(self.width):
            if i < filled:
                t = i / max(self.width - 1, 1)
                color = self._gradient_color(t)
                parts.append(f"{color}\u2588")
            else:
                parts.append(f"{C_GRAY}\u2591")
        parts.append(RESET)
        return "".join(parts)

    def _animate(self):
        while not self._stop.is_set():
            if self._current < self._target:
                diff = self._target - self._current
                step = max(1.0, diff * 0.20)
                self._current = min(self._target, self._current + step)
            pct = self._current
            bar = self._render_bar(pct)
            if self.palette.enabled:
                pct_str = f"{C_AQUA_BRIGHT}{pct:5.1f}%{RESET}"
                msg = f"{C_BLUE_DIM}{self._message}{RESET}"
            else:
                pct_str = f"{pct:5.1f}%"
                msg = self._message
            line = f"\r  {msg} {bar} {pct_str}"
            stripped = __import__('re').sub(r'\x1b\[[0-9;]*m', '', line)
            self._last_visible_len = len(stripped)
            try:
                self.stream.write(line)
                self.stream.flush()
            except (OSError, ValueError):
                break
            time.sleep(0.06)
        try:
            clear_width = self._last_visible_len + 2
            self.stream.write("\r" + " " * clear_width + "\r")
            self.stream.flush()
        except (OSError, ValueError):
            pass

    def start(self, message, target=100.0):
        if not self.enabled:
            return
        self._message = message
        self._target = target
        self._current = 0.0
        self._stop.clear()
        self._last_visible_len = 0
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def update(self, target=None, message=None):
        if not self.enabled:
            return
        if target is not None:
            self._target = max(0.0, min(100.0, float(target)))
        if message is not None:
            self._message = message

    def complete(self, final_message=None):
        if not self.enabled:
            if final_message:
                try:
                    self.stream.write(final_message + "\n")
                    self.stream.flush()
                except (OSError, ValueError):
                    pass
            return
        self._target = 100.0
        self._current = 99.5
        time.sleep(0.08)
        self._current = 100.0
        time.sleep(0.04)
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.3)
        try:
            clear_width = self._last_visible_len + 2
            self.stream.write("\r" + " " * clear_width + "\r")
            self.stream.flush()
            if final_message:
                self.stream.write(final_message + "\n")
                self.stream.flush()
        except (OSError, ValueError):
            pass


class Spinner:
    def __init__(self, palette, enabled=True, stream=None):
        self.palette = palette
        self.enabled = enabled
        self.stream = stream or sys.stdout
        self._thread = None
        self._stop = threading.Event()
        self._message = ""
        self._last_visible_len = 0
    def _spin(self):
        idx = 0
        while not self._stop.is_set():
            frame = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
            if self.palette.enabled:
                line = f"\r  {C_AQUA}{frame}{RESET} {C_BLUE_DIM}{self._message}{RESET}"
            else:
                line = f"\r  {frame} {self._message}"
            stripped = __import__('re').sub(r'\x1b\[[0-9;]*m', '', line)
            self._last_visible_len = len(stripped)
            try:
                self.stream.write(line)
                self.stream.flush()
            except (OSError, ValueError):
                break
            idx += 1
            time.sleep(0.08)
        try:
            clear_width = self._last_visible_len + 2
            self.stream.write("\r" + " " * clear_width + "\r")
            self.stream.flush()
        except (OSError, ValueError):
            pass
    def start(self, message):
        if not self.enabled: return
        self._message = message
        self._stop.clear()
        self._last_visible_len = 0
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
    def stop(self, final=None, success=True):
        if not self.enabled:
            if final:
                try:
                    self.stream.write(final + "\n")
                    self.stream.flush()
                except (OSError, ValueError):
                    pass
            return
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        try:
            clear_width = self._last_visible_len + 2
            self.stream.write("\r" + " " * clear_width + "\r")
            self.stream.flush()
            if final:
                self.stream.write(final + "\n")
                self.stream.flush()
        except (OSError, ValueError):
            pass


def _format_bytes(num):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {u}" if u != "B" else f"{num} {u}"
        num /= 1024.0
    return f"{num:.1f} PB"


def main(argv=None):
    try:
        ns, options = parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 1
    palette = ColorPalette(enabled=should_enable_color(options.no_color))
    animation = (not options.no_animation) and (not is_ci_environment()) and sys.stderr.isatty()
    env = detect_environment()
    tools_list = check_all_tools(env)
    tools = {s.name: s for s in tools_list}
    if options.json_output:
        if not options.input_path:
            return 1
        detected = detect_file(options.input_path)
        if not detected.is_regular:
            sys.stdout.write(json.dumps({"error": detected.error}) + "\n")
            return 3
        snap = inspect_metadata(detected, tools.get("exiftool"), tools.get("ffmpeg"))
        sys.stdout.write(json.dumps(snapshot_to_json(snap, detected), default=str, indent=2) + "\n")
        return 0
    sys.stdout.write(render_header(palette))
    sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('env')}  {palette.aqua(env.platform_name)}  {palette.aqua(env.architecture)}  {palette.gray('py')} {palette.aqua(env.python_version)}\n")
    if env.package_managers:
        sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('pkg')}  {palette.aqua(env.package_managers[0])}\n")
    for s in tools_list:
        if s.functional:
            sys.stdout.write(f"  {palette.neon('+')} {palette.aqua_bright(s.name)}\n")
        else:
            sys.stdout.write(f"  {palette.red('x')} {palette.red(s.name)}\n")

    missing = [s for s in tools_list if not s.functional]
    if missing and env.package_managers and not options.json_output:
        pm = env.package_managers[0]
        sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('pkg')}  {palette.aqua(pm)}\n")
        sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('missing')}  {palette.aqua(', '.join(s.name for s in missing))}\n")
        should_install = options.yes or options.install_deps
        if not should_install:
            sys.stderr.write(f"  {palette.aqua('>')} {palette.blue('auto-install ' + str(len(missing)) + ' tool(s)?')} [Y/n] ")
            sys.stderr.flush()
            try:
                answer = sys.stdin.readline().strip().lower()
            except (KeyboardInterrupt, EOFError):
                answer = "n"
            should_install = not answer or answer[0] in ("y", "1", "t")
        if should_install:
            for s in missing:
                sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('install ' + s.name)}\n")
                sys.stdout.flush()
                cmd = get_install_command(s.name, env)
                if not cmd:
                    sys.stdout.write(f"  {palette.yellow('!')} no cmd for {s.name}\n")
                    continue
                try:
                    if "&&" in cmd or "||" in cmd:
                        result = subprocess.run(cmd, shell=True, stdin=sys.stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=600)
                    else:
                        result = subprocess.run(cmd.split(), stdin=sys.stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=600)
                    if result.returncode == 0:
                        new_status = recheck_tool(s.name)
                        tools[s.name] = new_status
                        if new_status.functional:
                            sys.stdout.write(f"  {palette.neon('+')} {palette.neon(s.name + ' ok')}\n")
                        else:
                            sys.stdout.write(f"  {palette.yellow('!')} {s.name} not functional\n")
                    else:
                        sys.stdout.write(f"  {palette.red('x')} {s.name} failed\n")
                except (subprocess.TimeoutExpired, OSError) as exc:
                    sys.stdout.write(f"  {palette.red('x')} {s.name} error\n")
            still_missing = [name for name, st in tools.items() if not st.functional]
            if still_missing:
                sys.stdout.write(f"  {palette.yellow('!')} missing  {', '.join(still_missing)}\n")
            else:
                sys.stdout.write(f"  {palette.neon('+')} all ok\n")
        else:
            sys.stdout.write(f"  {palette.yellow('!')} skipped\n")
    if not options.input_path:
        sys.stderr.write(f"  {palette.aqua('>')} {palette.blue('Enter the Path of the file')} : ")
        sys.stderr.flush()
        try:
            line = sys.stdin.readline().strip()
        except (KeyboardInterrupt, EOFError):
            return 130
        if not line:
            return 1
        options.input_path = line.strip().strip('"').strip("'")
    detected = detect_file(options.input_path)
    if not detected.is_regular:
        sys.stderr.write(f"  {palette.red('x')} {detected.error}\n")
        return 3
    sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('file')}  {palette.aqua(str(detected.path))}\n")
    sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('size')}  {palette.aqua(_format_bytes(detected.size_bytes))}  {palette.blue('type')}  {palette.aqua(detected.detected_format)}  {palette.blue('mime')}  {palette.aqua(detected.mime_type)}\n")
    if detected.magic_description:
        desc = detected.magic_description
        if len(desc) > 70:
            desc = desc[:67] + "..."
        sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('desc')}  {palette.aqua(desc)}\n")
    if not detected.extension_matches:
        sys.stdout.write(f"  {palette.yellow('!')} ext mismatch  {detected.extension or 'none'} != {detected.detected_format}\n")
    snap = inspect_metadata(detected, tools.get("exiftool"), tools.get("ffmpeg"))
    if snap.error:
        sys.stdout.write(f"  {palette.red('x')} {snap.error}\n")
    elif snap.warning:
        sys.stdout.write(f"  {palette.yellow('!')} {snap.warning}\n")
    if snap.privacy_sensitive:
        sys.stdout.write(f"  {palette.yellow('!')} {palette.yellow('privacy fields')}\n")
        for k in list(snap.privacy_sensitive.keys())[:8]:
            val = snap.privacy_sensitive[k][:45]
            sys.stdout.write(f"      {palette.aqua(k)}  {palette.yellow(val)}\n")
        sys.stdout.write("\n")
    for k, v in list(snap.fields.items())[:20]:
        display = v if len(v) <= 55 else v[:52] + "..."
        k_display = k if len(k) <= 36 else k[:33] + "..."
        sys.stdout.write(f"  {palette.blue(k_display):<38} {palette.aqua(display)}\n")
    if len(snap.fields) > 20:
        sys.stdout.write(f"  {palette.gray(f'+{len(snap.fields) - 20} more')}\n")
    decision = route(detected, tools, options)
    sys.stdout.write(f"  {palette.aqua('>')} {palette.blue('cleaner')}  {palette.aqua(decision.cleaner_name)}  {palette.blue('write')}  {palette.neon('yes') if decision.can_write else palette.yellow('no')}\n")
    if decision.missing_tools:
        sys.stdout.write(f"  {palette.yellow('!')} missing  {', '.join(decision.missing_tools)}\n")
    if options.scan_only:
        sys.stdout.write(f"  {palette.gray('-')} scan done  use --clean\n")
        return 0
    if not decision.can_write:
        sys.stdout.write(f"  {palette.red('x')} {decision.reason}\n")
        return 4
    if options.dry_run:
        sys.stdout.write(f"  {palette.aqua('>')} dry run  {decision.cleaner_name}\n")
        sys.stdout.write(f"  {palette.aqua('>')} out  {default_output_path(detected.path, options)}\n")
        sys.stdout.write(f"  {palette.gray('-')} no changes\n")
        return 0
    if not options.clean_only and not options.yes:
        sys.stderr.write(f"  {palette.aqua('>')} {palette.blue('Do you want to delete Metadata')} {palette.gray('(y/n)')} : ")
        sys.stderr.flush()
        try:
            answer = sys.stdin.readline().strip().lower()
        except (KeyboardInterrupt, EOFError):
            return 130
        if not answer or answer[0] not in ("y", "1", "t"):
            sys.stdout.write(f"  {palette.gray('-')} cancelled\n")
            return 0
    output_path = default_output_path(detected.path, options)
    cleaner = decision.cleaner_cls(tools, options)
    sys.stdout.write(f"  {palette.aqua('>')} {palette.aqua(cleaner.name + ' -> ' + output_path.name)}\n")
    sp = FlowBar(palette, enabled=animation)
    sp.start("cleaning", target=95.0)
    result = cleaner.clean(detected, output_path, snap)
    sp.complete(f"  {palette.neon('+')} {palette.neon('cleaning done')}")
    if not result.success:
        sys.stderr.write(f"  {palette.red('x')} {result.errors[0] if result.errors else 'error'}\n")
        return 5
    for w in result.warnings:
        sys.stdout.write(f"  {palette.yellow('!')} {w}\n")
    report = verify_output(detected, result, snap, tools)
    sp2 = FlowBar(palette, enabled=animation)
    sp2.start("verifying", target=95.0)
    import time as _time
    _time.sleep(0.3)
    sp2.complete(f"  {palette.neon('+')} {palette.neon('verify done')}")
    for k, v in report.as_dict().items():
        display_key = k.replace("_", " ")
        if isinstance(v, bool):
            if v:
                sys.stdout.write(f"  {palette.neon('+')} {palette.blue(display_key)}\n")
            else:
                sys.stdout.write(f"  {palette.red('x')} {palette.red(display_key)}\n")
        elif isinstance(v, list):
            if v:
                for item in v[:5]:
                    item_str = str(item).replace("_", " ")
                    if len(item_str) > 50:
                        item_str = item_str[:47] + "..."
                    sys.stdout.write(f"  {palette.yellow('!')} {palette.yellow(item_str)}\n")
                if len(v) > 5:
                    sys.stdout.write(f"  {palette.gray(f'+{len(v) - 5} more')}\n")
            else:
                sys.stdout.write(f"  {palette.neon('+')} {palette.blue(display_key)} {palette.gray('ok')}\n")
        else:
            val_str = str(v)
            if len(val_str) > 50:
                val_str = val_str[:47] + "..."
            sys.stdout.write(f"  {palette.blue(display_key)}  {palette.aqua(val_str)}\n")
    sys.stdout.write(f"\n  {palette.neon('+')} {palette.neon('done')}\n\n")
    sys.stdout.write(f"  {palette.blue('in')}   {detected.path}\n")
    sys.stdout.write(f"  {palette.neon('out')}  {result.output_path}\n\n")
    sys.stdout.write(f"  {palette.neon('+')} {palette.neon('original kept')}\n")
    if report.remaining_privacy_fields:
        sys.stdout.write(f"  {palette.yellow('!')} some metadata remains\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
