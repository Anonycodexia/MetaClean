from __future__ import annotations

import os
import re
import shutil

from .colors import ColorPalette, RESET
from ..config import APP_NAME, APP_TAGLINE, APP_VERSION


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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


def _terminal_width() -> int:
    try:
        return shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        return 80


def _logo_max_width() -> int:
    return max(_visible_len(line) for line in LOGO_LINES)


def _center_line(text: str, target_width: int) -> str:
    visible = _visible_len(text)
    if visible >= target_width:
        return text
    padding = (target_width - visible) // 2
    return " " * padding + text


def _gradient_color(t: float, enabled: bool) -> str:
    if not enabled:
        return ""
    t = max(0.0, min(1.0, t))
    r = int(0 + (80 - 0) * t)
    g = int(180 + (255 - 180) * t)
    b = int(160 + (220 - 160) * t)
    return f"\x1b[38;2;{r};{g};{b}m"


def _colorize_line_gradient(line: str, index: int, total: int, enabled: bool, bold: bool = False) -> str:
    if not enabled:
        return line
    if not line:
        return line
    t = index / max(total - 1, 1)
    color = _gradient_color(t, enabled)
    prefix = "\x1b[1m" if bold else ""
    return f"{prefix}{color}{line}{RESET}"


def render_logo(palette: ColorPalette) -> str:
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


def render_logo_solid(palette: ColorPalette) -> str:
    return "\n".join(palette.green(line) for line in LOGO_LINES)


def render_header(palette: ColorPalette, version: str = APP_VERSION) -> str:
    logo = render_logo(palette)
    term_width = _terminal_width()
    title = palette.bold(palette.aqua_bright(APP_NAME.upper()))
    tagline = palette.blue("Universal Metadata Sanitizer")
    version_line = palette.aqua(f"v{version}")
    sep = palette.gray("/")
    header_line = f"{title} {sep} {tagline} {sep} {version_line}"
    centered_header = _center_line(header_line, term_width)
    return f"{logo}\n\n{centered_header}\n"


def render_section_header(palette: ColorPalette, title: str, width: int = 50) -> str:
    return ""


def render_separator(palette: ColorPalette, width: int = 50, char: str = "\u2500") -> str:
    return ""


def render_divider(palette: ColorPalette, width: int = 50) -> str:
    return ""
