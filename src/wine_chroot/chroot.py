#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Chroot initialization and management."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .console_styles import console, error, step, success, warning
from .utils import check_command_exists


class ChrootManager:
    """Manages chroot creation, configuration, and validation."""

    def __init__(self, config: Config, verbose: bool = False):
        """Initialize chroot manager.

        Args:
            config: Configuration instance
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

    def check_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if all required tools are available.

        Returns:
            Tuple of (all_ok, missing_commands)
        """
        required = [
            "debootstrap",
            "schroot",
            "qemu-x86_64-static",
            "pkexec",
        ]

        missing = []
        for cmd in required:
            if cmd == "qemu-x86_64-static":
                # Check for qemu user static in different locations
                if not (
                    check_command_exists("qemu-x86_64-static")
                    or Path("/usr/bin/qemu-x86_64-static").exists()
                    or Path("/usr/libexec/qemu-binfmt/x86_64-static").exists()
                ):
                    missing.append(cmd)
            elif not check_command_exists(cmd):
                missing.append(cmd)

        return len(missing) == 0, missing

    def check_root_access(self) -> bool:
        """Check if we can get root access via sudo or pkexec.

        Returns:
            True if root access is available
        """
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                timeout=2,
                check=True,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def initialize(
        self,
        chroot_name: str | None = None,
        chroot_path: Path | None = None,
        debian_version: str = "trixie",
        skip_wine: bool = False,
        dry_run: bool = False,
    ) -> bool:
        """Initialize a complete chroot environment.

        Args:
            chroot_name: Name for the schroot configuration
            chroot_path: Path where to install the chroot
            debian_version: Debian version to install
            skip_wine: Don't install Wine automatically
            dry_run: Show what would be done without executing

        Returns:
            True if initialization succeeded

        Raises:
            SystemExit: If initialization fails
        """
        # Use config values if not provided
        if not chroot_name:
            chroot_name = self.config.chroot_name
        if not chroot_path:
            # If a custom name was provided, derive path from it
            # Otherwise use the config path
            if chroot_name and chroot_name != self.config.chroot_name:
                chroot_path = Path("/srv") / chroot_name
            else:
                chroot_path = self.config.chroot_path

        console.print("\n[bold cyan]Wine Chroot Initialization[/]")
        console.print(f"Chroot name: [yellow]{chroot_name}[/]")
        console.print(f"Install path: [yellow]{chroot_path}[/]")
        console.print(f"Debian version: [yellow]{debian_version}[/]")
        console.print()

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be made[/]")
            console.print()

        # Step 1: Check prerequisites
        step(1, "Checking prerequisites...")
        all_ok, missing = self.check_prerequisites()
        if not all_ok:
            error(f"Missing required tools: {', '.join(missing)}")
            console.print("\nInstall with:")
            console.print("  sudo apt install debootstrap schroot qemu-user-static binfmt-support")
            return False

        if not self.check_root_access():
            warning("Cannot verify sudo access without password")
            console.print("           You may be prompted for your password during installation")

        success("All prerequisites available")

        # Step 2: Check if chroot already exists
        console.print()
        step(2, "Checking if chroot already exists...")
        if chroot_path.exists():
            error(f"Path already exists: {chroot_path}")
            console.print("         Please remove it first or choose a different path")
            return False
        success("Path is available")

        # Step 3: Create base system with debootstrap
        if not self._run_debootstrap(chroot_path, debian_version, dry_run):
            return False

        # Step 4: Configure schroot
        if not self._configure_schroot(chroot_name, chroot_path, dry_run):
            return False

        # Step 5: Configure fstab for bind mounts
        if not self._configure_fstab(dry_run):
            return False

        # Step 6: Configure locales
        if not self._configure_locales(chroot_name, dry_run):
            return False

        # Step 7: Add package repositories
        if not self._configure_repositories(chroot_name, debian_version, dry_run):
            return False

        # Step 8: Enable i386 architecture
        if not self._enable_i386(chroot_name, dry_run):
            return False

        # Step 9: Install Wine
        if not skip_wine:
            if not self._install_wine(chroot_name, dry_run):
                return False
        else:
            console.print("\n[yellow]Skipping Wine installation (--skip-wine)[/]")

        # Step 10: Verify installation
        if not dry_run:
            if not self._verify_installation(chroot_name):
                console.print()
                warning("Verification failed, but chroot was created")
                console.print("           You may need to configure it manually")

        # Success!
        console.print("\n[bold green]✓ Chroot initialization completed successfully![/]")
        console.print()
        console.print("Next steps:")
        console.print(f"  1. Test the chroot: sudo schroot -c {chroot_name}")
        if not skip_wine:
            console.print("  2. Test Wine: wine-chroot run 'C:\\Windows\\notepad.exe'")
        console.print(
            "  3. Create launchers: wine-chroot desktop -e /path/to/app.exe -n 'App Name'"
        )
        console.print()

        return True

    def _run_debootstrap(
        self,
        chroot_path: Path,
        debian_version: str,
        dry_run: bool,
    ) -> bool:
        """Run debootstrap to create base system.

        Args:
            chroot_path: Path where to install
            debian_version: Debian version
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(3, f"Creating Debian {debian_version} amd64 base system...")
        console.print("    This may take several minutes...")

        if dry_run:
            console.print(
                "[dim]Would run: sudo debootstrap --arch=amd64 "
                f"{debian_version} {chroot_path} http://deb.debian.org/debian[/]"
            )
            return True

        cmd = [
            "sudo",
            "debootstrap",
            "--arch=amd64",
            debian_version,
            str(chroot_path),
            "http://deb.debian.org/debian",
        ]

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing base system...", total=None)

                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes max
                    check=True,
                )

                progress.update(task, completed=True)

            success("Base system created")
            return True

        except subprocess.CalledProcessError as e:
            error("debootstrap failed")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return False
        except subprocess.TimeoutExpired:
            error("debootstrap timed out after 10 minutes")
            return False
        except FileNotFoundError:
            error(
                "debootstrap command not found", hint="Install with: sudo apt install debootstrap"
            )
            return False
        except PermissionError:
            error(
                "Permission denied running debootstrap",
                hint="This operation requires root privileges",
            )
            return False
        except OSError as e:
            error(
                f"System error running debootstrap: {e}",
                hint="Check disk space and filesystem availability",
            )
            return False

    def _configure_schroot(
        self,
        chroot_name: str,
        chroot_path: Path,
        dry_run: bool,
    ) -> bool:
        """Configure schroot.

        Args:
            chroot_name: Schroot name
            chroot_path: Chroot path
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(4, "Configuring schroot...")

        config_content = f"""[{chroot_name}]
description=Debian amd64 chroot for Wine
directory={chroot_path}
type=directory
users={Path.home().name}
root-users={Path.home().name}
personality=linux
preserve-environment=true
"""

        config_file = Path(f"/etc/schroot/chroot.d/{chroot_name}.conf")

        if dry_run:
            console.print(f"[dim]Would create: {config_file}[/]")
            console.print("[dim]Content:[/]")
            console.print(f"[dim]{config_content}[/]")
            return True

        try:
            # Write config using sudo tee
            subprocess.run(
                ["sudo", "tee", str(config_file)],
                input=config_content,
                capture_output=True,
                text=True,
                check=True,
            )

            console.print(f"[green]✓[/] Schroot configured: {config_file}")
            return True

        except subprocess.CalledProcessError as e:
            error("Failed to create schroot config")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return False
        except FileNotFoundError:
            error("sudo or tee command not found")
            return False
        except PermissionError:
            error(
                "Permission denied creating schroot config",
                hint="This operation requires root privileges",
            )
            return False
        except OSError as e:
            error(f"I/O error creating schroot config: {e}")
            return False

    def _configure_fstab(self, dry_run: bool) -> bool:
        """Configure fstab for bind mounts.

        Args:
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(5, "Configuring bind mounts...")

        fstab_content = """# fstab: static file system information for chroots.
