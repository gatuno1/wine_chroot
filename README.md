# Wine Chroot - Run Windows Apps on ARM64 Linux

**Wine Chroot** is an automated solution for running Windows amd64 applications on ARM64 Linux hardware (specifically Debian-based systems) using Wine within a chroot environment.

This tool simplifies the entire workflow from chroot setup to application execution and desktop integration, providing a unified Python-based CLI for all operations.

## Features

- **Automated Setup**: One-command chroot initialization with `wine-chroot init`
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

1 **Clone the repository:**

```bash
git clone https://github.com/gatuno/wine_chroot.git
cd wine_chroot
```

2 **Install uv (if not already installed):**

```bash
# Install uv using the official install script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell configuration
if [ -n "$BASH_VERSION" ]; then
    source ~/.bashrc
elif [ -n "$ZSH_VERSION" ]; then
    source ~/.zshrc
elif [ -n "$FISH_VERSION" ]; then
    source ~/.config/fish/config.fish
fi

# Install shell autocompletion (optional but recommended)
# For bash:
if [ -n "$BASH_VERSION" ]; then
    echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
    echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc
# For zsh:
elif [ -n "$ZSH_VERSION" ]; then
    echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
    echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
# For fish:
elif [ -n "$FISH_VERSION" ]; then
    uv generate-shell-completion fish > ~/.config/fish/completions/uv.fish
    uvx --generate-shell-completion fish > ~/.config/fish/completions/uvx.fish
fi

# Reload shell again to enable autocompletion
if [ -n "$BASH_VERSION" ]; then
    source ~/.bashrc
elif [ -n "$ZSH_VERSION" ]; then
    source ~/.zshrc
elif [ -n "$FISH_VERSION" ]; then
    source ~/.config/fish/config.fish
fi
```

3 **Install system dependencies:**

```bash
sudo apt update
sudo apt install schroot debootstrap qemu-user-static binfmt-support icoutils
```

4 **Install wine-chroot:**

```bash
# Install as a global tool (recommended - makes 'wine-chroot' command available)
uv tool install -e .

# Verify installation
wine-chroot --version
```

**Alternative installation methods:**

```bash
# Install in virtual environment (requires 'uv run' prefix)
uv pip install -e .
uv run wine-chroot --version

# Install without editable mode (for production use)
uv tool install .
```

> **For developers**: See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development setup and testing workflow.

### Setting Up the Chroot

**Option 1 - Automated Setup (Recommended):**

Use the `wine-chroot init` command to automatically create and configure the chroot:

```bash
# Initialize with default settings
wine-chroot init

# Or customize the installation
wine-chroot init --name my-wine-chroot --path /opt/wine-chroot

# Preview what will be done without making changes
wine-chroot init --dry-run
```

The init command will:

- Create a Debian amd64 chroot using debootstrap
- Configure schroot and bind mounts
- Install Wine (wine, wine32, wine64)
- Set up locales and repositories
- Verify the installation

**Option 2 - Manual Setup:**

If you prefer manual configuration or need more control, follow the detailed guide in [docs/chroot-setup.md](docs/chroot-setup.md).

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

### Initializing a Chroot (First Time Setup)

If you haven't set up a chroot yet, use the `init` command:

```bash
# Basic initialization (uses default settings)
wine-chroot init

# Custom location
wine-chroot init --name wine-testing --path /opt/wine-testing

# Different Debian version
wine-chroot init --debian-version bookworm

# Skip Wine installation (install manually later)
wine-chroot init --skip-wine

# Dry-run to see what will happen
wine-chroot init --dry-run
```

**What the init command does:**

1. ✓ Checks system prerequisites
2. ✓ Creates Debian amd64 base system with debootstrap
3. ✓ Configures schroot profile
4. ✓ Sets up bind mounts (fstab)
5. ✓ Configures locales
6. ✓ Adds Debian repositories
7. ✓ Enables i386 architecture (for 32-bit Wine)
8. ✓ Installs Wine packages
9. ✓ Verifies installation

**Time and space requirements:**

- Download size: ~200-500 MB
- Disk space needed: ~2-3 GB
- Time: 10-30 minutes (depending on internet speed)

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
│   ├── README.md            # Documentation index
│   ├── chroot-setup.md      # Detailed chroot setup guide
│   └── DEVELOPMENT.md       # Development guide
├── tests/                   # Unit tests
├── pyproject.toml           # Project metadata
├── wine-chroot.toml.example # Example configuration
├── CLAUDE.md                # AI assistant guidelines
└── README.md                # This file
```

## Development

Want to contribute or customize wine-chroot? Check out the comprehensive development guide:

**[📖 Development Guide](docs/DEVELOPMENT.md)**

The guide covers:

- Development environment setup
- Project architecture and module overview
- Code style guidelines and best practices
- Testing and debugging
- Contributing workflow
- Building and packaging

Quick start for developers:

```bash
# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Check code style
ruff check src/
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

**Alternative Using pkexec:**

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

- **Setup issues**: Check [docs/chroot-setup.md](docs/chroot-setup.md) for detailed chroot configuration
- **Development questions**: See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for development guidelines
- **Bugs or features**: Open an issue on GitHub
- **General questions**: Use GitHub Discussions

## License

This project is distributed under the terms of the **GNU General Public License version 3** (or, at your option, any later version).

See the [LICENSE](LICENSE) file for the full license text.

## Contributing

Contributions are welcome! Please see the [Development Guide](docs/DEVELOPMENT.md) for:

- Setting up your development environment
- Code style guidelines
- Testing requirements
- Pull request process
- Commit message conventions

## Acknowledgments

- **Wine Project**: For the Windows compatibility layer
- **QEMU**: For ARM64 → x86-64 emulation
- **schroot**: For chroot management

## References

- [Wine on Debian Wiki](https://wiki.debian.org/Wine)
- [WineHQ Debian/Ubuntu Guide](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu)
- [schroot Documentation](https://manpages.debian.org/testing/schroot/schroot.1.en.html)
- [QEMU User Emulation](https://qemu-project.gitlab.io/qemu/user/main.html)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
