#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
#
# make_wine_chroot_desktop.sh
#
# Generate a .desktop launcher that runs a Windows .exe with Wine inside a schroot.
# The script runs on the host and creates shortcuts that launch applications
# inside the chroot environment where Wine is installed.
#
# Use cases:
# - Run Windows x86/amd64 applications on ARM64 hosts using a Debian amd64 schroot
# - Isolate Wine applications in dedicated chroot environments
#
# Usage:
#   ./make_wine_chroot_desktop.sh --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/WlkataStudio/WlkataStudio.exe" \
#       --name "Wlkata Studio (Wine chroot)" --icon
#
# Options:
#   --exe PATH        -> Path to the .exe as seen from the host inside the schroot tree (required)
#   --name NAME       -> Name that will appear in the desktop menu (required)
#   --desktop FILE    -> Name of the .desktop file (defaults to a derived slug)
#   --icon            -> Attempt to extract the .exe icon using wrestool + icotool
#   --schroot NAME    -> Name of the schroot to use (default: debian-amd64)
#
# Requirements:
# - Host: schroot, icoutils (wrestool, icotool)
# - Chroot: Wine installed and configured
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any later version.

set -e
set -u

SCHROOT_NAME="debian-amd64"
EXE_PATH=""
APP_NAME=""
DESKTOP_NAME=""
DO_ICON=false

show_help() {
        cat << EOF
Usage: $(basename "$0") --exe EXE --name NAME [--desktop DESKTOP] [--icon] [--schroot SCHROOT]

Generate a .desktop launcher that runs an .exe with Wine inside a schroot.

Required arguments:
    --exe EXE          Path to the .exe as seen from the host inside the schroot tree
    --name NAME        Name that will appear in the desktop menu

Optional arguments:
    --desktop DESKTOP  Name of the .desktop file (defaults to a derived slug)
    --icon             Attempt to extract the .exe icon using wrestool + icotool
    --schroot SCHROOT  Name of the schroot to use (default: debian-amd64)
    -h, --help         Show this help message

EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --exe)
            EXE_PATH="$2"
            shift 2
            ;;
        --name)
            APP_NAME="$2"
            shift 2
            ;;
        --desktop)
            DESKTOP_NAME="$2"
            shift 2
            ;;
        --icon)
            DO_ICON=true
            shift 1
            ;;
        --schroot)
            SCHROOT_NAME="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option: $1"
            echo "Use --help to list the available options."
            exit 1
            ;;
    esac
done

if [[ -z "$EXE_PATH" ]]; then
    echo "Error: Missing required argument --exe"
    echo "Usage: $(basename "$0") --exe EXE --name NAME"
    echo "Use --help for more information."
    exit 1
fi

if [[ -z "$APP_NAME" ]]; then
    echo "Error: Missing required argument --name"
    echo "Usage: $(basename "$0") --exe EXE --name NAME"
    echo "Use --help for more information."
    exit 1
fi

# Ensure the .exe file exists
if [[ ! -f "$EXE_PATH" ]]; then
    echo "[!] The .exe does not exist at this path: $EXE_PATH"
    echo "    Remember that it must be the path as seen from the host, e.g."
    echo "    /srv/debian-amd64/root/.wine/drive_c/Program Files/..."
    exit 1
fi

# Determine the .desktop filename
if [[ -z "$DESKTOP_NAME" ]]; then
    # Convert the name into a safe filename (similar to Python: re.sub(r"[^a-z0-9]+", "-", ...))
    DESKTOP_NAME="$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/^-//;s/-$//')".desktop
fi

DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

# Convert the Linux path of the exe to a Windows path (C:\...)
# If the path contains 'drive_c/', convert it to C:\... with backslashes.
# If it is already in C:\... format, leave it untouched.
WIN_EXE_PATH=""
if [[ "$EXE_PATH" =~ ^[A-Za-z]:\\ ]]; then
    # Already in Windows format
    WIN_EXE_PATH="$EXE_PATH"
