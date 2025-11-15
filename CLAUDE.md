# Wine Chroot - Project Guidelines

## Project Vision

Wine Chroot is an automated solution for running Windows amd64 applications on ARM64 Linux hardware (specifically Debian-based systems) using Wine within a chroot environment. The project provides a unified Python-based CLI tool that simplifies the entire workflow: from chroot initialization to application execution and desktop integration.

## Architecture Overview

### System Components

```text
┌─────────────────────────────────────────────────────────────┐
│  Host System (Debian ARM64)                                 │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  wine-chroot CLI Tool (Python + uv)                │    │
│  │  - init: Create and configure chroot               │    │
│  │  - run: Execute Windows apps                       │    │
│  │  - desktop: Create .desktop launchers              │    │
│  │  - list: Show available apps                       │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  schroot + qemu-user-static                        │    │
│  │  (Manages chroot sessions and ARM64→AMD64)         │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Chroot Environment (Debian AMD64)                 │    │
│  │  - Wine x64 + Wine x86 (i386 + amd64)              │    │
│  │  - Windows applications                             │    │
│  │  - Shared /home, /dev, /proc, /tmp, X11            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Single Language**: Python 3.10+ only, no bash scripts
2. **Modern Tooling**: uv for package management, TOML for configuration
3. **Automation First**: Minimize manual steps, provide guided setup
4. **Desktop Integration**: Seamless X11 integration with proper .desktop files
5. **Configuration-Driven**: wine-chroot.toml stores all settings
6. **Simple CLI**: Intuitive commands for common tasks

## Project Structure

```asciiart
wine_chroot/
├── src/
│   └── wine_chroot/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── chroot.py           # Chroot initialization and management
│       ├── runner.py           # Wine execution wrapper
│       ├── desktop.py          # Desktop integration (.desktop creation)
│       ├── icons.py            # Icon extraction (wrestool/icotool)
│       ├── config.py           # Configuration management (TOML)
│       └── utils.py            # Path conversion, validation, etc.
├── docs/
│   └── chroot-setup.md         # Detailed chroot setup guide
├── tests/
│   └── test_*.py               # Unit tests
├── .github/
│   └── copilot-instructions.md
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # Dependency lock file
├── wine-chroot.toml.example    # Example configuration file
├── CLAUDE.md                   # This file
├── README.md                   # User-facing documentation
└── LICENSE                     # GPL-3.0-or-later

```

## Core Functionality

### 1. Chroot Initialization (`wine-chroot init`)

Automates the creation of a Debian amd64 chroot on an ARM64 host:

- Check for required system packages (debootstrap, schroot, qemu-user-static, etc.)
- Create the chroot using debootstrap
- Configure schroot profile
- Set up fstab for bind-mounts (/home, /dev, /proc, /tmp, /tmp/.X11-unix)
- Install Wine inside the chroot (wine, wine32, wine64, winetricks)
- Enable i386 architecture
- Generate wine-chroot.toml configuration file

### 2. Application Execution (`wine-chroot run`)

Simplified wrapper around the schroot + Wine execution:

```bash
# Instead of: sudo schroot -c debian-amd64 -- wine "C:\Program Files\App\app.exe"
wine-chroot run "C:\Program Files\App\app.exe"
# or
wine-chroot run /srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe
```

Features:

- Automatic path conversion (Linux → Windows format)
- X11 forwarding (DISPLAY, XAUTHORITY)
- Privilege management (pkexec/sudo)
- Environment preservation

### 3. Desktop Integration (`wine-chroot desktop`)

Creates .desktop launchers with icon extraction:

```bash
wine-chroot desktop \
  --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe" \
  --name "My Application" \
  --icon
```

Features:

- Automatic icon extraction using wrestool + icotool
- Proper StartupWMClass for window grouping
- Categories: Wine, WindowsApps
- Integration with application menus

### 4. Application Management (`wine-chroot list`)

Lists installed Windows applications in the chroot:

```bash
wine-chroot list
```

Scans common Wine directories and displays:

- Application names
- Executable paths
- Whether a .desktop launcher exists

## Configuration System

### wine-chroot.toml

Central configuration file in TOML format:

```toml
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
use_pkexec = true  # true = pkexec, false = sudo
preserve_environment = true
x11_forwarding = true

[applications]
# Optional: pre-configured applications
# [[applications.app]]
# name = "Notepad++"
# exe = "C:\\Program Files\\Notepad++\\notepad++.exe"
# icon = "~/.local/share/icons/notepad-plus-plus.png"
```

## CLI Interface

```bash
wine-chroot --help

Usage: wine-chroot [OPTIONS] COMMAND [ARGS]...

Wine Chroot - Run Windows applications on ARM64 Linux

Commands:
  init       Initialize a new chroot environment
  run        Run a Windows application
  desktop    Create a .desktop launcher
  list       List applications or launchers
  config     Manage configuration

Options:
  -c, --config PATH   Path to wine-chroot.toml configuration file
  -v, --verbose       Enable verbose output
  -V, --version       Show version information
  -h, --help          Show this message and exit
