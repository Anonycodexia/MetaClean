from __future__ import annotations

import os
import platform
import shutil
import sys

from .config import EnvironmentInfo


TERMUX_INDICATORS = ("TERMUX_VERSION", "PREFIX")
TERMUX_PREFIX_VALUE = "/data/data/com.termux/files/usr"


def detect_termux() -> bool:
    for name in TERMUX_INDICATORS:
        if os.environ.get(name):
            value = os.environ[name]
            if name == "PREFIX" and value == TERMUX_PREFIX_VALUE:
                return True
            if name == "TERMUX_VERSION":
                return True
    if os.path.isdir("/data/data/com.termux/files/usr"):
        return True
    return False


def detect_macos() -> bool:
    return sys.platform == "darwin"


def detect_windows() -> bool:
    return sys.platform in ("win32", "cygwin", "msys")


def detect_linux() -> bool:
    return sys.platform.startswith("linux") and not detect_termux()


def detect_architecture() -> str:
    machine = platform.machine() or platform.processor() or "unknown"
    return machine


def detect_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def detect_linux_distribution() -> str:
    if not detect_linux():
        return "Linux"
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            data = handle.read()
        info: dict[str, str] = {}
        for line in data.splitlines():
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            info[key.strip().lower()] = value.strip().strip('"').strip("'")
        if "pretty_name" in info:
            return info["pretty_name"]
        if "name" in info:
            return info["name"]
    except OSError:
        pass
    return "Linux"


def detect_platform_name() -> str:
    if detect_termux():
        version = os.environ.get("TERMUX_VERSION", "")
        if version:
            return f"Termux {version}"
        return "Termux"
    if detect_macos():
        return f"macOS {platform.mac_ver()[0]}"
    if detect_windows():
        return f"Windows {platform.release()}"
    if detect_linux():
        return detect_linux_distribution()
    return f"{platform.system()} {platform.release()}"


def detect_package_managers() -> list[str]:
    found: list[str] = []
    if detect_termux():
        if shutil.which("pkg"):
            found.append("pkg")
        return found
    if detect_macos():
        if shutil.which("brew"):
            found.append("brew")
        return found
    if detect_windows():
        for candidate in ("winget", "choco", "scoop"):
            if shutil.which(candidate):
                found.append(candidate)
        return found
    if detect_linux():
        for candidate in ("apt", "apt-get", "dnf", "yum", "pacman", "zypper", "apk", "nix", "snap", "flatpak"):
            if shutil.which(candidate):
                found.append(candidate)
        return found
    return found


def detect_shell() -> str:
    shell = os.environ.get("SHELL")
    if shell:
        return shell
    if detect_windows():
        comspec = os.environ.get("COMSPEC")
        if comspec:
            return comspec
    return "unknown"


def detect_environment() -> EnvironmentInfo:
    info = EnvironmentInfo(
        platform_name=detect_platform_name(),
        architecture=detect_architecture(),
        python_version=detect_python_version(),
        shell=detect_shell(),
        package_managers=detect_package_managers(),
    )
    if detect_termux():
        info.is_termux = True
        info.platform_kind = "termux"
    elif detect_linux():
        info.is_linux = True
        info.platform_kind = "linux"
    elif detect_macos():
        info.is_macos = True
        info.platform_kind = "macos"
    elif detect_windows():
        info.is_windows = True
        info.platform_kind = "windows"
    return info
