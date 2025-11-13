#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Desktop integration for creating .desktop launchers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

from .config import Config
from .icons import extract_icon, get_wine_icon
from .utils import linux_path_to_windows, slugify, validate_exe_path

console = Console()


class DesktopManager:
    """Manages creation and management of .desktop files for Wine applications."""

    def __init__(self, config: Config, verbose: bool = False):
        """Initialize desktop manager.

        Args:
            config: Configuration instance
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

    def create_launcher(
        self,
        exe_path: Path,
        app_name: str,
        extract_icon_flag: bool = False,
        desktop_filename: Optional[str] = None,
    ) -> Path:
        """Create a .desktop launcher for a Windows application.

        Args:
            exe_path: Path to the .exe file (from host perspective)
            app_name: Application name for the menu
            extract_icon_flag: Whether to extract icon from .exe
            desktop_filename: Custom .desktop filename (optional)

        Returns:
            Path to the created .desktop file

        Raises:
            SystemExit: If launcher creation fails
        """
        # Validate .exe path
        if not validate_exe_path(exe_path, self.config.chroot_path):
            raise SystemExit(1)

        # Determine .desktop filename
        if not desktop_filename:
            desktop_filename = slugify(app_name) + ".desktop"
        elif not desktop_filename.endswith(".desktop"):
            desktop_filename += ".desktop"

        desktop_dir = self.config.applications_dir
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_file = desktop_dir / desktop_filename

        # Convert to Windows path
        win_exe_path = linux_path_to_windows(exe_path)

        # Extract icon if requested
        icon_path: Optional[Path] = None
        if extract_icon_flag:
            icon_name = slugify(app_name)
            icon_path = extract_icon(
                exe_path,
                self.config.icon_dir,
                icon_name,
                self.verbose,
            )

        # Build .desktop file content
        lines = [
            "[Desktop Entry]",
            f"Name={app_name}",
            f"Comment=Run {app_name} inside the {self.config.chroot_name} chroot",
        ]

        # Build Exec command
        privilege_cmd = "pkexec" if self.config.use_pkexec else "sudo"
        exec_line = (
            f'Exec={privilege_cmd} schroot -c {self.config.chroot_name} '
            f'-- wine "{win_exe_path}"'
        )
        lines.append(exec_line)

        # Standard fields
        lines.extend([
            "Type=Application",
            f"Categories={';'.join(self.config.get('desktop.categories', ['Wine', 'WindowsApps']))};",
            "StartupNotify=true",
            "Terminal=false",
            f"StartupWMClass={Path(win_exe_path).name}",
        ])

        # Add icon if available
        if icon_path:
            lines.append(f"Icon={icon_path}")
        else:
            lines.append(f"Icon={get_wine_icon()}")

        # Write .desktop file
        desktop_content = "\n".join(lines) + "\n"
        desktop_file.write_text(desktop_content, encoding="utf-8")

        console.print(
            f"[green]Desktop launcher created:[/] {desktop_file}",
        )

        # Update desktop database
        self._update_desktop_database(desktop_dir)

        # Show usage hints
        console.print()
        console.print(f'[cyan]Look for "{app_name}" in your application menu[/]')

        if self.config.use_pkexec:
            console.print(
                "[yellow]Note:[/] Using pkexec may cause issues with some applications.",
            )
            console.print(
                "       Consider using sudo for better reliability (set use_pkexec = false in config).",
            )
        else:
            console.print(
                "[yellow]Tip:[/] To avoid password prompts when launching, add a sudoers entry:",
            )
            console.print(
                "     echo '$USER ALL=(ALL) NOPASSWD: /usr/bin/schroot' | sudo tee /etc/sudoers.d/schroot",
            )
            console.print(
                "     sudo chmod 0440 /etc/sudoers.d/schroot",
            )

        return desktop_file

    def _update_desktop_database(self, desktop_dir: Path) -> None:
        """Update the desktop database to refresh application menus.

        Args:
            desktop_dir: Directory containing .desktop files
        """
        try:
            subprocess.run(
                ["update-desktop-database", str(desktop_dir)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if self.verbose:
                console.print("[dim]Desktop database updated[/]")
        except FileNotFoundError:
            if self.verbose:
                console.print(
                    "[dim]update-desktop-database not found, skipping[/]",
                )

    def list_desktop_files(self) -> list[tuple[str, Path]]:
        """List all Wine-related .desktop files.

        Returns:
            List of (app_name, desktop_file_path) tuples
        """
        desktop_dir = self.config.applications_dir
        if not desktop_dir.exists():
            return []

        wine_desktops = []
        for desktop_file in desktop_dir.glob("*.desktop"):
            try:
                content = desktop_file.read_text(encoding="utf-8")
                # Check if it's a Wine-related desktop file
                if "schroot" in content and "wine" in content.lower():
                    # Extract name
                    for line in content.split("\n"):
                        if line.startswith("Name="):
                            app_name = line.split("=", 1)[1].strip()
                            wine_desktops.append((app_name, desktop_file))
                            break
            except Exception:
                continue

        return sorted(wine_desktops)

    def remove_launcher(self, desktop_file: Path) -> bool:
        """Remove a .desktop launcher.

        Args:
            desktop_file: Path to the .desktop file

        Returns:
            True if removed successfully
        """
        try:
            if desktop_file.exists():
                desktop_file.unlink()
                console.print(f"[green]Removed launcher:[/] {desktop_file}")
                self._update_desktop_database(self.config.applications_dir)
                return True
            else:
                console.print(f"[yellow]Launcher not found:[/] {desktop_file}")
                return False
        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to remove launcher: {e}")
            return False

    def list_wine_applications(self) -> list[dict]:
        """Scan the chroot for installed Windows applications.

        Returns:
            List of dictionaries with application information

        Notes:
            Scans common Wine installation directories for .exe files.
        """
        chroot_path = self.config.chroot_path
        wine_prefix = self.config.wine_prefix

        # Common application directories
        search_dirs = [
            chroot_path / wine_prefix.lstrip("/") / "drive_c" / "Program Files",
            chroot_path / wine_prefix.lstrip("/") / "drive_c" / "Program Files (x86)",
        ]

        applications = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Find .exe files (excluding uninstallers and updaters)
            for exe_file in search_dir.rglob("*.exe"):
                exe_name = exe_file.name.lower()

                # Skip common non-application executables
                if any(skip in exe_name for skip in [
                    "unins", "uninst", "uninstall",
                    "update", "updater", "setup", "install",
                ]):
                    continue

                # Check if a .desktop file exists
                desktop_exists = False
                for _, desktop_path in self.list_desktop_files():
                    try:
                        content = desktop_path.read_text()
                        if str(exe_file) in content or exe_file.name in content:
                            desktop_exists = True
                            break
                    except Exception:
                        continue

                applications.append({
                    "name": exe_file.stem,
                    "path": exe_file,
                    "win_path": linux_path_to_windows(exe_file),
                    "has_desktop": desktop_exists,
                })

        return applications
