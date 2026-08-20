from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import DetectedFile, RuntimeOptions, ToolStatus
from ..metadata import MetadataSnapshot


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


class CleanerBase(ABC):
    name: str = "Base"
    supported_formats: tuple[str, ...] = ()
    required_tools: tuple[str, ...] = ()
    can_write_formats: tuple[str, ...] = ()

    def __init__(self, tools: dict[str, ToolStatus], options: RuntimeOptions):
        self.tools = tools
        self.options = options

    @classmethod
    def supports(cls, detected_format: str) -> bool:
        return detected_format in cls.supported_formats

    @classmethod
    def can_write(cls, detected_format: str) -> bool:
        if not cls.can_write_formats:
            return detected_format in cls.supported_formats
        return detected_format in cls.can_write_formats

    @classmethod
    def is_available(cls, tools: dict[str, ToolStatus]) -> bool:
        for required in cls.required_tools:
            tool = tools.get(required)
            if not tool or not tool.functional:
                return False
        return True

    @abstractmethod
    def clean(self, detected: DetectedFile, output_path: Path, before_snapshot: MetadataSnapshot) -> CleanResult:
        raise NotImplementedError

    def required_tools_missing(self) -> list[str]:
        missing: list[str] = []
        for required in self.required_tools:
            tool = self.tools.get(required)
            if not tool or not tool.functional:
                missing.append(required)
        return missing

    def describe_action(self, detected: DetectedFile, output_path: Path) -> str:
        return f"{self.name} -> {output_path.name}"
