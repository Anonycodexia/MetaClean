from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import EnvironmentInfo, ToolStatus
from .platform import detect_termux


REQUIRED_TOOLS: list[dict[str, str | list[str]]] = [
    {
        "name": "exiftool",
        "executables": ["exiftool"],
        "version_args": ["-ver"],
        "version_pattern": r"^\d+\.\d+",
    },
    {
        "name": "ffmpeg",
        "executables": ["ffmpeg"],
        "version_args": ["-version"],
        "version_pattern": r"ffmpeg version",
    },
    {
        "name": "qpdf",
        "executables": ["qpdf"],
        "version_args": ["--version"],
        "version_pattern": r"qpdf version",
    },
]


@dataclass
class DependencyResult:
    tools: list[ToolStatus] = field(default_factory=list)
    all_available: bool = False
    install_offered: dict[str, bool] = field(default_factory=dict)


def find_executable(name: str) -> str | None:
    return shutil.which(name)


def run_version_command(executable: str, args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and output:
            return True, output
        return False, output or f"Exit code {result.returncode}"
    except FileNotFoundError:
        return False, "Executable not found"
    except subprocess.TimeoutExpired:
        return False, "Version check timed out"
    except OSError as exc:
        return False, str(exc)


def parse_version_line(raw: str) -> str:
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        return line
    return raw.strip()


def verify_tool_functional(executable: str, name: str) -> tuple[bool, str | None]:
    if name == "exiftool":
        ok, output = run_version_command(executable, ["-ver"])
        if ok and any(ch.isdigit() for ch in output):
            return True, parse_version_line(output)
        return False, output
    if name == "ffmpeg":
        ok, output = run_version_command(executable, ["-version"])
        if ok and "ffmpeg version" in output.lower():
            return True, output.splitlines()[0]
        return False, output
    if name == "qpdf":
        ok, output = run_version_command(executable, ["--version"])
        if ok and "qpdf version" in output.lower():
            return True, output.splitlines()[0]
        return False, output
    return False, "Unknown tool"


def get_install_commands(name: str, env: EnvironmentInfo) -> list[str]:
    commands: list[str] = []
    primary = get_install_command(name, env)
    if primary:
        commands.append(primary)
    return commands


def get_install_command(name: str, env: EnvironmentInfo) -> str | None:
    if not env.package_managers:
        return None
    pm = env.package_managers[0]
    if env.is_termux:
        if name == "exiftool":
            return "pkg install -y perl && cpan -f -i Image::ExifTool"
        if name == "ffmpeg":
            return "pkg install -y ffmpeg"
        if name == "qpdf":
            return "pkg install -y qpdf"
    if pm == "apt" or pm == "apt-get":
        if name == "exiftool":
            return f"sudo -n {pm} install -y libimage-exiftool-perl 2>/dev/null || sudo {pm} install -y libimage-exiftool-perl || {pm} install -y libimage-exiftool-perl"
        if name == "ffmpeg":
            return f"sudo -n {pm} install -y ffmpeg 2>/dev/null || sudo {pm} install -y ffmpeg || {pm} install -y ffmpeg"
        if name == "qpdf":
            return f"sudo -n {pm} install -y qpdf 2>/dev/null || sudo {pm} install -y qpdf || {pm} install -y qpdf"
    if pm == "dnf" or pm == "yum":
        if name == "exiftool":
            return f"sudo -n {pm} install -y perl-Image-ExifTool 2>/dev/null || sudo {pm} install -y perl-Image-ExifTool || {pm} install -y perl-Image-ExifTool"
        if name == "ffmpeg":
            return f"sudo -n {pm} install -y ffmpeg 2>/dev/null || sudo {pm} install -y ffmpeg || {pm} install -y ffmpeg"
        if name == "qpdf":
            return f"sudo -n {pm} install -y qpdf 2>/dev/null || sudo {pm} install -y qpdf || {pm} install -y qpdf"
    if pm == "pacman":
        if name == "exiftool":
            return "sudo -n pacman -S --noconfirm perl-image-exiftool 2>/dev/null || sudo pacman -S --noconfirm perl-image-exiftool || pacman -S --noconfirm perl-image-exiftool"
        if name == "ffmpeg":
            return "sudo -n pacman -S --noconfirm ffmpeg 2>/dev/null || sudo pacman -S --noconfirm ffmpeg || pacman -S --noconfirm ffmpeg"
        if name == "qpdf":
            return "sudo -n pacman -S --noconfirm qpdf 2>/dev/null || sudo pacman -S --noconfirm qpdf || pacman -S --noconfirm qpdf"
    if pm == "zypper":
        if name == "exiftool":
            return "sudo -n zypper --non-interactive install perl-Image-ExifTool 2>/dev/null || sudo zypper --non-interactive install perl-Image-ExifTool || zypper --non-interactive install perl-Image-ExifTool"
        if name == "ffmpeg":
            return "sudo -n zypper --non-interactive install ffmpeg 2>/dev/null || sudo zypper --non-interactive install ffmpeg || zypper --non-interactive install ffmpeg"
        if name == "qpdf":
            return "sudo -n zypper --non-interactive install qpdf 2>/dev/null || sudo zypper --non-interactive install qpdf || zypper --non-interactive install qpdf"
    if pm == "apk":
        if name == "exiftool":
            return "doas apk add --no-cache exiftool 2>/dev/null || sudo -n apk add --no-cache exiftool 2>/dev/null || apk add --no-cache exiftool"
        if name == "ffmpeg":
            return "doas apk add --no-cache ffmpeg 2>/dev/null || sudo -n apk add --no-cache ffmpeg 2>/dev/null || apk add --no-cache ffmpeg"
        if name == "qpdf":
            return "doas apk add --no-cache qpdf 2>/dev/null || sudo -n apk add --no-cache qpdf 2>/dev/null || apk add --no-cache qpdf"
    if pm == "brew":
        if name == "exiftool":
            return "brew install exiftool"
        if name == "ffmpeg":
            return "brew install ffmpeg"
        if name == "qpdf":
            return "brew install qpdf"
    if pm == "winget":
        if name == "exiftool":
            return "winget install --silent --accept-source-agreements --accept-package-agreements Oliver.Bettenworth.ExifTool"
        if name == "ffmpeg":
            return "winget install --silent --accept-source-agreements --accept-package-agreements Gyan.FFmpeg"
        if name == "qpdf":
            return "winget install --silent --accept-source-agreements --accept-package-agreements QPDF.QPDF"
    if pm == "choco":
        if name == "exiftool":
            return "choco install exiftool -y"
        if name == "ffmpeg":
            return "choco install ffmpeg -y"
        if name == "qpdf":
            return "choco install qpdf -y"
    if pm == "scoop":
        if name == "exiftool":
            return "scoop install exiftool"
        if name == "ffmpeg":
            return "scoop install ffmpeg"
        if name == "qpdf":
            return "scoop install qpdf"
    return None


def check_tool(spec: dict[str, str | list[str]]) -> ToolStatus:
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
    statuses: list[ToolStatus] = []
    for spec in REQUIRED_TOOLS:
        status = check_tool(spec)
        if not status.available:
            status.install_command = get_install_command(status.name, env)
        statuses.append(status)
    return statuses


def attempt_install(name: str, env: EnvironmentInfo, runner) -> bool:
    command = get_install_command(name, env)
    if not command:
        return False
    if "&&" in command or "||" in command:
        return runner(command, shell=True)
    parts = command.split()
    if not parts:
        return False
    return runner(parts, shell=False)


def recheck_tool(name: str) -> ToolStatus:
    for spec in REQUIRED_TOOLS:
        if str(spec["name"]) == name:
            return check_tool(spec)
    return ToolStatus(name=name)
