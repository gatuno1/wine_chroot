# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wine Chroot enables running Windows amd64 applications on ARM64 Linux systems using Wine within a Debian chroot environment. The project uses schroot + qemu-user-static for cross-architecture execution.

**Current Status**: Bash script implementation focusing on desktop integration and launcher scripts.

## Architecture

```text
┌──────────────────────────────────────────────────────┐
│  Host System (Debian ARM64)                          │
│                                                      │
│  ┌──────────────────────────────────────────┐        │
│  │  run-chroot.sh                           │        │
│  │  - Handles X11 integration               │        │
│  │  - Manages environment variables         │        │
│  │  - Creates runtime directories           │        │
│  └──────────────────────────────────────────┘        │
│                    ↓                                 │
│  ┌──────────────────────────────────────────┐        │
│  │  schroot + qemu-user-static              │        │
│  │  (ARM64 → AMD64 translation)             │        │
│  └──────────────────────────────────────────┘        │
│                    ↓                                 │
│  ┌──────────────────────────────────────────┐        │
│  │  Chroot Environment (Debian AMD64)       │        │
│  │  - Wine x64 + Wine x86 (i386 + amd64)    │        │
│  │  - Windows applications                  │        │
│  │  - Shared /home, /dev, /proc, X11 socket │        │
│  └──────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

**Key Concepts:**

1. **Host-side scripts** (in `src/`) run on the ARM64 host
2. **Chroot environment** contains Debian AMD64 with Wine installed
3. **schroot** manages sessions and bind-mounts
4. **qemu-user-static** provides transparent AMD64 emulation
5. **X11 forwarding** enables GUI applications from inside chroot

## Project Structure

```asciiart
wine_chroot/
├── src/
│   ├── run-chroot.sh        # Main launcher script (v1)
│   └── run-chroot-v2.sh     # Simplified launcher script (v2) ⭐ RECOMMENDED
├── docs/
│   ├── chroot-setup_es.md    # Complete setup guide (Spanish) - v1
│   ├── chroot-setup-v2_es.md # Simplified setup guide (Spanish) - v2 ⭐
│   └── COMPARISON-v1-vs-v2.md # Detailed comparison
├── pyproject.toml            # Project metadata
├── LICENSE                   # GPL-3.0-or-later
└── CLAUDE.md                 # This file
```

## Core Scripts

### ⭐ run-chroot-v2.sh (RECOMMENDED)

**Version 2 - Simplified approach using `preserve-environment=true`**

**Purpose**: Execute commands inside the chroot with automatic environment inheritance.

**Key Features:**

- **40% less code** than v1 (12 vs 20 lines of executable code)
- DISPLAY and XAUTHORITY **inherited automatically** from host (no manual configuration)
- Only configures XDG_RUNTIME_DIR and WINEPREFIX
- Simpler and more maintainable
- Requires `preserve-environment=true` in schroot config

**When to use v2:**
- ✅ Personal use / development environments
- ✅ When simplicity is a priority
- ✅ Single-user desktop setups
- ✅ You trust the host environment

### run-chroot.sh (v1)

**Version 1 - Full control approach using `preserve-environment=false`**

**Purpose**: Execute commands inside the chroot with manual environment configuration.

**Key Features:**

- **Full control** over all environment variables
- Derives user-specific variables (UID, GID, HOME) from `$USER` parameter, not from the executing process
- Manually configures X11 integration (DISPLAY, XAUTHORITY)
- Sets up XDG_RUNTIME_DIR to `/tmp/runtime-$USER` for Qt/KDE applications
- Creates runtime directory in `/tmp` (avoiding ownership issues with `/run/user/$UID` in schroot)
- Works with `preserve-environment=false` (default schroot behavior)

**When to use v1:**
- ⚙️ Multi-user environments with strict security requirements
- ⚙️ When you need full control over what gets exposed to the chroot
- ⚙️ Production environments where predictability is critical
- ⚙️ When you don't trust the host environment

**Critical Implementation Detail:**

```bash
# IMPORTANT: Get target user info, not current process info
USER="${USER:-$(whoami)}"
TARGET_UID=$(id -u "$USER")      # Not $UID
TARGET_GID=$(id -g "$USER")      # Not $(id -g)
TARGET_HOME=$(getent passwd "$USER" | cut -d: -f6)  # Not $HOME
```

This ensures that when executed via `sudo USER=actual_user ./run-chroot.sh`, all paths and permissions reference `actual_user`, not root.

**Environment Variables:**

- `CHROOT_NAME`: Name of the schroot (default: debian-amd64)
- `CHROOT_PATH`: Path to chroot root (default: /srv/$CHROOT_NAME)
- `USER`: Target user for Wine execution

**Usage Examples:**

```bash
# Execute Wine application
run-chroot wine "C:\Program Files\App\app.exe"

