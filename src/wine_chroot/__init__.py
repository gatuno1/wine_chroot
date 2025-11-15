#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Wine Chroot - Run Windows applications on ARM64 Linux.

This package provides tools to execute Windows amd64 applications on ARM64
hardware using Wine within a Debian chroot environment.

Features:
- Automated chroot initialization with wine-chroot init
- Wine execution wrapper for running Windows applications
- Desktop integration with .desktop launcher creation
- Icon extraction from Windows executables
- TOML-based configuration management
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Wine Chroot Contributors"
__license__ = "GPL-3.0-or-later"

# Export standardized console utilities for internal use
from .console_styles import (
    Style,
    command,
    console,
    error,
    file,
    highlight,
    info,
    path,
    step,
    success,
    value,
    warning,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "console",
    "success",
    "error",
    "warning",
    "info",
    "step",
    "command",
    "path",
    "file",
    "value",
    "highlight",
    "Style",
]
