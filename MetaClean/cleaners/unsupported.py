from __future__ import annotations

from pathlib import Path

from ..config import DetectedFile, RuntimeOptions, ToolStatus
from ..metadata import MetadataSnapshot
from .base import CleanerBase, CleanResult


class UnsupportedCleaner(CleanerBase):
    name = "Unsupported"
    supported_formats = ()
    can_write_formats = ()
    required_tools = ()

    @classmethod
    def supports(cls, detected_format: str) -> bool:
        return False

    @classmethod
    def is_available(cls, tools: dict[str, ToolStatus]) -> bool:
        return True

    def clean(self, detected: DetectedFile, output_path: Path, before_snapshot: MetadataSnapshot) -> CleanResult:
        result = CleanResult(cleaner_name=self.name, method="none")
        result.errors.append(f"Format '{detected.detected_format}' is not supported for embedded-metadata cleaning.")
        result.warnings.append("For text/source files, only filesystem metadata exists; no embedded metadata to clean.")
        result.warnings.append("For unsupported binary formats, do not trust generic metadata commands.")
        return result

    def describe_action(self, detected: DetectedFile, output_path: Path) -> str:
        return f"No embedded metadata cleaning available for {detected.detected_format}"