# Run Wine configuration
run-chroot winecfg

# Launch Q4Wine (Wine GUI manager)
run-chroot q4wine
```

## System Requirements

### Host System (ARM64)

- Debian Trixie (or compatible) ARM64
- Required packages:
  - `debootstrap` - Create Debian base systems
  - `schroot` - Manage chroot sessions
  - `qemu-user-static` - AMD64 emulation on ARM64
  - `binfmt-support` - Binary format support
  - `icoutils` - Icon extraction (wrestool, icotool)

### Chroot Environment (AMD64)

- Debian Trixie AMD64 (created via debootstrap)
- Required packages:
  - `wine`, `wine32`, `wine64` - Windows application layer
  - `winetricks` - Wine helper scripts
  - `fonts-wine` - Windows fonts
  - Optional: `q4wine` - GUI Wine manager
  - Optional: `gnome-terminal`, `konsole`, or `lxterminal` - Better terminal emulators

## Setup Process

**Complete setup instructions are in `docs/chroot-setup_es.md` (Spanish).**

### Quick Reference

1. **Install host tools:**

   ```bash
   sudo apt install debootstrap schroot qemu-user-static binfmt-support
   ```

2. **Create chroot:**

   ```bash
   sudo debootstrap --arch=amd64 trixie /srv/debian-amd64 \
     http://deb.debian.org/debian
   ```

3. **Configure schroot:**

   - Create `/etc/schroot/chroot.d/debian-amd64.conf`
   - Edit `/etc/schroot/default/fstab` for bind-mounts
   - See `docs/chroot-setup_es.md` for detailed configuration

4. **Install Wine in chroot:**

   ```bash
   sudo schroot -c debian-amd64
   # Inside chroot:
   dpkg --add-architecture i386
   apt update
   apt install wine wine32 wine64 winetricks fonts-wine
   ```

5. **Install run-chroot script:**

   ```bash
   sudo cp src/run-chroot.sh /usr/local/bin/run-chroot
   sudo chmod +x /usr/local/bin/run-chroot
   ```

6. **Configure sudoers** (optional, for password-less execution):

   ```bash
   sudo visudo
   # Add: <user> ALL=(ALL) NOPASSWD: /usr/bin/schroot
   ```

## Desktop Integration

### .desktop File Format

Create launchers in `~/.local/share/applications/`:

```ini
[Desktop Entry]
Name=Application Name
Comment=Description
Exec=/usr/local/bin/run-chroot wine "C:\\Path\\To\\App.exe"
Icon=~/.local/share/icons/app-icon.png
Terminal=false
Type=Application
StartupNotify=true
Categories=Wine;WindowsApps;
StartupWMClass=app.exe
```

**Key Fields:**

- `Exec`: Must use `run-chroot` and Windows path format with double backslashes
- `Icon`: Extract icons using `wrestool` and `icotool` (see docs)
- `StartupWMClass`: Usually the executable name (helps window managers)
- `Categories`: Include `Wine;` for organization

### Refresh Desktop Database

After creating/modifying .desktop files:

```bash
update-desktop-database ~/.local/share/applications
```

## Common Tasks

### Testing Chroot

```bash
# List available chroots
schroot --list

# Check architecture
uname -m                              # Should show: aarch64
sudo schroot -c debian-amd64 -- uname -m  # Should show: x86_64

# Enter chroot interactively
sudo schroot -c debian-amd64
```

### Managing Schroot Sessions

```bash
# List active sessions
schroot --list --all-sessions

