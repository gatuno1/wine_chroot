# Wine Chroot - Run Windows Apps on ARM64 Linux

**Wine Chroot** is an automated solution for running Windows amd64 applications on ARM64 Linux hardware (specifically Debian-based systems) using Wine within a chroot environment.

This tool simplifies the entire workflow from chroot setup to application execution and desktop integration, providing a unified Python-based CLI for all operations.

## Features

- **Simple CLI Interface**: Unified command-line tool for all operations
- **Desktop Integration**: Automatic .desktop launcher creation with icon extraction
- **X11 Support**: Seamless GUI application integration with your desktop
- **Configuration-Driven**: TOML-based configuration for easy customization
- **Application Discovery**: Automatically find installed Windows applications
- **Modern Python**: Built with Python 3.10+ using uv for package management

## System Architecture

```text
┌───────────────────────────────────────────────────────────┐
│  Host System (Debian ARM64)                               │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │  wine-chroot CLI Tool                              │   │
│  │  • run: Execute Windows apps                       │   │
│  │  • desktop: Create launchers                       │   │
│  │  • list: Show applications                         │   │
│  │  • config: Manage settings                         │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │  schroot + qemu-user-static                        │   │
│  │  (ARM64 → AMD64 emulation)                         │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Chroot Environment (Debian AMD64)                 │   │
│  │  • Wine x64 + Wine x86                             │   │
│  │  • Windows applications                            │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

**Host system requirements:**

- Debian Trixie (testing) or compatible distribution on ARM64
- Root access (for chroot creation)
- Internet connection (for package installation)

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/gatuno/wine_chroot.git
cd wine_chroot
```

2. **Install uv (if not already installed):**

```bash
# Install uv using the official install script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell configuration
source ~/.bashrc  # or source ~/.zshrc for zsh

# Install shell autocompletion (optional but recommended)
# For bash:
if [ -n "$BASH_VERSION" ]; then
    echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
    echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc
fi

# For zsh:
if [ -n "$ZSH_VERSION" ]; then
    echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
    echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
fi

# For fish:
# uv generate-shell-completion fish > ~/.config/fish/completions/uv.fish
# uvx --generate-shell-completion fish > ~/.config/fish/completions/uvx.fish

# Reload shell again to enable autocompletion
source ~/.bashrc  # or source ~/.zshrc
```

3. **Install system dependencies:**

```bash
sudo apt update
sudo apt install schroot debootstrap qemu-user-static binfmt-support icoutils
```

4. **Install wine-chroot:**

```bash
# Option 1: Install in development mode (recommended for testing/development)
# This creates an editable installation that reflects code changes immediately
uv pip install -e .

# Verify installation
wine-chroot --version

# Option 2: Run directly with uv (no installation needed)
# This is useful for trying the tool without installing
uv run wine-chroot --help
```

**Why development mode?**
Installing with `-e` (editable mode) is useful because:

- Changes to the code are reflected immediately without reinstalling
- You can customize the tool for your needs
- Easy to contribute improvements back to the project
- The `wine-chroot` command becomes available system-wide

### Setting Up the Chroot

Follow the detailed guide in [docs/chroot-setup.md](docs/chroot-setup.md) to create and configure your Debian amd64 chroot with Wine.

**Quick summary:**

```bash
# 1. Create the chroot named 'debian-amd64'
sudo debootstrap --arch=amd64 trixie /srv/debian-amd64 http://deb.debian.org/debian

# 2. Configure schroot (see docs/chroot-setup.md)

# 3. Enter chroot and install Wine
sudo schroot -c debian-amd64
apt update && apt install wine wine32 wine64 wine-binfmt fonts-wine  --install-recommends
exit
```

### Configuration

Create a configuration file (optional but recommended):

```bash
wine-chroot config --init
```

This creates `~/.config/wine-chroot.toml` with default settings. Edit as needed:

```toml
[chroot]
name = "debian-amd64"
path = "/srv/debian-amd64"

[execution]
use_pkexec = false  # Use sudo (false) or pkexec (true)
                    # sudo is recommended for reliability with .desktop launchers
```

See [wine-chroot.toml.example](wine-chroot.toml.example) for all options.

## Usage

### Running Windows Applications

Execute a Windows application directly:

```bash
# Using Windows path format
wine-chroot run "C:\Program Files\MyApp\app.exe"

# Using Linux path format
wine-chroot run /srv/debian-amd64/root/.wine/drive_c/Program\ Files/MyApp/app.exe

# With arguments
wine-chroot run "C:\Windows\notepad.exe" myfile.txt

# Wait for application to exit
wine-chroot run --wait "C:\Program Files\MyApp\app.exe"
```

### Creating Desktop Launchers

Create a .desktop file for easy access from your application menu:

