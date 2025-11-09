#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""
make_wine_chroot_desktop.py

Generate a .desktop launcher that runs a Windows .exe with Wine inside a schroot.
The script runs on the host and creates desktop shortcuts that launch applications
inside the chroot environment where Wine is installed.

Use cases:
- Run Windows x86/amd64 applications on ARM64 hosts using a Debian amd64 schroot
- Isolate Wine applications in separate chroot environments

Usage:
    python3 make_wine_chroot_desktop.py \
        --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/WlkataStudio/WlkataStudio.exe" \
        --name "Wlkata Studio (Wine chroot)" \
        --icon

Requirements:
- Host: schroot, icoutils (wrestool, icotool)
- Chroot: Wine installed and ready

This program is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.
"""

from __future__ import annotations
import argparse
import re
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich_argparse import RichHelpFormatter


console = Console()


def linux_path_to_win(path: str) -> str:
    """Convert a path under drive_c/ to a Windows-style path when possible."""
    if re.match(r"^[A-Za-z]:\\", path):
        return path  # already in Windows format

    if "drive_c/" in path:
        after = path.split("drive_c/", 1)[1]
        win = after.replace("/", "\\")
        return f"C:\\{win}"
    # fall back to the original path (Wine can handle Unix paths)
    return path


def extract_icon(exe_path: Path, icon_dir: Path, desktop_basename: str) -> Path | None:
    """Try extracting the icon from the .exe using wrestool + icotool."""
    tmp_ico = Path("/tmp") / f"{desktop_basename}.ico"

    # Step 1: wrestool
    try:
        subprocess.run(
            ["sudo", "wrestool", "-x", "-t14", str(exe_path), "-o", str(tmp_ico)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"Failed to extract .ico with wrestool: {e}", style="yellow")
        return None

    if not tmp_ico.exists():
        console.print("wrestool did not produce an .ico", style="yellow")
        return None

    # Step 2: icotool to /tmp/icoextract_py
    tmp_png_dir = Path("/tmp/icoextract_py")
    tmp_png_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["icotool", "-x", str(tmp_ico), "-o", str(tmp_png_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"Failed to convert .ico to .png: {e}", style="yellow")
        return None

    pngs = sorted(tmp_png_dir.glob("*.png"))
    if not pngs:
        console.print("No extracted PNGs were found", style="yellow")
        return None

    # Pick the "largest" by filename (usually the last one)
    chosen_png = pngs[-1]
    icon_dir.mkdir(parents=True, exist_ok=True)
    final_icon = icon_dir / f"{desktop_basename}.png"
    shutil.copy(chosen_png, final_icon)
    console.print(f"Icon copied to '{final_icon}'", style="green")
    return final_icon


def build_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a .desktop launcher that runs an .exe with Wine inside a schroot.",
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument(
        "-e", "--exe",
        required=True,
        help="Path to the .exe as seen from the host inside the schroot tree",
    )
    parser.add_argument(
        "-n", "--name",
        required=True,
        help="Application name displayed in the desktop menu",
    )
    parser.add_argument(
        "-d", "--desktop",
        help="Name of the .desktop file (defaults to a slugified app name)",
    )
    parser.add_argument(
        "-i", "--icon",
        action="store_true",
        help="Attempt to extract the .exe icon using wrestool and icotool",
    )
    parser.add_argument(
        "-s", "--schroot",
        default="debian-amd64",
        help="Name of the schroot to use (default: debian-amd64)",
    )
    return parser


def main() -> None:
    """Generate a .desktop entry for launching Windows executables inside a Wine schroot.

    The script produces desktop menu entries that run Windows executables within an isolated
    schroot environment using Wine. Optionally, it can extract icons from the executable and
    populate the desktop entry with useful metadata.
    """
    parser = build_parser()
    args = parser.parse_args()

    exe_path = Path(args.exe).expanduser()
    try:
        if not exe_path.exists():
            console.print(f"The .exe does not exist at this path: '{exe_path}'", style="bold red")
            console.print(
                "    Remember that this must be the path as seen from the host, e.g.",
                style="bold red",
            )
            console.print(
                "    /srv/debian-amd64/root/.wine/drive_c/Program Files/...",
                style="bold red",
            )
            raise SystemExit(1)
    except PermissionError:
        console.print(
            f"Cannot verify if '{exe_path}' exists (permission denied).",
            style="yellow",
        )
        console.print(
            "    Continuing anyway. If the path is incorrect, the .desktop launcher will fail.",
            style="yellow",
        )

    app_name = args.name
    # determine .desktop filename
    if args.desktop:
        desktop_filename = args.desktop
    else:
        desktop_filename = re.sub(r"[^a-z0-9]+", "-", app_name.lower()).strip("-") + ".desktop"

    desktop_dir = Path.home() / ".local" / "share" / "applications"
    icon_dir = Path.home() / ".local" / "share" / "icons"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    # convert the Linux path to a Windows path (C:\...)
    win_exe_path = linux_path_to_win(str(exe_path))

    # optional icon extraction
    icon_path: Path | None = None
    if args.icon:
        icon_path = extract_icon(exe_path, icon_dir, desktop_filename.replace(".desktop", ""))

    desktop_file = desktop_dir / desktop_filename

    # .desktop file contents
    lines = [
        "[Desktop Entry]",
        f"Name={app_name}",
        f"Comment=Run {app_name} inside the {args.schroot} schroot",
        # command executed when launching the shortcut
        f'Exec=pkexec schroot -c {args.schroot} -- wine "{win_exe_path}"',
        "Type=Application",
        "Categories=Wine;WindowsApps;",
        "StartupNotify=true",
        "Terminal=false",
        # helps desktop environments to group the app window
        f"StartupWMClass={Path(win_exe_path).name}",
    ]
    if icon_path:
        lines.append(f"Icon={icon_path}")

    desktop_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"Desktop file created at: '{desktop_file}'", style="cyan")

    # try to refresh desktop database
    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        # ignore if the utility is unavailable
        pass

    console.print()
    console.print("Done.", style="bold green")
    console.print(f'Look for "{app_name}" in your application menu.')
    console.print("If sudo prompts for a password, add a sudoers entry such as:")
    console.print("    YOURUSER ALL=(ALL) NOPASSWD: /usr/bin/schroot")


if __name__ == "__main__":
    main()
