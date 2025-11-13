#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Icon extraction from Windows executables using wrestool and icotool."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def extract_icon(
    exe_path: Path,
    icon_dir: Path,
    icon_name: str,
    verbose: bool = False,
) -> Optional[Path]:
    """Extract icon from .exe file using wrestool and icotool.

    Args:
        exe_path: Path to the .exe file
        icon_dir: Directory where to save the extracted icon
        icon_name: Base name for the icon file (without extension)
        verbose: Print detailed extraction information

    Returns:
        Path to the extracted .png icon, or None if extraction failed

    Notes:
        Requires icoutils (wrestool, icotool) to be installed on the system.
        Uses sudo for wrestool as it may need elevated permissions to read .exe files.
    """
    # Check if required tools are available
    if not shutil.which("wrestool"):
        console.print(
            "[yellow]Warning:[/] wrestool not found. Icon extraction disabled.",
        )
        console.print("           Install with: sudo apt install icoutils")
        return None

    if not shutil.which("icotool"):
        console.print(
            "[yellow]Warning:[/] icotool not found. Icon extraction disabled.",
        )
        console.print("           Install with: sudo apt install icoutils")
        return None

    tmp_ico = Path("/tmp") / f"{icon_name}.ico"
    tmp_png_dir = Path("/tmp") / "wine_chroot_icons"

    if verbose:
        console.print(f"[dim]Extracting icon from {exe_path}...[/]")

    # Step 1: Extract .ico from .exe using wrestool
    try:
        subprocess.run(
            ["sudo", "wrestool", "-x", "-t14", str(exe_path), "-o", str(tmp_ico)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[yellow]wrestool failed: {e.stderr}[/]")
        else:
            console.print("[yellow]Warning:[/] Failed to extract .ico with wrestool")
        return None

    if not tmp_ico.exists():
        console.print("[yellow]Warning:[/] wrestool did not produce an .ico file")
        return None

    # Step 2: Convert .ico to .png using icotool
    tmp_png_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["icotool", "-x", str(tmp_ico), "-o", str(tmp_png_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[yellow]icotool failed: {e.stderr}[/]")
        else:
            console.print("[yellow]Warning:[/] Failed to convert .ico to .png")
        return None

    # Step 3: Find the largest PNG (usually the last one alphabetically)
    pngs = sorted(tmp_png_dir.glob("*.png"))
    if not pngs:
        console.print("[yellow]Warning:[/] No .png files were extracted")
        return None

    # Choose the largest PNG by filename (e.g., *_256x256x32.png)
    chosen_png = pngs[-1]

    # Copy to final destination
    icon_dir.mkdir(parents=True, exist_ok=True)
    final_icon = icon_dir / f"{icon_name}.png"
    shutil.copy(chosen_png, final_icon)

    if verbose:
        console.print(f"[green]Icon extracted to {final_icon}[/]")

    # Cleanup
    try:
        tmp_ico.unlink(missing_ok=True)
        for png in pngs:
            png.unlink(missing_ok=True)
        tmp_png_dir.rmdir()
    except Exception:
        pass  # Ignore cleanup errors

    return final_icon


def find_system_icon(app_name: str) -> Optional[str]:
    """Try to find a system icon that matches the application name.

    Args:
        app_name: Application name to search for

    Returns:
        Icon name/path if found, None otherwise

    Notes:
        This searches common icon themes for icons matching the app name.
        Useful as a fallback when icon extraction fails.
    """
    # Common icon locations
    icon_paths = [
        Path("/usr/share/icons/hicolor"),
        Path("/usr/share/pixmaps"),
        Path.home() / ".local" / "share" / "icons",
    ]

    # Normalize app name for searching
    search_name = app_name.lower().replace(" ", "-")

    for base_path in icon_paths:
        if not base_path.exists():
            continue

        # Search for PNG/SVG icons
        for pattern in [f"**/{search_name}.png", f"**/{search_name}.svg"]:
            icons = list(base_path.glob(pattern))
            if icons:
                return str(icons[0])

    return None


def get_wine_icon() -> str:
    """Get the default Wine icon name.

    Returns:
        Icon name for Wine applications
    """
    return "wine"
