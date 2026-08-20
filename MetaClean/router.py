from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cleaners import CleanerBase, CLEANER_REGISTRY, select_cleaner, UnsupportedCleaner
from .config import DetectedFile, RuntimeOptions, ToolStatus


@dataclass
class RoutingDecision:
    detected_format: str
    cleaner_cls: type[CleanerBase]
    cleaner_name: str
    can_write: bool
    required_tools_present: bool
    missing_tools: list[str]
    reason: str
    warnings: list[str]


def _find_missing_tools_for_format(fmt: str, tools: dict[str, ToolStatus]) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for cleaner_cls in CLEANER_REGISTRY:
        if cleaner_cls is UnsupportedCleaner:
            continue
        if not cleaner_cls.supports(fmt):
            continue
        for required in cleaner_cls.required_tools:
            if required in seen:
                continue
            seen.add(required)
            tool = tools.get(required)
            if not tool or not tool.functional:
                missing.append(required)
    return missing


def route(detected: DetectedFile, tools: dict[str, ToolStatus], options: RuntimeOptions) -> RoutingDecision:
    fmt = detected.detected_format
    warnings: list[str] = []
    if not detected.extension_matches:
        warnings.append(f"Extension '{detected.extension or '(none)'}' disagrees with detected format '{fmt}'.")
    cleaner_cls = select_cleaner(fmt, tools)
    if cleaner_cls is None:
        missing = _find_missing_tools_for_format(fmt, tools)
        if _is_text_source(fmt):
            return RoutingDecision(
                detected_format=fmt,
                cleaner_cls=UnsupportedCleaner,
                cleaner_name="Unsupported",
                can_write=False,
                required_tools_present=True,
                missing_tools=[],
                reason="Text and source files do not carry embedded metadata requiring cleaning.",
                warnings=warnings,
            )
        if missing:
            return RoutingDecision(
                detected_format=fmt,
                cleaner_cls=UnsupportedCleaner,
                cleaner_name="Unsupported",
                can_write=False,
                required_tools_present=False,
                missing_tools=missing,
                reason=f"Cleaner for '{fmt}' requires missing tools: {', '.join(missing)}",
                warnings=warnings,
            )
        return RoutingDecision(
            detected_format=fmt,
            cleaner_cls=UnsupportedCleaner,
            cleaner_name="Unsupported",
            can_write=False,
            required_tools_present=False,
            missing_tools=[],
            reason=f"No registered cleaner supports format '{fmt}'.",
            warnings=warnings,
        )
    can_write = cleaner_cls.can_write(fmt)
    missing = []
    for required in cleaner_cls.required_tools:
        tool = tools.get(required)
        if not tool or not tool.functional:
            missing.append(required)
    required_present = not missing
    if not required_present:
        return RoutingDecision(
            detected_format=fmt,
            cleaner_cls=UnsupportedCleaner,
            cleaner_name="Unsupported",
            can_write=False,
            required_tools_present=False,
            missing_tools=missing,
            reason=f"Cleaner '{cleaner_cls.name}' requires missing tools: {', '.join(missing)}",
            warnings=warnings,
        )
    if not can_write:
        return RoutingDecision(
            detected_format=fmt,
            cleaner_cls=UnsupportedCleaner,
            cleaner_name="Unsupported",
            can_write=False,
            required_tools_present=True,
            missing_tools=[],
            reason=f"Cleaner '{cleaner_cls.name}' cannot write format '{fmt}' safely.",
            warnings=warnings,
        )
    return RoutingDecision(
        detected_format=fmt,
        cleaner_cls=cleaner_cls,
        cleaner_name=cleaner_cls.name,
        can_write=True,
        required_tools_present=True,
        missing_tools=[],
        reason=f"Cleaner '{cleaner_cls.name}' selected for format '{fmt}'.",
        warnings=warnings,
    )


def _is_text_source(fmt: str) -> bool:
    return fmt in {
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
        "text",
    }
