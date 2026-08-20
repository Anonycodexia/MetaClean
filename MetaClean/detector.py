from __future__ import annotations

import os
import struct
import subprocess
from pathlib import Path

from .config import DetectedFile


MAX_SIGNATURE_SIZE = 64
MAX_MAGIC_PROBE_BYTES = 1024 * 1024


SIGNATURE_TABLE: list[tuple[bytes, str, str]] = [
    (b"\xff\xd8\xff", "jpeg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"GIF87a", "gif", "image/gif"),
    (b"GIF89a", "gif", "image/gif"),
    (b"BM", "bmp", "image/bmp"),
    (b"II*\x00", "tiff", "image/tiff"),
    (b"MM\x00*", "tiff", "image/tiff"),
    (b"RIFF", "riff", "application/octet-stream"),
    (b"WEBP", "webp", "image/webp"),
    (b"\x1a\x45\xdf\xa3", "matroska", "video/x-matroska"),
    (b"\x00\x00\x01\x00", "ico", "image/x-icon"),
    (b"\x00\x00\x02\x00", "cur", "image/x-icon"),
    (b"PK\x03\x04", "zip", "application/zip"),
    (b"PK\x05\x06", "zip", "application/zip"),
    (b"PK\x07\x08", "zip", "application/zip"),
    (b"%PDF", "pdf", "application/pdf"),
    (b"OggS", "ogg", "audio/ogg"),
    (b"ID3", "mp3", "audio/mpeg"),
    (b"\xff\xfb", "mp3", "audio/mpeg"),
    (b"\xff\xf3", "mp3", "audio/mpeg"),
    (b"\xff\xfa", "mp3", "audio/mpeg"),
    (b"fLaC", "flac", "audio/flac"),
    (b"FORM", "iff", "application/octet-stream"),
    (b".snd", "au", "audio/basic"),
    (b"RIFF", "wave", "audio/wav"),
    (b"ftyp", "mp4_family", "video/mp4"),
    (b"\x00\x00\x00", "mp4_family", "video/mp4"),
    (b"FLV", "flv", "video/x-flv"),
    (b"\x1a\x45\xdf\xa3", "webm", "video/webm"),
]


EXTENSION_TO_FORMAT: dict[str, str] = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".jpe": "jpeg",
    ".jfif": "jpeg",
    ".png": "png",
    ".gif": "gif",
    ".bmp": "bmp",
    ".tiff": "tiff",
    ".tif": "tiff",
    ".webp": "webp",
    ".heic": "heic",
    ".heif": "heif",
    ".hif": "heic",
    ".avif": "avif",
    ".cr2": "cr2",
    ".cr3": "cr3",
    ".nef": "nef",
    ".arw": "arw",
    ".dng": "dng",
    ".raf": "raf",
    ".rw2": "rw2",
    ".orf": "orf",
    ".psd": "psd",
    ".mp4": "mp4",
    ".m4v": "m4v",
    ".mov": "mov",
    ".mkv": "matroska",
    ".avi": "avi",
    ".webm": "webm",
    ".3gp": "3gp",
    ".3g2": "3g2",
    ".mts": "mts",
    ".m2ts": "mts",
    ".flv": "flv",
    ".wmv": "wmv",
    ".mp3": "mp3",
    ".flac": "flac",
    ".wav": "wave",
    ".aac": "aac",
    ".m4a": "m4a",
    ".ogg": "ogg",
    ".opus": "opus",
    ".wma": "wma",
    ".aiff": "aiff",
    ".aif": "aiff",
    ".pdf": "pdf",
    ".py": "python_source",
    ".js": "javascript_source",
    ".ts": "typescript_source",
    ".java": "java_source",
    ".c": "c_source",
    ".cpp": "cpp_source",
    ".cc": "cpp_source",
    ".cxx": "cpp_source",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".rs": "rust_source",
    ".go": "go_source",
    ".rb": "ruby_source",
    ".sh": "shell_source",
    ".bash": "shell_source",
    ".zsh": "shell_source",
    ".ps1": "powershell_source",
    ".bat": "batch_source",
    ".cmd": "batch_source",
    ".txt": "plain_text",
    ".md": "markdown",
    ".rst": "rst_text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".csv": "csv",
    ".tsv": "tsv",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".log": "log_text",
}


SOURCE_FORMATS = {
    "python_source",
    "javascript_source",
    "typescript_source",
    "java_source",
    "c_source",
    "cpp_source",
    "c_header",
    "cpp_header",
    "rust_source",
    "go_source",
    "ruby_source",
    "shell_source",
    "powershell_source",
    "batch_source",
    "plain_text",
    "markdown",
    "rst_text",
    "json",
    "yaml",
    "xml",
    "html",
    "css",
    "scss",
    "csv",
    "tsv",
    "toml",
    "ini",
    "log_text",
}


