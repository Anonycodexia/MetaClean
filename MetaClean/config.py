from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


APP_NAME = "MetaClean"
APP_TAGLINE = "Universal Metadata Inspection & Sanitization"
APP_VERSION = "1.0.0"

DEFAULT_OUTPUT_SUFFIX = "cleaned"
DEFAULT_OUTPUT_PATTERN = "{stem}.{suffix}{ext}"
DEFAULT_OUTPUT_PATTERN_INDEXED = "{stem}.{suffix}-{index}{ext}"

SECTION_BORDER_TOP = "\u256d\u2500" * 24 + "\u256e"
SECTION_BORDER_BOTTOM = "\u2570\u2500" * 24 + "\u256f"
SECTION_BORDER_LINE = "\u2500" * 48

SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
PROGRESS_BLOCK_FULL = "\u2588"
PROGRESS_BLOCK_EMPTY = "\u2591"
PROGRESS_WIDTH = 24

MAX_METADATA_PREVIEW_FIELDS = 20

PRIVACY_SENSITIVE_KEYS = (
    "gps",
    "gpslatitude",
    "gpslongitude",
    "gpsaltituderef",
    "gpsposition",
    "make",
    "model",
    "serialnumber",
    "cameraserialnumber",
    "ownername",
    "artist",
    "author",
    "creator",
    "software",
    "encoder",
    "comment",
    "description",
    "datetimeoriginal",
    "createdate",
    "modifydate",
    "itunes",
    "composer",
    "copyright",
    "xmp",
    "iptc",
    "exif",
    "icc_profile",
    "thumbnailimage",
    "previewimage",
    "author",
    "title",
    "subject",
    "keywords",
    "producer",
    "creator_tool",
)


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


def default_output_path(source: Path, options: RuntimeOptions) -> Path:
    if options.output_path:
        return Path(options.output_path).expanduser()
    parent = source.parent
    stem = source.stem
    ext = source.suffix
    candidate = parent / DEFAULT_OUTPUT_PATTERN.format(stem=stem, suffix=DEFAULT_OUTPUT_SUFFIX, ext=ext)
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = parent / DEFAULT_OUTPUT_PATTERN_INDEXED.format(
            stem=stem, suffix=DEFAULT_OUTPUT_SUFFIX, index=index, ext=ext
        )
        if not candidate.exists():
            return candidate
        index += 1


def is_ci_environment() -> bool:
    ci_indicators = (
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "CIRCLECI",
        "TRAVIS",
        "BUILD_NUMBER",
        "TERMUX_NO_ANIMATION",
    )
    return any(os.environ.get(name) for name in ci_indicators)
