#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Wine execution wrapper for running Windows applications in chroot."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from rich.console import Console

from .config import Config
from .utils import linux_path_to_windows

console = Console()


class WineRunner:
    """Manages execution of Windows applications through Wine in a chroot."""

    def __init__(self, config: Config, verbose: bool = False):
        """Initialize Wine runner.

        Args:
            config: Configuration instance
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

    def run(
        self,
        exe_path: str | Path,
        args: list[str] | None = None,
        wait: bool = False,
        show_terminal: bool = False,
    ) -> int:
        """Run a Windows application.

        Args:
            exe_path: Path to .exe file (Windows or Linux format)
            args: Additional arguments to pass to the application
            wait: Wait for application to exit before returning
            show_terminal: Show terminal output (don't capture stdout/stderr)

        Returns:
            Exit code of the application

        Raises:
            SystemExit: If execution fails
        """
        # Convert path to Windows format if needed
        if isinstance(exe_path, Path) or "/" in str(exe_path):
            win_path = linux_path_to_windows(exe_path)
        else:
            win_path = str(exe_path)

        # Build command
        privilege_cmd = "pkexec" if self.config.use_pkexec else "sudo"
        cmd = [
            privilege_cmd,
            "schroot",
            "-c", self.config.chroot_name,
            "--",
        ]

        # Preserve environment variables for X11
        if self.config.get("execution.x11_forwarding", True):
            display = os.environ.get("DISPLAY", ":0")
            xauthority = os.environ.get("XAUTHORITY", "")

            cmd.extend([
                "env",
                f"DISPLAY={display}",
            ])

            if xauthority:
                cmd.append(f"XAUTHORITY={xauthority}")

        # Add Wine command
        cmd.extend(["wine", win_path])

        # Add application arguments
        if args:
            cmd.extend(args)

        if self.verbose:
            console.print(f"[dim]$ {' '.join(cmd)}[/]")

        # Enable X11 access for local connections
        if self.config.get("execution.x11_forwarding", True):
            try:
                subprocess.run(
                    ["xhost", "+local:"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except FileNotFoundError:
                pass  # xhost not available, continue anyway

        # Execute
        try:
            if wait or show_terminal:
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=not show_terminal,
                )
                return result.returncode
            else:
                # Run in background
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                if self.verbose:
                    console.print("[green]Application started in background[/]")
                return 0

        except subprocess.CalledProcessError as e:
            console.print("[bold red]Error:[/] Failed to run application")
            console.print(f"Exit code: {e.returncode}")
            if e.stderr:
                console.print(f"Error output: {e.stderr}")
            return e.returncode

        except FileNotFoundError as exc:
            console.print(
                f"[bold red]Error:[/] Command not found: {privilege_cmd}",
            )
            console.print(
                f"Please install {privilege_cmd} or update your configuration",
            )
            raise SystemExit(1) from exc

    def run_wine_command(
        self,
        wine_args: list[str],
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a Wine command inside the chroot.

        Args:
            wine_args: Arguments to pass to Wine
            capture_output: Capture stdout/stderr

        Returns:
            CompletedProcess instance

        Examples:
            >>> runner.run_wine_command(["--version"])
            >>> runner.run_wine_command(["winecfg"])
        """
        privilege_cmd = "pkexec" if self.config.use_pkexec else "sudo"
        cmd = [
            privilege_cmd,
            "schroot",
            "-c", self.config.chroot_name,
            "--",
            "wine",
        ]
        cmd.extend(wine_args)

        if self.verbose:
            console.print(f"[dim]$ {' '.join(cmd)}[/]")

        return subprocess.run(
            cmd,
            check=False,
            capture_output=capture_output,
            text=True,
        )

    def check_wine_installation(self) -> bool:
        """Check if Wine is properly installed in the chroot.

        Returns:
            True if Wine is installed and working
        """
        try:
            result = self.run_wine_command(["--version"], capture_output=True)
            if result.returncode == 0 and result.stdout:
                version = result.stdout.strip()
                if self.verbose:
                    console.print(f"[green]Wine is installed: {version}[/]")
                return True
        except Exception as e:
            if self.verbose:
                console.print(f"[yellow]Wine check failed: {e}[/]")

        return False

    def get_wine_version(self) -> str | None:
        """Get the Wine version installed in the chroot.

        Returns:
            Wine version string, or None if unavailable
        """
        try:
            result = self.run_wine_command(["--version"], capture_output=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except Exception:
            pass

        return None