elif [[ "$EXE_PATH" == *"drive_c/"* ]]; then
    # Extract the portion after drive_c/
    AFTER_DRIVE=$(echo "$EXE_PATH" | sed 's#.*drive_c/##')
    # Replace / with \
    AFTER_DRIVE_WIN=$(echo "$AFTER_DRIVE" | sed 's#/#\\#g')
    WIN_EXE_PATH="C:\\$AFTER_DRIVE_WIN"
else
    # Fallback: return the original path (Wine handles Unix paths)
    WIN_EXE_PATH="$EXE_PATH"
fi

# Optional icon extraction
ICON_PATH=""
if $DO_ICON; then
    DESKTOP_BASENAME="$(basename "$DESKTOP_NAME" .desktop)"
    ICON_PATH="$ICON_DIR/${DESKTOP_BASENAME}.png"
    TMP_ICO="/tmp/${DESKTOP_BASENAME}.ico"
    TMP_PNG_DIR="/tmp/icoextract_bash"
    
    echo "[*] Extracting icon from $EXE_PATH ..."
    
    # Step 1: wrestool - extract the .ico from the .exe
    if sudo wrestool -x -t14 "$EXE_PATH" -o "$TMP_ICO" 2>/dev/null; then
        if [[ -f "$TMP_ICO" ]]; then
            # Step 2: icotool - convert .ico to .png
            mkdir -p "$TMP_PNG_DIR"
            if icotool -x "$TMP_ICO" -o "$TMP_PNG_DIR" 2>/dev/null; then
                # Choose the largest PNG (often the last one in alphabetical order)
                CHOSEN_PNG=$(ls -1 "$TMP_PNG_DIR"/*.png 2>/dev/null | sort | tail -n 1 || true)
                if [[ -n "$CHOSEN_PNG" ]]; then
                    cp "$CHOSEN_PNG" "$ICON_PATH"
                    echo "[*] Icon copied to $ICON_PATH"
                else
                    echo "[!] No extracted PNGs were found"
                    ICON_PATH=""
                fi
            else
                echo "[!] Failed to convert .ico to .png"
                ICON_PATH=""
            fi
        else
            echo "[!] wrestool did not produce an .ico"
            ICON_PATH=""
        fi
    else
        echo "[!] Failed to extract .ico with wrestool"
        ICON_PATH=""
    fi
fi

DESKTOP_FILE="$DESKTOP_DIR/$DESKTOP_NAME"

# .desktop contents
{
    echo "[Desktop Entry]"
    echo "Name=$APP_NAME"
    echo "Comment=Run $APP_NAME inside the $SCHROOT_NAME schroot"
    echo "Exec=sudo schroot -c $SCHROOT_NAME -- wine \"$WIN_EXE_PATH\""
    echo "Type=Application"
    echo "Categories=Wine;WindowsApps;"
    echo "StartupNotify=true"
    echo "Terminal=false"
    echo "StartupWMClass=$(basename "$WIN_EXE_PATH")"
    if [[ -n "$ICON_PATH" ]]; then
        echo "Icon=$ICON_PATH"
    fi
} > "$DESKTOP_FILE"

echo "[*] .desktop created at: $DESKTOP_FILE"

# Attempt to refresh the desktop database
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "[OK] Done."
echo "Look for '$APP_NAME' in your desktop menu."
echo "If sudo prompts for a password, add a sudoers entry such as:"
echo "    YOURUSER ALL=(ALL) NOPASSWD: /usr/bin/schroot"

echo "[*] Access created at: $DESKTOP_FILE"
echo "[*] Refreshing desktop database..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "Done. You should see '$APP_NAME' in the menu (Wine category)."
echo "If it prompts for a password when launching, add to sudoers:"
echo "    YOURUSER ALL=(ALL) NOPASSWD: /usr/bin/schroot"
