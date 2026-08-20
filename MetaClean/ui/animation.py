from __future__ import annotations

import sys
import time
import threading
import re

from .colors import ColorPalette, RESET, C_AQUA, C_AQUA_BRIGHT, C_BLUE_DIM, C_NEON, C_GRAY


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(text: str) -> int:
    stripped = _ANSI_RE.sub("", text)
    return len(stripped)


class FlowBar:
    def __init__(self, palette: ColorPalette, enabled: bool = True, stream=None, width: int = 28):
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

    def _gradient_color(self, t: float) -> str:
        if not self.palette.enabled:
            return ""
        t = max(0.0, min(1.0, float(t)))
        r = int(0 + (80 - 0) * t)
        g = int(180 + (255 - 180) * t)
        b = int(160 + (220 - 160) * t)
        return f"\x1b[38;2;{r};{g};{b}m"

    def _render_bar(self, pct: float) -> str:
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
            self._last_visible_len = _visible_len(line)
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

    def start(self, message: str, target: float = 100.0):
        if not self.enabled:
            return
        self._message = message
        self._target = target
        self._current = 0.0
        self._stop.clear()
        self._last_visible_len = 0
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def update(self, target: float = None, message: str = None):
        if not self.enabled:
            return
        if target is not None:
            self._target = max(0.0, min(100.0, float(target)))
        if message is not None:
            self._message = message

    def complete(self, final_message: str = None):
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
    def __init__(self, palette: ColorPalette, enabled: bool = True, stream=None):
        self.palette = palette
        self.enabled = enabled
        self.stream = stream or sys.stdout
        self._thread = None
        self._stop = threading.Event()
        self._message = ""
        self._frames = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
        self._last_visible_len = 0

    def _spin(self):
        idx = 0
        while not self._stop.is_set():
            frame = self._frames[idx % len(self._frames)]
            if self.palette.enabled:
                line = f"\r  {C_AQUA}{frame}{RESET} {C_BLUE_DIM}{self._message}{RESET}"
            else:
                line = f"\r  {frame} {self._message}"
            self._last_visible_len = _visible_len(line)
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

    def start(self, message: str):
        if not self.enabled:
            return
        self._message = message
        self._stop.clear()
        self._last_visible_len = 0
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, final_message: str | None = None, success: bool = True):
        if not self.enabled:
            if final_message:
                try:
                    self.stream.write(final_message + "\n")
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
            if final_message:
                self.stream.write(final_message + "\n")
                self.stream.flush()
        except (OSError, ValueError):
            pass


def render_progress_bar(palette: ColorPalette, percent: float, width: int = 24, label: str = "") -> str:
    clamped = max(0.0, min(100.0, float(percent)))
    filled = max(0, min(width, int(round(clamped / 100 * width))))
    bar_full = palette.green("\u2588" * filled)
    bar_empty = palette.gray("\u2591" * (width - filled))
    pct_text = f"{int(clamped):3d}%"
    label_text = f"{label} " if label else ""
    return f"{label_text}{bar_full}{bar_empty} {pct_text}"
