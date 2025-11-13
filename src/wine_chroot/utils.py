#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Utility functions for path conversion, validation, and system checks."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def linux_path_to_windows(path: str | Path) -> str:
    """Convert a Linux path to Windows format.

    Args:
        path: Linux path, potentially inside a Wine drive_c directory

    Returns:
        Windows-style path string (e.g., "C:\\Program Files\\app.exe")

    Examples:
        >>> linux_path_to_windows("/srv/debian-amd64/root/.wine/drive_c/Program Files/app.exe")
        "C:\\\\Program Files\\\\app.exe"
        >>> linux_path_to_windows("C:\\\\Windows\\\\System32")
        "C:\\\\Windows\\\\System32"
    """
    path_str = str(path)

    # Already in Windows format
    if re.match(r"^[A-Za-z]:\\", path_str):
        return path_str

    # Contains drive_c/ - convert to C:\
    if "drive_c/" in path_str:
        after = path_str.split("drive_c/", 1)[1]
        win = after.replace("/", "\\")
        return f"C:\\{win}"

    # Fallback: return original (Wine can handle Unix paths)
    return path_str


def windows_path_to_linux(win_path: str, chroot_path: Path, wine_prefix: str = ".wine") -> Path:
    """Convert a Windows path to Linux path inside chroot.

    Args:
        win_path: Windows-style path (e.g., "C:\\Program Files\\app.exe")
        chroot_path: Root path of the chroot
        wine_prefix: Wine prefix directory name (default: .wine)

    Returns:
        Linux Path object pointing to the file in the chroot

    Examples:
        >>> windows_path_to_linux("C:\\\\Program Files\\\\app.exe", Path("/srv/debian-amd64"))
        PosixPath('/srv/debian-amd64/root/.wine/drive_c/Program Files/app.exe')
    """
    # Remove C:\ or c:\ prefix
    if re.match(r"^[A-Za-z]:\\", win_path):
        win_path = win_path[3:]

    # Convert backslashes to forward slashes
    linux_part = win_path.replace("\\", "/")

    # Build full path
    return chroot_path / "root" / wine_prefix / "drive_c" / linux_part


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def check_system_dependencies(verbose: bool = False) -> tuple[bool, list[str]]:
    """Check if required system dependencies are installed.

    Args:
        verbose: Print detailed information

    Returns:
        Tuple of (all_ok, missing_commands)
    """
    required = {
        "schroot": "Manage chroot sessions",
        "debootstrap": "Create Debian base systems",
        "qemu-user-static": "x86-64 emulation on ARM64 (or qemu-x86_64-static)",
        "wrestool": "Extract icons from .exe files (package: icoutils)",
        "icotool": "Convert .ico to .png (package: icoutils)",
    }

    missing = []
    for cmd, description in required.items():
        # Special case: qemu can have different names
        if cmd == "qemu-user-static":
            if not (check_command_exists("qemu-x86_64-static") or
                    check_command_exists("qemu-user-static")):
                missing.append(cmd)
                if verbose:
                    console.print(f"[yellow]✗[/] {cmd}: {description}")
            elif verbose:
                console.print(f"[green]✓[/] {cmd}: {description}")
        elif not check_command_exists(cmd):
            missing.append(cmd)
            if verbose:
                console.print(f"[yellow]✗[/] {cmd}: {description}")
        elif verbose:
            console.print(f"[green]✓[/] {cmd}: {description}")

    return len(missing) == 0, missing


def run_command(
    cmd: list[str],
    check: bool = True,
    capture_output: bool = True,
    verbose: bool = False,
) -> subprocess.CompletedProcess:
    """Run a shell command with optional output capture.

    Args:
        cmd: Command and arguments as list
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr
        verbose: Print command before executing

    Returns:
        CompletedProcess instance

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    if verbose:
        console.print(f"[dim]$ {' '.join(cmd)}[/]")

    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def slugify(text: str) -> str:
    """Convert text to a safe filename slug.

    Args:
        text: Input text

    Returns:
        Slugified string suitable for filenames

    Examples:
        >>> slugify("My Application (Wine)")
        "my-application-wine"
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def validate_exe_path(exe_path: Path, chroot_path: Path | None = None) -> bool:
    """Validate that an .exe path exists and is accessible.

    Args:
        exe_path: Path to the .exe file
        chroot_path: Optional chroot path for additional validation

    Returns:
        True if valid and accessible
    """
    try:
        if not exe_path.exists():
            console.print(
                f"[bold red]Error:[/] The .exe does not exist at '{exe_path}'",
            )
            if chroot_path:
                console.print(
                    "[yellow]Hint:[/] Make sure the path is from the host perspective:",
                )
                console.print(f"        {chroot_path}/root/.wine/drive_c/Program Files/...")
            return False

        if not exe_path.is_file():
            console.print(f"[bold red]Error:[/] Path exists but is not a file: '{exe_path}'")
            return False

        return True

    except PermissionError:
        console.print(
            f"[yellow]Warning:[/] Cannot verify if '{exe_path}' exists (permission denied)",
        )
        console.print(
            "            Continuing anyway. If the path is incorrect, execution will fail.",
        )
        return True  # Assume it exists, will fail later if not


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_float = float(size_bytes)
    for unit in ["KB", "MB", "GB", "TB"]:
        size_float /= 1024.0
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
    return f"{size_float:.1f} PB"