```

### Subcommands

#### `wine-chroot init`

```bash
wine-chroot init [OPTIONS]

Initialize a new chroot environment

Options:
  -n, --name TEXT           Chroot name (default: from config or 'debian-amd64')
  -p, --path PATH           Chroot installation path (default: from config or '/srv/debian-amd64')
  --debian-version TEXT     Debian version (default: trixie)
  --skip-wine               Don't install Wine automatically
  --dry-run                 Show what would be done without making changes
  -h, --help                Show this message and exit
```

#### `wine-chroot run`

```bash
wine-chroot run [OPTIONS] EXE [ARGS]...

Run a Windows application

Arguments:
  EXE   Path to .exe file (Windows or Linux format)
  ARGS  Arguments to pass to the application

Options:
  -w, --wait            Wait for application to exit
  -t, --terminal        Show terminal output
  -h, --help            Show this message and exit
```

#### `wine-chroot desktop`

```bash
wine-chroot desktop [OPTIONS]

Create a .desktop launcher

Options:
  -e, --exe PATH        Path to .exe file (required)
  -n, --name TEXT       Application name for the menu (required)
  -i, --icon            Extract icon from .exe
  -d, --desktop TEXT    Custom .desktop filename
  -h, --help            Show this message and exit
```

#### `wine-chroot list`

```bash
wine-chroot list [OPTIONS]

List applications or launchers

Options:
  -l, --launchers       List only .desktop launchers (without this flag, lists all Windows applications in chroot)
  -h, --help            Show this message and exit
```

#### `wine-chroot config`

```bash
wine-chroot config [OPTIONS]

Manage configuration

Options:
  -s, --show            Show current configuration
  -i, --init            Create example configuration file
  -o, --output PATH     Output path for --init (default: ~/.config/wine-chroot.toml)
  -h, --help            Show this message and exit

Note: -s/--show and -i/--init are mutually exclusive (one is required)
```

## Technology Stack

### Core Dependencies

- **Python 3.10+**: Modern Python features (match/case, type hints, pathlib)
- **uv**: Ultra-fast Python package manager
- **rich**: Beautiful terminal output and progress bars
- **rich-argparse**: Enhanced argument parsing with rich formatting
- **tomli/tomllib**: TOML configuration parsing (tomllib in Python 3.11+)
- **pytest**: Testing framework

### System Dependencies

**Host (ARM64):**

- debootstrap: Create Debian base systems
- schroot: Manage chroot sessions
- qemu-user-static: x86-64 emulation on ARM64
- binfmt-support: Binary format support
- icoutils: Icon extraction (wrestool, icotool)

**Chroot (AMD64):**

- wine, wine32, wine64: Windows application layer
- winetricks: Wine configuration helper
- fonts-wine: Windows fonts

## Development Guidelines

### Code Style

- **Type hints**: Use type annotations for all functions
- **Docstrings**: Google-style docstrings for all public functions
- **Console output**: Use standardized console styles from `wine_chroot.console_styles`
- **Error handling**: Graceful error messages, avoid stack traces for user errors
- **Pathlib**: Use pathlib.Path instead of os.path
- **f-strings**: Use f-strings for string formatting

### Console Output Standards

**All console output must use the standardized styles from `wine_chroot.console_styles`:**

```python
from wine_chroot import console, success, error, warning, info
from wine_chroot import path, file, value, highlight

# Status messages
success("Operation completed")
error("File not found", hint="Check the path")
warning("Locale configuration failed")
info("Checking system dependencies...")

# Content formatting
console.print(f"Installing to {path('/srv/debian-amd64')}")
console.print(f"Created {file('wine-chroot.toml')}")
console.print(f"Debian version: {value('trixie')}")
console.print(f"Using {highlight('Wine')} in chroot")
```

**See `docs/CONSOLE_STYLE_GUIDE.md` for complete guidelines.**

### Example Code Pattern

```python
from pathlib import Path
from wine_chroot import console, success, error, path as format_path

def convert_path_to_windows(linux_path: Path) -> str:
    """Convert a Linux path to Windows format.

    Args:
        linux_path: Path object representing a file in the chroot

    Returns:
        Windows-style path string (e.g., "C:\\Program Files\\app.exe")

    Example:
        >>> convert_path_to_windows(Path("/srv/debian-amd64/root/.wine/drive_c/Program Files/app.exe"))
        "C:\\Program Files\\app.exe"
    """
    if "drive_c/" in str(linux_path):
        after = str(linux_path).split("drive_c/", 1)[1]
        win = after.replace("/", "\\")
        return f"C:\\{win}"
    return str(linux_path)

