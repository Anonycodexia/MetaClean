from ..config import ToolStatus
from .base import CleanerBase, CleanResult
from .exiftool import ExifToolCleaner
from .ffmpeg import FFmpegCleaner
from .qpdf import QpdfCleaner
from .unsupported import UnsupportedCleaner


CLEANER_REGISTRY: list[type[CleanerBase]] = [
    ExifToolCleaner,
    QpdfCleaner,
    FFmpegCleaner,
    UnsupportedCleaner,
]


def available_cleaners(detected_format: str, tools: dict[str, ToolStatus]) -> list[type[CleanerBase]]:
    matches: list[type[CleanerBase]] = []
    for cleaner_cls in CLEANER_REGISTRY:
        if cleaner_cls.supports(detected_format) and cleaner_cls.is_available(tools):
            matches.append(cleaner_cls)
    return matches


def select_cleaner(detected_format: str, tools: dict[str, ToolStatus]) -> type[CleanerBase] | None:
    matches = available_cleaners(detected_format, tools)
    if not matches:
        return None
    if UnsupportedCleaner in matches and len(matches) > 1:
        matches = [m for m in matches if m is not UnsupportedCleaner]
    return matches[0]


def register_cleaner(cleaner_cls: type[CleanerBase]) -> None:
    if cleaner_cls not in CLEANER_REGISTRY:
        CLEANER_REGISTRY.insert(-1, cleaner_cls)


__all__ = [
    "CleanerBase",
    "CleanResult",
    "ExifToolCleaner",
    "FFmpegCleaner",
    "QpdfCleaner",
    "UnsupportedCleaner",
    "CLEANER_REGISTRY",
    "available_cleaners",
    "select_cleaner",
    "register_cleaner",
]
