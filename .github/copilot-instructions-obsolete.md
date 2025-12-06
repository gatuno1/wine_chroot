# Wine Chroot Project - Copilot Instructions

## Project Summary

The project ships Python 3.10+ and Bash implementations designed for Debian Linux hosts.
It generates .desktop files to launch Windows applications with Wine inside schroot environments.
The toolchain relies on **uv** for Python environments and packaging.
License: GNU GPL v3 or later.

**Architecture:**
- Scripts run on the **HOST** (Debian ARM64 or other architectures)
- Wine runs **INSIDE THE CHROOT** (Debian amd64)
- Enables Windows x86/amd64 applications on hosts with different CPU architectures

## Dependencies

### Python
- **Minimum version**: Python 3.10+
- **Python dependencies**: rich, rich-argparse
- **Standard library modules**: argparse, re, shutil, subprocess, pathlib

### System - Host side
- schroot (manage chroot environments)
- icoutils (wrestool, icotool for icon extraction)

### System - Inside the chroot
- wine (run Windows applications)
- The chroot must be provisioned and ready to use

## Project Layout

- `python/` - Python 3.10+ implementation
  - `make_wine_chroot_desktop.py` - Main Python script
- `bash/` - Bash implementation
  - `make_wine_chroot_desktop.sh` - Main Bash script
- `pyproject.toml` - Python project configuration (uv)
- `README.md` - Project documentation

## Tooling

- Python 3.10+
- Bash 4.0+
- uv (Python package manager)
- Debian Linux

## Core Commands

### Python via uv

```bash
# Run the Python script
uv run python/make_wine_chroot_desktop.py

# Add dependencies
uv add <package>

# Create a virtual environment
uv venv

# Install the project
uv pip install -e .
```

### Bash

```bash
# Execute the Bash script
./bash/make_wine_chroot_desktop.sh

# Grant execution permissions
chmod +x bash/make_wine_chroot_desktop.sh
```

## Best Practices

- Prefer uv for Python-related operations
- Maintain compatibility with Python 3.10+
- Bash scripts should use `set -e` and `set -u`
- Document user-facing changes in English
- Test on Debian Linux