# <file system> <mount point>   <type>  <options>  <dump>  <pass>
/dev            /dev            none    rw,bind    0       0
/dev/pts        /dev/pts        none    rw,bind    0       0
/home           /home           none    rw,bind    0       0
/proc           /proc           none    rw,bind    0       0
/sys            /sys            none    rw,bind    0       0
/tmp            /tmp            none    rw,bind    0       0
/tmp/.X11-unix  /tmp/.X11-unix  none    rw,bind    0       0
"""

        fstab_file = Path("/etc/schroot/default/fstab")

        if dry_run:
            console.print(f"[dim]Would update: {fstab_file}[/]")
            return True

        try:
            # Backup existing fstab if it exists
            if fstab_file.exists():
                backup = Path(f"{fstab_file}.backup.{int(time.time())}")
                subprocess.run(["sudo", "cp", str(fstab_file), str(backup)], check=True)
                console.print(f"[dim]Backed up existing fstab to {backup}[/]")

            # Write new fstab
            subprocess.run(
                ["sudo", "tee", str(fstab_file)],
                input=fstab_content,
                capture_output=True,
                text=True,
                check=True,
            )

            success("Bind mounts configured")
            return True

        except subprocess.CalledProcessError as e:
            error("Failed to configure fstab")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return False
        except FileNotFoundError:
            error("sudo, cp or tee command not found")
            return False
        except PermissionError:
            error(
                "Permission denied configuring fstab",
                hint="This operation requires root privileges",
            )
            return False
        except OSError as e:
            error(f"I/O error configuring fstab: {e}")
            return False

    def _configure_locales(self, chroot_name: str, dry_run: bool) -> bool:
        """Configure locales inside chroot.

        Args:
            chroot_name: Schroot name
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(6, "Configuring locales...")

        if dry_run:
            console.print("[dim]Would install locales and configure en_US.UTF-8[/]")
            return True

        try:
            # Install locales package
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "apt", "update"],
                capture_output=True,
                text=True,
                check=True,
            )

            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "apt", "install", "-y", "locales"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Generate en_US.UTF-8 locale
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "locale-gen", "en_US.UTF-8"],
                capture_output=True,
                check=True,
            )

            success("Locales configured")
            return True

        except subprocess.CalledProcessError as e:
            warning("Locale configuration failed")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return True  # Non-critical, continue
        except FileNotFoundError:
            console.print(
                "[yellow]Warning:[/] Required commands not found for locale configuration"
            )
            return True  # Non-critical, continue
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/] Locale configuration failed: {e}")
            return True  # Non-critical, continue

    def _configure_repositories(
        self,
        chroot_name: str,
        debian_version: str,
        dry_run: bool,
    ) -> bool:
        """Configure Debian repositories inside chroot.

        Args:
            chroot_name: Schroot name
            debian_version: Debian version
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(7, "Configuring Debian repositories...")

        sources_list = f"""# Debian {debian_version} repositories
