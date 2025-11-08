# Wine Chroot Project

This project ships two implementations, Python 3.10+ and Bash, designed to run on Debian Linux hosts.

## Project Structure

```asciiart
wine_chroot/
├── python/                            # Python implementation
│   ├── make_wine_chroot_desktop.py    # Primary Python script
│   └── requirements.txt               # Python dependencies (legacy helpers)
├── bash/                              # Bash implementation
│   └── make_wine_chroot_desktop.sh    # Primary Bash script
├── .github/
│   └── copilot-instructions.md
├── pyproject.toml                     # Python project configuration (uv)
├── .gitignore
└── README.md
```

## System Requirements

### Host (where these scripts run)

- **Operating System**: Debian Linux (or Debian-based distributions such as Ubuntu)
- **Privileges**: User able to run scripts with sudo
- **schroot**: Manage and access the chroot environment
- **icoutils**: Tools to extract icons from .exe files (wrestool, icotool)

### Inside the chroot (debian-amd64)

- **Wine**: Installed inside the schroot to run Windows applications
- The schroot must already exist and be configured

### Python Implementation Requirements

- **Python**: 3.10 or newer
- **Python dependencies**: `rich`, `rich-argparse` (installed automatically via uv)
- **uv**: Ultra-fast Python package manager (optional but recommended)

### Bash Implementation Requirements

- **Bash**: 4.0 or newer (usually installed by default on Debian)

## Installation on Debian

### 1. Install uv

```bash
# Recommended installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative via pip
pip install uv
```

### 2. Verify installed versions

```bash
# Check uv
uv --version

# Check Python
python3 --version

# Check Bash
bash --version
```

### 3. Install host-side system dependencies

```bash
# Refresh package list
sudo apt update

# Install Python 3.10+ if missing
sudo apt install python3

# Install required host tools
sudo apt install schroot icoutils

# Validate installation
schroot --version
wrestool --version
icotool --version
```

### 4. Set up Wine inside the chroot

Wine must be installed **inside the schroot**, not on the host:

```bash
# Enter the chroot
sudo schroot -c debian-amd64

# Inside the chroot, install wine
apt update
apt install wine

# Verify installation
wine --version

# Leave the chroot
exit
```

**Note:** This README assumes an existing debian-amd64 schroot. Instructions for creating the schroot will be documented separately.

## Usage

### Python Implementation Usage

The Python script generates `.desktop` launchers that run Windows applications through Wine inside a schroot.

#### Basic Usage (Python)

```bash
uv run python/make_wine_chroot_desktop.py \
    --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe" \
    --name "Application Name"
```

#### Selected Options (Python)

```bash
# Extract icon assets
uv run python/make_wine_chroot_desktop.py \
    --exe "/path/to/program.exe" \
    --name "My Application" \
    --icon

# Target a custom schroot
uv run python/make_wine_chroot_desktop.py \
    --exe "/path/to/program.exe" \
    --name "My Application" \
    --schroot "my-chroot"

# Using short options (same as above)
uv run python/make_wine_chroot_desktop.py \
    -e "/path/to/program.exe" \
    -n "My Application" \
    -i \
    -s "my-chroot" \
    -d "custom.desktop"

# Show CLI help
uv run python/make_wine_chroot_desktop.py --help
```

#### Available Options

| Short | Long         | Required | Default        | Description                                    |
|-------|--------------|----------|----------------|------------------------------------------------|
| `-e`  | `--exe`      | Yes      | -              | Path to the .exe inside the schroot tree       |
| `-n`  | `--name`     | Yes      | -              | Application name for the desktop menu          |
| `-d`  | `--desktop`  | No       | Auto-generated | Custom .desktop filename                       |
| `-i`  | `--icon`     | No       | False          | Extract icon from .exe using wrestool/icotool  |
| `-s`  | `--schroot`  | No       | `debian-amd64` | Name of the schroot to use                     |

### Execution methods

#### Option 1: Run with uv (recommended)

```bash
# Execute directly via uv
uv run python/make_wine_chroot_desktop.py --exe <path> --name <name>

# Or, after installing the project entry point
uv run wine-chroot --exe <path> --name <name>
```

#### Option 2: uv-managed virtual environment

```bash
# Create a virtual environment with uv
uv venv

# Activate the environment
source .venv/bin/activate

# Install the project and dependencies
uv pip install -e .

# Run the script
python python/make_wine_chroot_desktop.py

# Deactivate when finished
deactivate
```

#### Option 3: Direct execution (without uv)

```bash
# Navigate to the python directory
cd python

# Run the script
python3 make_wine_chroot_desktop.py
```

### Bash Implementation Usage

The Bash script mirrors the functionality of the Python version.

#### Basic Usage (Bash)

```bash
./bash/make_wine_chroot_desktop.sh \
    --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe" \
    --name "Application Name"
```

#### Selected Options (Bash)

```bash
# Extract icon assets
./bash/make_wine_chroot_desktop.sh \
    --exe "/path/to/program.exe" \
    --name "My Application" \
    --icon

# Target a custom schroot
./bash/make_wine_chroot_desktop.sh \
    --exe "/path/to/program.exe" \
    --name "My Application" \
    --schroot "my-chroot"

# Using short options (same as above)
./bash/make_wine_chroot_desktop.sh \
    -e "/path/to/program.exe" \
    -n "My Application" \
    -i \
    -s "my-chroot" \
    -d "custom.desktop"

# Show CLI help
./bash/make_wine_chroot_desktop.sh --help
```

Both Python and Bash implementations support the same short options for convenience.

**Note:** Ensure the script is executable:

```bash
chmod +x bash/make_wine_chroot_desktop.sh
```

## Troubleshooting

### uv: "command not found"

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart the terminal or reload the shell
source ~/.zshrc  # or ~/.bashrc
```

### Python: "command not found"

```bash
# Install Python 3
sudo apt install python3
```

### Bash: "Permission denied"

```bash
# Grant execute permissions
chmod +x bash/make_wine_chroot_desktop.sh
```

### Python: incorrect version

```bash
# Check the installed version
python3 --version

# uv can manage alternative Python versions
uv python install 3.11
uv python pin 3.11
```

### Missing host tools

```bash
# If wrestool or icotool are unavailable
sudo apt install icoutils

# If schroot is unavailable
sudo apt install schroot
```

### Wine fails inside the chroot

```bash
# Enter the chroot
sudo schroot -c debian-amd64

# Check whether wine is installed
which wine

# If missing, install it
apt update
apt install wine

# Test wine
wine --version

# Exit the chroot
exit
```

## License

This project is distributed under the terms of the **GNU General Public License**
version 3 (or, at your option, any later version). See the `LICENSE` file for the
full license text.

By contributing to this repository you agree that your contributions will be
published under the GPL-3.0-or-later license.

## Contributing

Contributions are welcome. Please make sure your changes work correctly on Debian Linux before opening a pull request.