```bash
# Basic launcher
wine-chroot desktop \
  --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/MyApp/app.exe" \
  --name "My Application"

# With icon extraction
wine-chroot desktop \
  --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/MyApp/app.exe" \
  --name "My Application" \
  --icon

# Short form
wine-chroot desktop -e "/path/to/app.exe" -n "My App" -i
```

The launcher will appear in your application menu under the "Wine" category.

### Listing Applications

**List installed Windows applications:**

```bash
wine-chroot list
```

**List only existing .desktop launchers:**

```bash
wine-chroot list --launchers
```

### Managing Configuration

**Show current configuration:**

```bash
wine-chroot config --show
```

**Create example configuration:**

```bash
wine-chroot config --init
```

### Other Commands

**Check version:**

```bash
wine-chroot --version
```

**Verbose output:**

```bash
wine-chroot -v run "C:\Program Files\MyApp\app.exe"
```

**Help:**

```bash
wine-chroot --help
wine-chroot run --help
wine-chroot desktop --help
```

## Project Structure

```asciiart
wine_chroot/
├── src/
│   └── wine_chroot/         # Main package
│       ├── cli.py           # CLI interface
│       ├── config.py        # Configuration management
│       ├── runner.py        # Wine execution
│       ├── desktop.py       # Desktop integration
│       ├── icons.py         # Icon extraction
│       └── utils.py         # Utilities
├── docs/
│   └── chroot-setup.md      # Detailed setup guide
├── tests/                   # Unit tests
├── pyproject.toml           # Project metadata
├── wine-chroot.toml.example # Example configuration
├── CLAUDE.md                # Development guidelines
└── README.md                # This file
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Format code
ruff format src/
```

### Running from Source

```bash
# Use uv to run directly
uv run wine-chroot --help

# Or activate virtual environment
source .venv/bin/activate
wine-chroot --help
```

## Troubleshooting

### Common Issues

**Wine not found in chroot:**

```bash
# Enter chroot and check Wine installation
sudo schroot -c debian-amd64
wine --version
exit
```

If Wine is not installed, install it inside the chroot:

```bash
sudo schroot -c debian-amd64
apt update
apt install wine wine32 wine64
exit
```

**Permission errors when launching applications:**

The tool uses `sudo` by default because it's more reliable with .desktop launchers. To avoid password prompts when launching applications from the menu, add a sudoers entry:

```bash
# Create a sudoers rule for schroot (recommended)
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/schroot" | sudo tee /etc/sudoers.d/schroot
sudo chmod 0440 /etc/sudoers.d/schroot
```

**Alternative: Using pkexec**

You can configure the tool to use `pkexec` instead of `sudo`:

```bash
wine-chroot config --init
# Edit ~/.config/wine-chroot.toml and set use_pkexec = true
```

However, note that `pkexec` may be less reliable for launching GUI applications from .desktop files. It's primarily useful for interactive CLI usage where you want a graphical authentication dialog.

**Icon extraction fails:**

Ensure icoutils is installed:

```bash
sudo apt install icoutils
```

**Application window doesn't appear:**

Check X11 forwarding:

```bash
# Allow local X11 connections
xhost +local:

# Verify DISPLAY is set
echo $DISPLAY
```

### Getting Help

- Check [docs/chroot-setup.md](docs/chroot-setup.md) for detailed setup instructions
- See [CLAUDE.md](CLAUDE.md) for development guidelines
- Open an issue on GitHub for bugs or feature requests

## Comparison with Other Solutions

**Wine Chroot vs Box64:**

- Wine Chroot provides full x86-64 Wine support without compatibility layers
- Better compatibility with complex Windows applications
- Uses real Debian packages instead of custom builds

**Wine Chroot vs CrossOver:**

- Free and open source (GPL-3.0-or-later)
- More transparent architecture
- Full control over Wine version and configuration

## License

This project is distributed under the terms of the **GNU General Public License version 3** (or, at your option, any later version).

See the [LICENSE](LICENSE) file for the full license text.

## Contributing

Contributions are welcome! Please:

1. Follow the code style in [CLAUDE.md](CLAUDE.md)
2. Add tests for new functionality
3. Update documentation as needed
4. Use conventional commits (feat:, fix:, docs:, etc.)

## Acknowledgments

- **Wine Project**: For the Windows compatibility layer
- **Debian**: For the stable base system
- **QEMU**: For ARM64 → x86-64 emulation
- **schroot**: For chroot management

## References

- [Wine on Debian Wiki](https://wiki.debian.org/Wine)
- [WineHQ Debian/Ubuntu Guide](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu)
- [schroot Documentation](https://manpages.debian.org/testing/schroot/schroot.1.en.html)
- [QEMU User Emulation](https://qemu-project.gitlab.io/qemu/user/main.html)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