# End all sessions
sudo schroot --end-session --all-sessions

# Kill hung Wine processes
sudo schroot -c debian-amd64 -- pkill -9 wine
```

### Debugging X11 Issues

```bash
# Allow X11 connections from specific user
xhost +SI:localuser:$USER

# Check X11 socket exists
ls -la /tmp/.X11-unix/

# Verify DISPLAY variable
echo $DISPLAY

# Test X11 forwarding
run-chroot xterm
```

### Path Conversion

**Windows paths in Wine:** Use double backslashes in shell commands

```bash
# Correct
run-chroot wine "C:\\Program Files\\App\\app.exe"

# Incorrect (will fail)
run-chroot wine "C:\Program Files\App\app.exe"
```

**Linux paths to Wine paths:**

```text
/srv/debian-amd64/home/user/.wine/drive_c/Program Files/App
           ↓
C:\\Program Files\\App
```

The script handles environment setup, but executable paths must be provided in Windows format.

## Troubleshooting

### Runtime Directory Errors (Qt/KDE apps)

**Symptom:** `QStandardPaths: runtime directory '/run/user/1000' is not owned by UID 1000`

**Cause:** schroot creates a new tmpfs for `/run` instead of bind-mounting it from the host, causing ownership mismatches

**Solution:** The `run-chroot.sh` script uses `/tmp/runtime-$USER` instead of `/run/user/$UID`, avoiding this issue entirely. Verify:

```bash
ls -ld /tmp/runtime-$(whoami)
# Should show: drwx------ owned by your user
```

This directory is automatically created by `run-chroot.sh` and is accessible from both host and chroot with correct permissions.

### Wine Prefix Issues

**Per-user prefix** (recommended):

```bash
# Initialize as specific user
sudo schroot -c debian-amd64 --user=$USER -- \
  env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" winecfg
# Creates: /home/$USER/.wine inside chroot
```

**Global prefix** (not recommended):

```bash
# Root prefix
sudo schroot -c debian-amd64 -- winecfg
# Creates: /root/.wine inside chroot
```

### Schroot Won't Start

1. End all sessions: `sudo schroot --end-session --all-sessions`
2. Unmount chroot: `sudo umount -R /srv/debian-amd64`
3. Re-mount: `sudo mount -a`
4. Verify config: `sudo schroot -c debian-amd64 -- true`

## Development Notes

### Bash Script Conventions

- Use `set -e` and `set -u` for safety
- Prefer `"${VAR:-default}"` for variable defaults
- Quote all paths: `"$PATH_VAR"`
- Use double backslashes in example Windows paths
- Document environment variables at script top

### User Variable Handling Pattern

**Always derive from target user, not process:**

```bash
# ✓ Correct - derives from $USER parameter
TARGET_UID=$(id -u "$USER")
TARGET_GID=$(id -g "$USER")
TARGET_HOME=$(getent passwd "$USER" | cut -d: -f6)

# ✗ Wrong - uses executing process (may be root)
TARGET_UID=$UID
TARGET_GID=$(id -g)
TARGET_HOME=$HOME
```

This is critical for scripts executed via sudo/pkexec.

### Testing Changes

When modifying `run-chroot.sh`:

1. Test with direct execution:

   ```bash
   ./src/run-chroot.sh wine notepad
   ```

2. Test with sudo (simulates .desktop launcher):

   ```bash
   sudo USER=$USER ./src/run-chroot.sh wine notepad
   ```

3. Test via installed script:

   ```bash
   sudo cp src/run-chroot.sh /usr/local/bin/run-chroot
   run-chroot wine notepad
   ```

4. Test via .desktop file (full integration):
   - Create test launcher in `~/.local/share/applications/`
   - Launch from application menu

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later)

See LICENSE file for full text.

## References

- Main documentation: `docs/chroot-setup_es.md` (Spanish)
- Wine on Debian: <https://wiki.debian.org/Wine>
- WineHQ Guide: <https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu>
- schroot manual: `man schroot`
- QEMU User Emulation: <https://qemu-project.gitlab.io/qemu/user/main.html>