# Using standardized console output
def install_wine(chroot_path: Path, verbose: bool = False) -> bool:
    """Install Wine in the chroot.

    Args:
        chroot_path: Path to the chroot
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    console.print(f"\nInstalling Wine in {format_path(str(chroot_path))}...")

    try:
        # ... installation logic ...
        success("Wine installed successfully")
        return True
    except FileNotFoundError:
        error("Required tools not found", hint="Install debootstrap and schroot")
        return False
```

### Testing

- Unit tests for path conversion, configuration parsing
- Integration tests for chroot operations (requires root)
- Mock system calls where appropriate
- Use pytest fixtures for common test setup

### Error Handling Philosophy

- **User errors**: Clear, actionable messages without stack traces

  ```python
  from wine_chroot import error

  error(
      f"The .exe file does not exist at '{path}'",
      hint="Make sure the path is from the host perspective"
  )
  raise SystemExit(1)
  ```

- **System errors**: Show details with --verbose flag
- **Missing dependencies**: Check at startup, provide installation instructions

  ```python
  from wine_chroot import error, console

  error("Missing required tools: debootstrap, schroot")
  console.print("\nInstall with:")
  console.print("  sudo apt install debootstrap schroot")
  ```

### Privilege Escalation: sudo vs pkexec

**Decision: Use sudo by default**

The tool uses `sudo` for schroot access by default instead of `pkexec` for the following reasons:

1. **Reliability with .desktop launchers**: `sudo` works consistently when launching applications from desktop menu entries, while `pkexec` can be erratic with GUI applications.

2. **Environment preservation**: `sudo` better preserves environment variables needed for X11 forwarding (DISPLAY, XAUTHORITY).

3. **Configuration simplicity**: A single sudoers rule (`/etc/sudoers.d/schroot`) provides seamless password-free launching.

4. **Historical evidence**: The original bash implementation used a wrapper script that relied on sudo-like behavior, which worked reliably.

**When to use pkexec:**

- Interactive CLI usage where graphical authentication dialogs are preferred
- Systems with strict security policies against sudoers rules
- User explicitly configures `use_pkexec = true` in wine-chroot.toml

**Implementation:**

```python
# Default configuration (config.py)
"execution": {
    "use_pkexec": False,  # sudo is more reliable
    ...
}
```

## Migration from Current Code

### What to Keep

1. Icon extraction logic (wrestool + icotool) from `make_wine_chroot_desktop.py`
2. Path conversion functions (Linux ↔ Windows)
3. Desktop file generation structure
4. GPL-3.0-or-later license headers

### What to Remove

- bash/ directory (consolidate into Python)
- python/ directory (move to src/wine_chroot/)
- Duplicate functionality between bash and Python versions

### What to Add

1. `wine-chroot init` command for chroot creation
2. `wine-chroot run` command as improved winegui.sh replacement
3. `wine-chroot list` command for application discovery
4. Configuration file system (wine-chroot.toml)
5. Comprehensive error checking and validation
6. Progress bars for long operations (debootstrap, Wine installation)

## Implementation Phases

### Phase 1: Core Restructuring ✓

- ✅ Create new src/wine_chroot/ package structure
- ✅ Move and refactor existing code
- ✅ Update pyproject.toml with new entry points
- ✅ Create CLAUDE.md (this file)

### Phase 2: Configuration System ✓

- ✅ Implement config.py with TOML support
- ✅ Create wine-chroot.toml.example
- ✅ Add config validation and property accessors

### Phase 3: CLI Commands ✓

- ✅ Implement cli.py with argparse + rich-argparse
- ✅ Create subcommands: run, desktop, list, config, init
- ✅ Add --verbose and --config flags

### Phase 4: Chroot Management ✓

- ✅ Implement chroot.py with init functionality
- ✅ Automate debootstrap, schroot config, Wine installation
- ✅ Add safety checks and dry-run mode
- ✅ Progress indicators for long operations

### Phase 5: Desktop Integration ✓

- ✅ Implement desktop.py with icon extraction
- ✅ Implement list command with app discovery
- ✅ Desktop file generation with proper metadata

### Phase 6: Documentation & Testing ✓

- ✅ Update README.md with new CLI usage
- ✅ Create docs/chroot-setup.md with detailed guide
- ✅ Create docs/DEVELOPMENT.md for contributors
- ✅ Comprehensive project documentation
- ⏳ Add comprehensive unit tests (in progress)

## Future Enhancements

- **GUI**: Optional GTK/Qt interface for non-technical users
- **Profiles**: Multiple chroot environments (wine-stable, wine-staging)
- **Winetricks integration**: `wine-chroot install vcrun2019`
- **Application templates**: Pre-configured settings for popular apps
- **Update management**: Upgrade Wine and chroot packages
- **Backup/restore**: Export/import chroot configurations
- **Performance monitoring**: Track application resource usage

## Contributing

When contributing to this project:

1. Follow the code style guidelines above
2. Add tests for new functionality
3. Update documentation (README, CLAUDE.md)
4. Use conventional commits (feat:, fix:, docs:, etc.)
5. Ensure all code is GPL-3.0-or-later compatible

## References

- [Wine on Debian Wiki](https://wiki.debian.org/Wine)
- [WineHQ Debian/Ubuntu Guide](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu)
- [schroot Documentation](https://manpages.debian.org/testing/schroot/schroot.1.en.html)
- [QEMU User Emulation](https://qemu-project.gitlab.io/qemu/user/main.html)
- [uv Documentation](https://github.com/astral-sh/uv)