EXTENSION_BY_FORMAT: dict[str, str] = {
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "bmp": ".bmp",
    "tiff": ".tiff",
    "webp": ".webp",
    "heic": ".heic",
    "heif": ".heif",
    "avif": ".avif",
    "cr2": ".cr2",
    "cr3": ".cr3",
    "nef": ".nef",
    "arw": ".arw",
    "dng": ".dng",
    "raf": ".raf",
    "rw2": ".rw2",
    "orf": ".orf",
    "psd": ".psd",
    "mp4": ".mp4",
    "m4v": ".m4v",
    "mov": ".mov",
    "matroska": ".mkv",
    "avi": ".avi",
    "webm": ".webm",
    "3gp": ".3gp",
    "3g2": ".3g2",
    "mts": ".mts",
    "flv": ".flv",
    "wmv": ".wmv",
    "mp3": ".mp3",
    "flac": ".flac",
    "wave": ".wav",
    "aac": ".aac",
    "m4a": ".m4a",
    "ogg": ".ogg",
    "opus": ".opus",
    "wma": ".wma",
    "aiff": ".aiff",
    "pdf": ".pdf",
}


def read_signature(path: Path, length: int = MAX_SIGNATURE_SIZE) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(length)
    except OSError:
        return b""


def detect_signature_format(path: Path) -> tuple[str, str]:
    head = read_signature(path)
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
        fourcc = head[8:12]
        if fourcc == b"WEBP":
            return "webp", "image/webp"
        if fourcc == b"WAVE":
            return "wave", "audio/wav"
        if fourcc == b"AVI ":
            return "avi", "video/x-msvideo"
        return "riff", "application/octet-stream"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        sub = head[4:8] if len(head) >= 8 else b""
        if sub.startswith(b"B2"):
            return "webm", "video/webm"
        return "matroska", "video/x-matroska"
    if head.startswith(b"\x00\x00\x00") and len(head) >= 12 and head[4:8] == b"ftyp":
        return "mp4_family", "video/mp4"
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06") or head.startswith(b"PK\x07\x08"):
        if _is_zip_heic(head):
            return "heic", "image/heic"
        return "zip", "application/zip"
    if head.startswith(b"%PDF"):
        return "pdf", "application/pdf"
    if head.startswith(b"OggS"):
        if len(head) >= 37 and head[28:36] == b"OpusHead":
            return "opus", "audio/ogg"
        return "ogg", "audio/ogg"
    if head.startswith(b"ID3") or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xfa"):
        return "mp3", "audio/mpeg"
    if head.startswith(b"fLaC"):
        return "flac", "audio/flac"
    if head.startswith(b"FORM") and len(head) >= 12:
        sub = head[8:12]
        if sub == b"AIFF":
            return "aiff", "audio/aiff"
        if sub == b"AIFC":
            return "aiff", "audio/aiff"
        return "iff", "application/octet-stream"
    if head.startswith(b"\x00\x00\x01\x00"):
        return "ico", "image/x-icon"
    if head.startswith(b"FLV"):
        return "flv", "video/x-flv"
    if head.startswith(b"\x30\x26\xb2\x75"):
        return "wmv", "video/x-ms-wmv"
    if head.startswith(b".snd"):
        return "au", "audio/basic"
    if _looks_like_text(head):
        return "text", "text/plain"
    return "binary", "application/octet-stream"


def _is_zip_heic(head: bytes) -> bool:
    if not head.startswith(b"PK\x03\x04"):
        return False
    if len(head) < 16:
        return False
    try:
        offset = 30 + struct.unpack("<H", head[26:28])[0] + struct.unpack("<H", head[28:30])[0]
        return head[offset:offset + 4] == b"ftyp" and head[offset + 4:offset + 8] in (b"heic", b"heix", b"mif1", b"heim", b"heis", b"hevc", b"hevx")
    except struct.error:
        return False


def _looks_like_text(head: bytes) -> bool:
    if not head:
        return False
    text_chars = set(range(9, 14)) | set(range(32, 127)) | {0}
    non_text_count = sum(1 for byte in head if byte not in text_chars)
    return non_text_count / max(len(head), 1) < 0.10


