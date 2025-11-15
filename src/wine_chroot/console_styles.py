#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Standardized console styles for wine-chroot.

This module provides consistent styling for console output across the project.
All modules should use these styles instead of hardcoding markup.
"""

from __future__ import annotations

from rich.console import Console

# Global console instance for the entire project
console = Console()


# Message Types
class Style:
    """Standard Rich markup styles for console messages."""

    # Status messages
    SUCCESS = "[bold green]✓[/bold green]"
    ERROR = "[bold red]Error:[/bold red]"
    WARNING = "[bold yellow]Warning:[/bold yellow]"
    INFO = "[cyan]ℹ[/cyan]"

    # Text emphasis
    BOLD = "bold"
    DIM = "dim"
    ITALIC = "italic"

    # Colors for content
    CYAN = "cyan"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    MAGENTA = "magenta"

    # Semantic colors
    PATH = "cyan"
    FILE = "green"
    COMMAND = "yellow"
    VALUE = "yellow"
    HIGHLIGHT = "bold cyan"


def success(message: str) -> None:
    """Print a success message with green checkmark.

    Args:
        message: The success message to display

    Example:
        >>> success("Installation completed")
        ✓ Installation completed
    """
    console.print(f"{Style.SUCCESS} {message}")


def error(message: str, hint: str | None = None) -> None:
    """Print an error message with red styling.

    Args:
        message: The error message to display
        hint: Optional hint to help the user resolve the error

    Example:
        >>> error("File not found", hint="Check the path and try again")
        Error: File not found
        Hint: Check the path and try again
    """
    console.print(f"{Style.ERROR} {message}")
    if hint:
        console.print(f"[yellow]Hint:[/yellow] {hint}")


def warning(message: str, hint: str | None = None) -> None:
    """Print a warning message with yellow styling.

    Args:
        message: The warning message to display
        hint: Optional hint to help the user resolve the warning

    Example:
        >>> warning("This operation may take a while")
        Warning: This operation may take a while
        >>> warning("Tool not found", hint="Install with: sudo apt install tool")
        Warning: Tool not found
        Hint: Install with: sudo apt install tool
    """
    console.print(f"{Style.WARNING} {message}")
    if hint:
        console.print(f"[yellow]Hint:[/yellow] {hint}")


def info(message: str) -> None:
    """Print an informational message with cyan styling.

    Args:
        message: The information message to display

    Example:
        >>> info("Checking system dependencies...")
        ℹ Checking system dependencies...
    """
    console.print(f"[{Style.CYAN}]{message}[/{Style.CYAN}]")


def step(number: int, message: str) -> None:
    """Print a numbered step message for multi-step operations.

    Args:
        number: The step number
        message: The step description

    Example:
        >>> step(1, "Checking prerequisites...")
        1. Checking prerequisites...
        >>> step(2, "Creating base system...")
        2. Creating base system...
    """
    console.print(f"[{Style.CYAN}]{number}.[/{Style.CYAN}] {message}")


def command(cmd: str) -> None:
    """Print a command that will be or was executed.

    Args:
        cmd: The command string

    Example:
        >>> command("sudo apt install wine")
        $ sudo apt install wine
    """
    console.print(f"[{Style.DIM}]$ {cmd}[/{Style.DIM}]")


def path(p: str) -> str:
    """Format a filesystem path.

    Args:
        p: The path to format

    Returns:
        Formatted path with cyan color

    Example:
        >>> console.print(f"Installing to {path('/srv/debian-amd64')}")
        Installing to /srv/debian-amd64
    """
    return f"[{Style.PATH}]{p}[/{Style.PATH}]"


def file(f: str) -> str:
    """Format a filename.

    Args:
        f: The filename to format

    Returns:
        Formatted filename with green color

    Example:
        >>> console.print(f"Created {file('wine-chroot.toml')}")
        Created wine-chroot.toml
    """
    return f"[{Style.FILE}]{f}[/{Style.FILE}]"


def value(v: str) -> str:
    """Format a configuration value or default.

    Args:
        v: The value to format

    Returns:
        Formatted value with yellow color

    Example:
        >>> console.print(f"Using default: {value('debian-amd64')}")
        Using default: debian-amd64
    """
    return f"[{Style.VALUE}]{v}[/{Style.VALUE}]"


def highlight(text: str) -> str:
    """Highlight important text.

    Args:
        text: The text to highlight

    Returns:
        Formatted text with bold cyan

    Example:
        >>> console.print(f"Running {highlight('Wine')} in chroot")
        Running Wine in chroot
    """
    return f"[{Style.HIGHLIGHT}]{text}[/{Style.HIGHLIGHT}]"


# Legacy compatibility - these will be deprecated
def print_success(message: str) -> None:
    """Deprecated: Use success() instead."""
    success(message)


def print_error(message: str, hint: str | None = None) -> None:
    """Deprecated: Use error() instead."""
    error(message, hint)


def print_warning(message: str, hint: str | None = None) -> None:
    """Deprecated: Use warning() instead."""
    warning(message, hint)


def print_info(message: str) -> None:
    """Deprecated: Use info() instead."""
    info(message)
