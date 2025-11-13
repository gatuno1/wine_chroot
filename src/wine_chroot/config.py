#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Configuration management for wine-chroot using TOML."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from rich.console import Console

# Use tomllib (Python 3.11+) or tomli (fallback)
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore

console = Console()


class Config:
    """Configuration manager for wine-chroot."""

    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".config" / "wine-chroot.toml",
        Path.home() / ".wine-chroot.toml",
        Path("wine-chroot.toml"),
    ]

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Explicit path to config file, or None to search defaults
        """
        self.config_path: Path | None = None
        self.data: dict[str, Any] = {}

        if config_path:
            self.config_path = config_path
            if not self.config_path.exists():
                console.print(
                    f"[yellow]Warning:[/] Config file not found: {config_path}",
                )
                console.print("Using default configuration")
        else:
            # Search for config in default locations
            for path in self.DEFAULT_CONFIG_PATHS:
                if path.exists():
                    self.config_path = path
                    break

        # Load config if found
        if self.config_path and self.config_path.exists():
            self.load()
        else:
            self._set_defaults()

    def load(self) -> None:
        """Load configuration from TOML file."""
        if not self.config_path:
            self._set_defaults()
            return

        if tomllib is None:
            console.print(
                "[bold red]Error:[/] TOML parser not available",
            )
            console.print("Install tomli: uv pip install tomli")
            raise SystemExit(1)

        try:
            with open(self.config_path, "rb") as f:
                self.data = tomllib.load(f)
            console.print(
                f"[dim]Loaded configuration from {self.config_path}[/]",
                highlight=False,
            )
        except Exception as e:
            console.print(
                f"[bold red]Error:[/] Failed to load config: {e}",
            )
            self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default configuration values."""
        self.data = {
            "chroot": {
                "name": "debian-amd64",
                "path": "/srv/debian-amd64",
                "architecture": "amd64",
                "debian_version": "trixie",
            },
            "wine": {
                "prefix": "/root/.wine",
                "enable_i386": True,
            },
            "desktop": {
                "icon_dir": str(Path.home() / ".local" / "share" / "icons"),
                "applications_dir": str(Path.home() / ".local" / "share" / "applications"),
                "categories": ["Wine", "WindowsApps"],
            },
            "execution": {
                "use_pkexec": False,  # sudo is more reliable than pkexec
                "preserve_environment": True,
                "x11_forwarding": True,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "chroot.name")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "chroot.name")
            value: Value to set
        """
        keys = key.split(".")
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def save(self, path: Path | None = None) -> None:
        """Save configuration to TOML file.

        Args:
            path: Path to save to, or None to use current config_path
        """
        save_path = path or self.config_path
        if not save_path:
            save_path = self.DEFAULT_CONFIG_PATHS[0]

        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # We need to write TOML manually or use a library like tomli-w
            # For simplicity, we'll generate it manually
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("# Wine Chroot Configuration\n\n")
                self._write_section(f, self.data)

            console.print(f"[green]Configuration saved to {save_path}[/]")
            self.config_path = save_path

        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to save config: {e}")

    def _write_section(self, f, data: dict, parent_key: str = "") -> None:
        """Recursively write TOML sections.

        Args:
            f: File object
            data: Dictionary to write
            parent_key: Parent section key for nested sections
        """
        # Write simple key-value pairs first
        for key, value in data.items():
            if not isinstance(value, dict):
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                elif isinstance(value, bool):
                    f.write(f"{key} = {str(value).lower()}\n")
                elif isinstance(value, list):
                    # Format lists
                    items = ", ".join(
                        f'"{item}"' if isinstance(item, str) else str(item) for item in value
                    )
                    f.write(f"{key} = [{items}]\n")
                else:
                    f.write(f"{key} = {value}\n")

        # Write nested sections
        for key, value in data.items():
            if isinstance(value, dict):
                section_key = f"{parent_key}.{key}" if parent_key else key
                f.write(f"\n[{section_key}]\n")
                # Write nested content (only direct values, not sub-dicts)
                for subkey, subvalue in value.items():
                    if not isinstance(subvalue, dict):
                        if isinstance(subvalue, str):
                            f.write(f'{subkey} = "{subvalue}"\n')
                        elif isinstance(subvalue, bool):
                            f.write(f"{subkey} = {str(subvalue).lower()}\n")
                        elif isinstance(subvalue, list):
                            items = ", ".join(
                                f'"{item}"' if isinstance(item, str) else str(item)
                                for item in subvalue
                            )
                            f.write(f"{subkey} = [{items}]\n")
                        else:
                            f.write(f"{subkey} = {subvalue}\n")

    @property
    def chroot_name(self) -> str:
        """Get chroot name."""
        return self.get("chroot.name", "debian-amd64")

    @property
    def chroot_path(self) -> Path:
        """Get chroot path as Path object."""
        return Path(self.get("chroot.path", "/srv/debian-amd64"))

    @property
    def wine_prefix(self) -> str:
        """Get Wine prefix path."""
        return self.get("wine.prefix", "/root/.wine")

    @property
    def use_pkexec(self) -> bool:
        """Get whether to use pkexec (True) or sudo (False)."""
        return self.get("execution.use_pkexec", False)

    @property
    def applications_dir(self) -> Path:
        """Get applications directory as Path object."""
        return Path(
            self.get(
                "desktop.applications_dir",
                str(Path.home() / ".local" / "share" / "applications"),
            )
        )

    @property
    def icon_dir(self) -> Path:
        """Get icon directory as Path object."""
        return Path(
            self.get(
                "desktop.icon_dir",
                str(Path.home() / ".local" / "share" / "icons"),
            )
        )


def create_example_config(output_path: Path) -> None:
    """Create an example configuration file.

    Args:
        output_path: Path where to create the example config
    """
    example = """# Wine Chroot Configuration
# This file configures the wine-chroot tool

[chroot]
name = "debian-amd64"
path = "/srv/debian-amd64"
architecture = "amd64"
debian_version = "trixie"

[wine]
prefix = "/root/.wine"  # Path inside chroot
enable_i386 = true

[desktop]
icon_dir = "~/.local/share/icons"
applications_dir = "~/.local/share/applications"
categories = ["Wine", "WindowsApps"]

[execution]
use_pkexec = false  # false = sudo (recommended), true = pkexec
preserve_environment = true
x11_forwarding = true

# Optional: pre-configured applications
# [[applications]]
# name = "Notepad++"
# exe = "C:\\\\Program Files\\\\Notepad++\\\\notepad++.exe"
# icon = "~/.local/share/icons/notepad-plus-plus.png"
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(example)

    console.print(f"[green]Created example configuration at {output_path}[/]")