def probe_magic(path: Path) -> tuple[str, str]:
    try:
        import magic
        if hasattr(magic, "Magic"):
            instance = magic.Magic(mime=True)
            mime = instance.from_file(str(path))
            description = instance.from_file(str(path))
            return mime, description
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["file", "-b", "--mime-type", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        mime = result.stdout.strip() if result.returncode == 0 else "application/octet-stream"
        result_desc = subprocess.run(
            ["file", "-b", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        description = result_desc.stdout.strip() if result_desc.returncode == 0 else ""
        return mime, description
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "application/octet-stream", ""


def detect_format_from_mime(mime: str) -> str:
    if not mime:
        return "unknown"
    mime_lower = mime.lower()
    mapping = {
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/tiff": "tiff",
        "image/webp": "webp",
        "image/heic": "heic",
        "image/heif": "heic",
        "image/avif": "avif",
        "image/x-canon-cr2": "cr2",
        "image/x-canon-cr3": "cr3",
        "image/x-nikon-nef": "nef",
        "image/x-sony-arw": "arw",
        "image/x-adobe-dng": "dng",
        "image/x-fuji-raf": "raf",
        "image/x-panasonic-rw2": "rw2",
        "image/x-olympus-orf": "orf",
        "image/vnd.adobe.photoshop": "psd",
        "image/x-icon": "ico",
        "video/mp4": "mp4",
        "video/quicktime": "mov",
        "video/x-m4v": "m4v",
        "video/x-matroska": "matroska",
        "video/webm": "webm",
        "video/x-msvideo": "avi",
        "video/3gpp": "3gp",
        "video/3gpp2": "3g2",
        "video/mp2t": "mts",
        "video/x-flv": "flv",
        "video/x-ms-wmv": "wmv",
        "audio/mpeg": "mp3",
        "audio/flac": "flac",
        "audio/wav": "wave",
        "audio/x-wav": "wave",
        "audio/aac": "aac",
        "audio/mp4": "m4a",
        "audio/x-m4a": "m4a",
        "audio/ogg": "ogg",
        "audio/opus": "opus",
        "audio/x-ms-wma": "wma",
        "audio/aiff": "aiff",
        "audio/x-aiff": "aiff",
        "application/pdf": "pdf",
        "text/plain": "text",
        "text/html": "html",
        "text/css": "css",
        "application/json": "json",
        "application/xml": "xml",
        "text/xml": "xml",
        "application/yaml": "yaml",
        "text/yaml": "yaml",
        "application/zip": "zip",
    }
    if mime_lower in mapping:
        return mapping[mime_lower]
    if mime_lower.startswith("text/"):
        return "text"
    return "unknown"


def detect_format_from_extension(extension: str) -> str:
    if not extension:
        return "unknown"
    return EXTENSION_TO_FORMAT.get(extension.lower(), "unknown")


def is_text_source_format(fmt: str) -> bool:
    return fmt in SOURCE_FORMATS or fmt in {"text"}


def is_supported_format(fmt: str) -> bool:
    if fmt in SOURCE_FORMATS:
        return False
    return fmt in EXTENSION_BY_FORMAT or fmt in {"mp4_family"}


def detect_file(path_str: str) -> DetectedFile:
    raw_path = Path(path_str).expanduser()
    path = raw_path.resolve(strict=False) if raw_path.exists() else raw_path
    detected = DetectedFile(
        path=raw_path,
        exists=raw_path.exists(),
        is_regular=False,
        is_symlink=raw_path.is_symlink(),
        size_bytes=0,
        extension=raw_path.suffix.lower(),
        mime_type="application/octet-stream",
        mime_short="binary",
        magic_description="",
        signature_format="unknown",
        detected_format="unknown",
        extension_matches=True,
        readable=False,
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
        stat = raw_path.stat()
        detected.size_bytes = stat.st_size
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
    if magic_mime and magic_mime != "application/octet-stream":
        detected.mime_type = magic_mime
    else:
        detected.mime_type = sig_mime
    detected.mime_short = detected.mime_type.split("/", 1)[-1] if "/" in detected.mime_type else detected.mime_type
    detected.magic_description = magic_desc
    ext_format = detect_format_from_extension(detected.extension)
    mime_format = detect_format_from_mime(detected.mime_type)
    candidates = [mime_format, sig_format, ext_format]
    for candidate in candidates:
        if candidate and candidate != "unknown":
            detected.detected_format = _normalize_format(candidate, sig_format)
            break
    if detected.detected_format == "mp4_family":
        detected.detected_format = "mp4"
    if detected.detected_format == "text" and ext_format != "unknown" and ext_format != "text":
        detected.detected_format = ext_format
    if detected.detected_format == "unknown" and ext_format != "unknown":
        detected.detected_format = ext_format
    ext_check_target = detected.detected_format
    if ext_format != "unknown" and ext_format != ext_check_target:
        if ext_format in SOURCE_FORMATS and ext_check_target == "text":
            detected.extension_matches = True
        elif ext_format == ext_check_target:
            detected.extension_matches = True
        elif ext_check_target == "mp4" and ext_format in {"mp4", "m4v"}:
            detected.extension_matches = True
        elif ext_check_target == "matroska" and ext_format == "matroska":
            detected.extension_matches = True
        else:
            detected.extension_matches = False
    elif ext_format == "unknown" and detected.extension:
        detected.extension_matches = False
    else:
        detected.extension_matches = True
    return detected


def _normalize_format(candidate: str, sig_format: str) -> str:
    if candidate == "riff" and sig_format in {"webp", "wave", "avi"}:
        return sig_format
    if candidate in {"mp4_family"}:
        return "mp4"
    return candidate
