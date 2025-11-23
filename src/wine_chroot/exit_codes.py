#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""Exit codes for wine-chroot commands."""

# Success
SUCCESS = 0

# General errors (1-9)
GENERAL_ERROR = 1
INVALID_ARGUMENTS = 2
PERMISSION_DENIED = 3
FILE_NOT_FOUND = 4

# Configuration errors (10-19)
CONFIG_ERROR = 10
CONFIG_NOT_FOUND = 11
CONFIG_INVALID = 12

# Chroot errors (20-29)
CHROOT_ERROR = 20
CHROOT_NOT_FOUND = 21
CHROOT_ALREADY_EXISTS = 22
CHROOT_CREATION_FAILED = 23

# Wine errors (30-39)
WINE_ERROR = 30
WINE_NOT_INSTALLED = 31
WINE_EXECUTION_FAILED = 32

# Application errors (40-49)
APP_ERROR = 40
APP_NOT_FOUND = 41
APP_EXECUTION_FAILED = 42

# Desktop integration errors (50-59)
DESKTOP_ERROR = 50
DESKTOP_FILE_CREATION_FAILED = 51
ICON_EXTRACTION_FAILED = 52

# System errors (60-69)
SYSTEM_ERROR = 60
MISSING_DEPENDENCIES = 61
SYSTEM_COMMAND_FAILED = 62

# User interruption
USER_INTERRUPTED = 130


def get_error_message(exit_code: int) -> str:
    """Get a human-readable error message for an exit code.

    Args:
        exit_code: The exit code to describe

    Returns:
        A human-readable description of the error
    """
    messages = {
        SUCCESS: "Success",
        GENERAL_ERROR: "General error",
        INVALID_ARGUMENTS: "Invalid arguments",
        PERMISSION_DENIED: "Permission denied",
        FILE_NOT_FOUND: "File not found",
        CONFIG_ERROR: "Configuration error",
        CONFIG_NOT_FOUND: "Configuration file not found",
        CONFIG_INVALID: "Invalid configuration",
        CHROOT_ERROR: "Chroot error",
        CHROOT_NOT_FOUND: "Chroot not found",
        CHROOT_ALREADY_EXISTS: "Chroot already exists",
        CHROOT_CREATION_FAILED: "Chroot creation failed",
        WINE_ERROR: "Wine error",
        WINE_NOT_INSTALLED: "Wine not installed",
        WINE_EXECUTION_FAILED: "Wine execution failed",
        APP_ERROR: "Application error",
        APP_NOT_FOUND: "Application not found",
        APP_EXECUTION_FAILED: "Application execution failed",
        DESKTOP_ERROR: "Desktop integration error",
        DESKTOP_FILE_CREATION_FAILED: "Desktop file creation failed",
        ICON_EXTRACTION_FAILED: "Icon extraction failed",
        SYSTEM_ERROR: "System error",
        MISSING_DEPENDENCIES: "Missing system dependencies",
        SYSTEM_COMMAND_FAILED: "System command failed",
        USER_INTERRUPTED: "User interrupted",
    }
    return messages.get(exit_code, f"Unknown error (code {exit_code})")