deb http://deb.debian.org/debian {debian_version} main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian {debian_version} main contrib non-free non-free-firmware

# Updates
deb http://deb.debian.org/debian {debian_version}-updates main contrib non-free non-free-firmware

# Security
deb http://security.debian.org/debian-security {debian_version}-security main contrib non-free non-free-firmware
"""

        if dry_run:
            console.print("[dim]Would configure /etc/apt/sources.list inside chroot[/]")
            return True

        try:
            # Write sources.list inside chroot
            cmd = f'echo "{sources_list}" | sudo tee /etc/apt/sources.list'
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "bash", "-c", cmd],
                capture_output=True,
                text=True,
                check=True,
            )

            # Update apt cache
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "apt", "update"],
                capture_output=True,
                check=True,
            )

            success("Repositories configured")
            return True

        except subprocess.CalledProcessError as e:
            warning("Failed to configure repositories")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return True  # Non-critical, continue
        except FileNotFoundError:
            console.print(
                "[yellow]Warning:[/] Required commands not found for repository configuration"
            )
            return True  # Non-critical, continue
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            warning(str(e))
            return True  # Non-critical

    def _enable_i386(self, chroot_name: str, dry_run: bool) -> bool:
        """Enable i386 architecture for 32-bit Wine support.

        Args:
            chroot_name: Schroot name
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(8, "Enabling i386 architecture...")

        if dry_run:
            console.print("[dim]Would run: dpkg --add-architecture i386[/]")
            return True

        try:
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "dpkg", "--add-architecture", "i386"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Update apt cache
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "apt", "update"],
                capture_output=True,
                check=True,
            )

            success("i386 architecture enabled")
            return True

        except subprocess.CalledProcessError as e:
            warning("Failed to add i386 architecture")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return True  # Non-critical, continue
        except FileNotFoundError:
            warning("Required commands not found for i386 configuration")
            return True  # Non-critical, continue
        except (PermissionError, OSError) as e:
            warning(str(e))
            return True  # Non-critical

    def _install_wine(self, chroot_name: str, dry_run: bool) -> bool:
        """Install Wine inside the chroot.

        Args:
            chroot_name: Schroot name
            dry_run: Dry run mode

        Returns:
            True if successful
        """
        console.print()
        step(9, "Installing Wine (this may take a while)...")

        if dry_run:
            console.print("[dim]Would install: wine wine32 wine64 wine-binfmt fonts-wine[/]")
            return True

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing Wine packages...", total=None)

                subprocess.run(
                    [
                        "sudo",
                        "schroot",
                        "-c",
                        chroot_name,
                        "--",
                        "apt",
                        "install",
                        "-y",
                        "--install-recommends",
                        "wine",
                        "wine32",
                        "wine64",
                        "wine-binfmt",
                        "fonts-wine",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes max
                    check=True,
                )

                progress.update(task, completed=True)

            success("Wine installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            error("Wine installation failed")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return False
        except subprocess.TimeoutExpired:
            error("Wine installation timed out")
            return False
        except FileNotFoundError:
            error("Required commands not found for Wine installation")
            return False
        except PermissionError:
            error(
                "Permission denied installing Wine", hint="This operation requires root privileges"
            )
            return False
        except OSError as e:
            error(
                f"System error installing Wine: {e}",
                hint="Check disk space and filesystem availability",
            )
            return False

    def _verify_installation(self, chroot_name: str) -> bool:
        """Verify the chroot installation.

        Args:
            chroot_name: Schroot name

        Returns:
            True if verification passed
        """
        console.print()
        step(10, "Verifying installation...")

        try:
            # Check if we can enter the chroot
            subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "echo", "test"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

            # Check Wine version
            result = subprocess.run(
                ["sudo", "schroot", "-c", chroot_name, "--", "wine", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            version = result.stdout.strip()
            console.print(f"[green]✓[/] Wine version: {version}")
            return True

        except subprocess.CalledProcessError as e:
            warning("Verification failed - command returned error")
            if self.verbose and e.stderr:
                console.print(f"[dim]{e.stderr}[/]")
            return False
        except subprocess.TimeoutExpired:
            warning("Verification timed out")
            return False
        except FileNotFoundError:
            warning("Required commands not found for verification")
            return False
        except PermissionError:
            warning("Permission denied during verification")
            return False
        except AttributeError:
            warning("Unexpected output format from Wine version check")
            return False
        except OSError as e:
            warning(f"System error during verification: {e}")
            return False
