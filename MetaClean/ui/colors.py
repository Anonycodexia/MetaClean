from __future__ import annotations

import os
import sys


RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"


C_AQUA = "\x1b[38;2;0;255;200m"
C_AQUA_BRIGHT = "\x1b[38;2;80;255;220m"
C_AQUA_DIM = "\x1b[38;2;0;180;160m"
C_BLUE = "\x1b[38;2;80;160;255m"
C_BLUE_BRIGHT = "\x1b[38;2;120;200;255m"
C_BLUE_DIM = "\x1b[38;2;40;100;180m"
C_NEON = "\x1b[38;2;0;255;180m"
C_NEON_BRIGHT = "\x1b[38;2;100;255;200m"
C_GREEN = "\x1b[38;2;0;255;100m"
C_YELLOW = "\x1b[38;2;255;220;80m"
C_RED = "\x1b[38;2;255;80;100m"
C_GRAY = "\x1b[38;2;120;140;160m"
C_WHITE = "\x1b[38;2;220;230;240m"


class ColorPalette:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{code}{text}{RESET}"

    def aqua(self, text: str) -> str:
        return self._wrap(C_AQUA, text)

    def aqua_bright(self, text: str) -> str:
        return self._wrap(C_AQUA_BRIGHT, text)

    def aqua_dim(self, text: str) -> str:
        return self._wrap(C_AQUA_DIM, text)

    def blue(self, text: str) -> str:
        return self._wrap(C_BLUE, text)

    def blue_bright(self, text: str) -> str:
        return self._wrap(C_BLUE_BRIGHT, text)

    def blue_dim(self, text: str) -> str:
        return self._wrap(C_BLUE_DIM, text)

    def neon(self, text: str) -> str:
        return self._wrap(C_NEON, text)

    def neon_bright(self, text: str) -> str:
        return self._wrap(C_NEON_BRIGHT, text)

    def green(self, text: str) -> str:
        return self._wrap(C_GREEN, text)

    def yellow(self, text: str) -> str:
        return self._wrap(C_YELLOW, text)

    def red(self, text: str) -> str:
        return self._wrap(C_RED, text)

    def gray(self, text: str) -> str:
        return self._wrap(C_GRAY, text)

    def white(self, text: str) -> str:
        return self._wrap(C_WHITE, text)

    def bold(self, text: str) -> str:
        return self._wrap(BOLD, text)

    def dim(self, text: str) -> str:
        return self._wrap(DIM, text)

    def label(self, text: str) -> str:
        return self._wrap(C_BLUE_DIM, text)

    def value(self, text: str) -> str:
        return self._wrap(C_AQUA, text)

    def success(self, text: str) -> str:
        return self._wrap(C_NEON, text)

    def warning(self, text: str) -> str:
        return self._wrap(C_YELLOW, text)

    def danger(self, text: str) -> str:
        return self._wrap(C_RED, text)


def should_enable_color(no_color_flag: bool) -> bool:
    if no_color_flag:
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CLICOLOR_FORCE") and os.environ.get("CLICOLOR_FORCE") != "0":
        return True
    if os.environ.get("CLICOLOR") == "0":
        return False
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    if term in ("dumb",):
        return False
    return True


def should_enable_animation(no_animation_flag: bool) -> bool:
    if no_animation_flag:
        return False
    if os.environ.get("METACLEAN_NO_ANIMATION"):
        return False
    if os.environ.get("CLICOLOR_FORCE") and os.environ.get("CLICOLOR_FORCE") != "0":
        pass
    elif not sys.stdout.isatty():
        return False
    if os.environ.get("CI") or os.environ.get("CONTINUOUS_INTEGRATION"):
        return False
    term = os.environ.get("TERM", "")
    if term in ("dumb",):
        return False
    return True
