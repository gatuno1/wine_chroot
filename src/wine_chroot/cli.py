#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Command-line interface for wine-chroot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich_argparse import RichHelpFormatter

from . import __version__
from .chroot import ChrootManager
from .config import Config, create_example_config
from .desktop import DesktopManager
from .runner import WineRunner
from .utils import check_system_dependencies, validate_exe_path

console = Console()


def cmd_run(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'run' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    exe_path = Path(args.exe).expanduser()

    # Validate path
    if not validate_exe_path(exe_path, config.chroot_path):
        return 1

    # Run application
    runner = WineRunner(config, verbose=args.verbose)

    # Check Wine installation first
    if not runner.check_wine_installation():
        console.print(
            "[bold red]Error:[/] Wine is not installed in the chroot",
        )
        console.print(
            f"Run: wine-chroot init --name {config.chroot_name}",
        )
        return 1

    return runner.run(
        exe_path,
        args=args.args if hasattr(args, "args") else None,
        wait=args.wait,
        show_terminal=args.terminal,
    )


def cmd_desktop(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'desktop' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    exe_path = Path(args.exe).expanduser()

    manager = DesktopManager(config, verbose=args.verbose)

    try:
        manager.create_launcher(
            exe_path=exe_path,
            app_name=args.name,
            extract_icon_flag=args.icon,
            desktop_filename=args.desktop,
        )
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_list(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'list' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    manager = DesktopManager(config, verbose=args.verbose)

    if args.launchers:
        # List .desktop files
        launchers = manager.list_desktop_files()

        if not launchers:
            console.print("[yellow]No Wine launchers found[/]")
            return 0

        table = Table(title="Wine Launchers")
        table.add_column("Application", style="cyan")
        table.add_column("Desktop File", style="dim")

        for app_name, desktop_file in launchers:
            table.add_row(app_name, str(desktop_file))

        console.print(table)

    else:
        # List applications in chroot
        console.print("[cyan]Scanning chroot for Windows applications...[/]")
        applications = manager.list_wine_applications()

        if not applications:
            console.print(
                "[yellow]No Windows applications found in chroot[/]",
            )
            return 0

        table = Table(title="Windows Applications")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="dim")
        table.add_column("Launcher", style="green")

        for app in applications:
            launcher_status = "✓" if app["has_desktop"] else "✗"
            table.add_row(
                app["name"],
                str(app["path"]),
                launcher_status,
            )

        console.print(table)

        # Show summary
        total = len(applications)
        with_launchers = sum(1 for app in applications if app["has_desktop"])
        console.print()
        console.print(
            f"Found {total} applications, {with_launchers} with launchers",
        )

    return 0


def cmd_config(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'config' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    if args.show:
        # Show current configuration
        console.print("[cyan]Current Configuration:[/]")
        console.print()

        table = Table(show_header=False)
        table.add_column("Key", style="yellow")
        table.add_column("Value", style="white")

        # Flatten config for display
        def add_rows(data: dict, prefix: str = ""):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    add_rows(value, full_key)
                else:
                    table.add_row(full_key, str(value))

        add_rows(config.data)
        console.print(table)

        if config.config_path:
            console.print()
            console.print(f"[dim]Loaded from: {config.config_path}[/]")
        else:
            console.print()
            console.print("[dim]Using default configuration[/]")

    elif args.init:
        # Create example configuration
        output_path = Path(args.output) if args.output else Config.DEFAULT_CONFIG_PATHS[0]
        create_example_config(output_path)

    return 0


def cmd_init(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'init' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    manager = ChrootManager(config, verbose=args.verbose)

    # Show confirmation if not in dry-run mode
    if not args.dry_run:
        chroot_path = Path(args.path) if args.path else config.chroot_path

        console.print("\n[bold yellow]⚠ Warning:[/] This will create a new chroot environment")
        console.print(f"Installation path: [cyan]{chroot_path}[/]")
        console.print("\nThis operation will:")
        console.print("  • Download ~200-500 MB of Debian packages")
        console.print("  • Require root access (sudo)")
        console.print("  • Take 10-30 minutes depending on your internet connection")
        console.print()

        response = input("Continue? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            console.print("\n[yellow]Cancelled by user[/]")
            return 1

    # Run initialization
    success = manager.initialize(
        chroot_name=args.name if args.name else None,
        chroot_path=Path(args.path) if args.path else None,
        debian_version=args.debian_version,
        skip_wine=args.skip_wine,
        dry_run=args.dry_run,
    )

    return 0 if success else 1


def cmd_version(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'version' command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Returns:
        Exit code
    """
    console.print(f"wine-chroot version {__version__}")

    # Show Wine version if available
    runner = WineRunner(config, verbose=args.verbose)
    wine_version = runner.get_wine_version()
    if wine_version:
        console.print(f"Wine in chroot: {wine_version}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="wine-chroot",
        description=("Manage Windows applications on ARM64 Linux using Wine in a chroot"),
        epilog=(
            "Use '[argparse.prog]wine-chroot[/] [argparse.args]<command> --help'[/] for more "
            "information on a specific command."
        ),
        formatter_class=RichHelpFormatter,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to '[argparse.default]wine-chroot.toml[/]' configuration file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        metavar="<command>",
    )

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new chroot environment",
        description=(
            "[i]command:[/i] [argparse.args]init[/] - "
            "Create and configure a new Debian amd64 chroot with Wine installed. "
            "This automates debootstrap, schroot configuration, and Wine setup."
        ),
        formatter_class=RichHelpFormatter,
    )
    init_parser.add_argument(
        "-n",
        "--name",
        help="Chroot name (default: from config)",
    )
    init_parser.add_argument(
        "-p",
        "--path",
        type=Path,
        help=(
            "Chroot installation path (default: from config)"
        ),
    )
    init_parser.add_argument(
        "--debian-version",
        default="trixie",
        help="Debian version to install (default: [argparse.default]trixie[/])",
    )
    init_parser.add_argument(
        "--skip-wine",
        action="store_true",
        help="Don't install Wine automatically",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run a Windows application",
        description=(
            "[i]command:[/i] [argparse.args]run[/] - "
            "Execute a Windows application inside the chroot using Wine"
        ),
        formatter_class=RichHelpFormatter,
    )
    run_parser.add_argument(
        "exe",
        help="Path to .exe file (Windows or Linux format)",
    )
    run_parser.add_argument(
        "args",
        nargs="*",
        help="Arguments to pass to the application",
    )
    run_parser.add_argument(
        "-w",
        "--wait",
        action="store_true",
        help="Wait for application to exit",
    )
    run_parser.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help="Show terminal output",
    )

    # desktop command
    desktop_parser = subparsers.add_parser(
        "desktop",
        help="Create a .desktop launcher",
        description=(
            "[i]command:[/i] [argparse.args]desktop[/] - "
            "Create a .desktop launcher file for easy application menu access. "
            "Optionally extracts icons from Windows executables."
        ),
        formatter_class=RichHelpFormatter,
    )
    desktop_parser.add_argument(
        "-e",
        "--exe",
        required=True,
        help="Path to .exe file",
    )
    desktop_parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Application name for the menu",
    )
    desktop_parser.add_argument(
        "-i",
        "--icon",
        action="store_true",
        help="Extract icon from .exe",
    )
    desktop_parser.add_argument(
        "-d",
        "--desktop",
        help="Custom [green].desktop[/] launcher filename",
    )

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List applications or launchers",
        description=(
            "[i]command:[/i] [argparse.args]list[/] - "
            "List installed Windows applications in the chroot or existing "
            "[green].desktop[/] launchers"
        ),
        formatter_class=RichHelpFormatter,
    )
    list_parser.add_argument(
        "-l",
        "--launchers",
        action="store_true",
        help="List only [green].desktop[/] launchers",
    )

    # config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
        description=(
            "[i]command:[/i] [argparse.args]config[/] - "
            "Display current configuration settings or create an example "
            "[argparse.default]'wine-chroot.toml'[/] configuration file"
        ),
        formatter_class=RichHelpFormatter,
    )
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Show current configuration",
    )
    config_group.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Create example configuration file",
    )
    config_parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output path for --init "
            "(default: [argparse.default]'~/.config/wine-chroot.toml'[/])"
        ),
    )

    return parser


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = build_parser()
    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        console.print(f"wine-chroot version {__version__}")
        return 0

    # Require a command
    if not args.command:
        parser.print_help()
        return 1

    # Check system dependencies
    if args.verbose:
        console.print("[cyan]Checking system dependencies...[/]")
        all_ok, missing = check_system_dependencies(verbose=True)
        if not all_ok:
            console.print()
            console.print("[yellow]Some dependencies are missing:[/]")
            for cmd in missing:
                console.print(f"  - {cmd}")
            console.print()
            console.print("Install with:")
            console.print("  sudo apt install schroot debootstrap qemu-user-static icoutils")
            console.print()

    # Load configuration
    config = Config(args.config if hasattr(args, "config") else None)

    # Dispatch to command handler
    commands = {
        "run": cmd_run,
        "desktop": cmd_desktop,
        "list": cmd_list,
        "config": cmd_config,
        "init": cmd_init,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if not handler:
        console.print(f"[bold red]Error:[/] Unknown command: {args.command}")
        return 1

    try:
        return handler(args, config)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/]")
        return 130
    except Exception as e:
        if args.verbose:
            console.print_exception()
        else:
            console.print(f"[bold red]Error:[/] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
