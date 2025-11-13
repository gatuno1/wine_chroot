# Development Guide

This guide covers everything you need to know to develop, test, and contribute to the Wine Chroot project.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Building and Packaging](#building-and-packaging)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- Python 3.10 or newer
- uv package manager
- Git
- System dependencies: `schroot`, `debootstrap`, `qemu-user-static`, `icoutils`

### Initial Setup

1. **Clone the repository:**

```bash
git clone https://github.com/gatuno/wine_chroot.git
cd wine_chroot
```

2. **Install uv (if not already installed):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or source ~/.zshrc
```

3. **Install in development mode:**

```bash
# Create virtual environment and install dependencies
uv sync

# Install the package in editable mode
uv pip install -e .

# Verify installation
wine-chroot --version
```

**Why development mode (`-e`)?**

Installing with `-e` (editable mode) has several advantages:

- **Live code changes**: Modifications to the source code are immediately reflected without reinstalling
- **Easy debugging**: You can add print statements and debug code on the fly
- **Local customization**: Test changes specific to your environment
- **Contribution workflow**: Makes it easy to develop features and submit pull requests
- **System-wide access**: The `wine-chroot` command is available from anywhere

### Development Dependencies

Install additional development tools:

```bash
# Install development dependencies (pytest, ruff, etc.)
uv pip install -e ".[dev]"

# Verify dev tools
pytest --version
ruff --version
```

### IDE Setup

#### VS Code

Recommended extensions:

- Python (Microsoft)
- Pylance
- Ruff
- Python Test Explorer

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Project Architecture

### Directory Structure

```
wine_chroot/
├── src/
│   └── wine_chroot/           # Main package
│       ├── __init__.py        # Package metadata
│       ├── cli.py             # CLI interface (argparse + rich)
│       ├── config.py          # TOML configuration management
│       ├── runner.py          # Wine execution wrapper
│       ├── desktop.py         # .desktop file creation
│       ├── icons.py           # Icon extraction (wrestool/icotool)
│       └── utils.py           # Path conversion, validation
├── docs/
│   ├── chroot-setup.md        # Chroot setup guide (Spanish)
│   └── DEVELOPMENT.md         # This file
├── tests/
│   └── test_*.py              # Unit and integration tests
├── pyproject.toml             # Project metadata and dependencies
├── wine-chroot.toml.example   # Example configuration
├── CLAUDE.md                  # AI assistant guidelines
├── README.md                  # User documentation
└── LICENSE                    # GPL-3.0-or-later
```

### Module Overview

#### `cli.py`
- **Purpose**: Command-line interface using argparse + rich-argparse
- **Commands**: `run`, `desktop`, `list`, `config`, `init`, `version`
- **Key functions**: `build_parser()`, `cmd_*()`, `main()`

#### `config.py`
- **Purpose**: TOML configuration file management
- **Key classes**: `Config`
- **Features**: Default values, property accessors, file generation

#### `chroot.py`
- **Purpose**: Chroot initialization and management
- **Key classes**: `ChrootManager`
- **Features**: Automated chroot creation, debootstrap wrapper, Wine installation, verification

#### `runner.py`
- **Purpose**: Execute Windows applications through Wine in chroot
- **Key classes**: `WineRunner`
- **Features**: Path conversion, X11 forwarding, sudo/pkexec support

#### `desktop.py`
- **Purpose**: Desktop integration (.desktop file management)
- **Key classes**: `DesktopManager`
- **Features**: Launcher creation, application discovery, icon integration

#### `icons.py`
- **Purpose**: Icon extraction from Windows executables
- **Key functions**: `extract_icon()`, `find_system_icon()`
- **Dependencies**: `wrestool`, `icotool` (icoutils package)

#### `utils.py`
- **Purpose**: Shared utilities
- **Key functions**: `linux_path_to_windows()`, `check_system_dependencies()`, `slugify()`

## Development Workflow

### Running from Source

```bash
# Option 1: Direct execution with uv
uv run wine-chroot --help

# Option 2: Activate virtual environment
source .venv/bin/activate
wine-chroot --help

# Option 3: Run module directly
python -m wine_chroot.cli --help
```

### Making Changes

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** to the source code

3. **Test your changes:**

```bash
# Run specific command
uv run wine-chroot config --show

# Test with verbose output
uv run wine-chroot -v run "C:\Windows\notepad.exe"
```

4. **Run tests:**

```bash
pytest
```

5. **Check code style:**

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### Adding New Features

#### Adding a New CLI Command

1. **Add command parser** in `cli.py`:

```python
# In build_parser()
mycommand_parser = subparsers.add_parser(
    "mycommand",
    help="Description of your command",
    formatter_class=RichHelpFormatter,
)
mycommand_parser.add_argument("--option", help="Option description")
```

2. **Implement command handler**:

```python
def cmd_mycommand(args: argparse.Namespace, config: Config) -> int:
    """Execute the 'mycommand' command."""
    console.print("[cyan]Running mycommand...[/]")
    # Implementation here
    return 0
```

3. **Register handler** in `main()`:

```python
commands = {
    "mycommand": cmd_mycommand,
    # ... other commands
}
```

#### Adding Configuration Options

1. **Update default configuration** in `config.py`:

```python
def _set_defaults(self) -> None:
    self.data = {
        "mysection": {
            "myoption": "default_value",
        },
    }
```

2. **Add property accessor**:

```python
@property
def myoption(self) -> str:
    """Get myoption value."""
    return self.get("mysection.myoption", "default_value")
```

3. **Update example config** in `create_example_config()`:

```python
example = '''
[mysection]
myoption = "default_value"  # Description
'''
```

## Code Style

### General Guidelines

- **Type hints**: Use type annotations for all function signatures
- **Docstrings**: Google-style docstrings for all public functions and classes
- **Line length**: Maximum 100 characters
- **Imports**: Organized by standard library, third-party, local (ruff handles this)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### Example Function

```python
def convert_path(linux_path: Path, chroot_path: Path) -> str:
    """Convert a Linux path to Windows format.

    Args:
        linux_path: Path object representing a file in the chroot
        chroot_path: Root path of the chroot

    Returns:
        Windows-style path string (e.g., "C:\\Program Files\\app.exe")

    Raises:
        ValueError: If path is not within the chroot

    Example:
        >>> convert_path(Path("/srv/debian-amd64/root/.wine/..."), Path("/srv/debian-amd64"))
        "C:\\Program Files\\app.exe"
    """
    if "drive_c/" in str(linux_path):
        after = str(linux_path).split("drive_c/", 1)[1]
        win = after.replace("/", "\\")
        return f"C:\\{win}"
    raise ValueError(f"Path not in Wine prefix: {linux_path}")
```

### Rich Console Output

Always use rich for user-facing output:

```python
from rich.console import Console

console = Console()

# Success messages
console.print("[green]Operation successful[/]")

# Errors
console.print("[bold red]Error:[/] Something went wrong")

# Warnings
console.print("[yellow]Warning:[/] Check your configuration")

# Info
console.print("[cyan]Info:[/] Processing files...")

# Dim/secondary text
console.print("[dim]This is less important[/]")
```

### Error Handling

```python
# User errors: Clear messages without stack traces
if not exe_path.exists():
    console.print(f"[bold red]Error:[/] File not found: {exe_path}")
    console.print("[yellow]Hint:[/] Check the path and try again")
    raise SystemExit(1)

# System errors: Show details in verbose mode
try:
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    if verbose:
        console.print_exception()
    else:
        console.print(f"[bold red]Error:[/] Command failed: {e}")
    return 1
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wine_chroot --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py

# Run specific test
pytest tests/test_cli.py::test_version

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Writing Tests

```python
# tests/test_utils.py
import pytest
from pathlib import Path
from wine_chroot.utils import linux_path_to_windows

def test_linux_path_to_windows():
    """Test path conversion from Linux to Windows format."""
    path = "/srv/debian-amd64/root/.wine/drive_c/Program Files/app.exe"
    result = linux_path_to_windows(path)
    assert result == "C:\\Program Files\\app.exe"

def test_linux_path_already_windows():
    """Test that Windows paths are left unchanged."""
    path = "C:\\Windows\\System32"
    result = linux_path_to_windows(path)
    assert result == "C:\\Windows\\System32"

@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary configuration file."""
    config_file = tmp_path / "wine-chroot.toml"
    config_file.write_text("""
[chroot]
name = "test-chroot"
path = "/tmp/test"
""")
    return config_file
```

### Integration Tests

Integration tests require actual system setup (chroot environment). Mark them appropriately:

```python
import pytest

@pytest.mark.integration
@pytest.mark.skipif(not Path("/srv/debian-amd64").exists(), reason="Chroot not available")
def test_wine_execution():
    """Test actual Wine execution in chroot."""
    # Test implementation
    pass
```

Run integration tests:

```bash
# Run only integration tests
pytest -m integration

# Skip integration tests
pytest -m "not integration"
```

## Building and Packaging

### Local Build

```bash
# Build source distribution and wheel
uv build

# Check build artifacts
ls -lh dist/
```

### Version Management

Update version in `pyproject.toml` and `src/wine_chroot/__init__.py`:

```python
# src/wine_chroot/__init__.py
__version__ = "1.1.0"
```

```toml
# pyproject.toml
[project]
version = "1.1.0"
```

### Creating a Release

1. **Update version** in both files
2. **Update CHANGELOG.md** (if present)
3. **Commit and tag**:

```bash
git add pyproject.toml src/wine_chroot/__init__.py
git commit -m "chore: bump version to 1.1.0"
git tag v1.1.0
git push origin main --tags
```

4. **Build and publish** (when ready for PyPI):

```bash
uv build
uv publish
```

## Contributing

### Contribution Workflow

1. **Fork the repository** on GitHub
2. **Clone your fork**:

```bash
git clone https://github.com/YOUR_USERNAME/wine_chroot.git
cd wine_chroot
```

3. **Set up development environment**:

```bash
uv pip install -e ".[dev]"
```

4. **Create a feature branch**:

```bash
git checkout -b feature/amazing-feature
```

5. **Make your changes** following the code style guidelines

6. **Add tests** for new functionality

7. **Run tests and linting**:

```bash
pytest
ruff check src/
ruff format src/
```

8. **Commit your changes**:

```bash
git commit -m "feat: add amazing feature"
```

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

9. **Push to your fork**:

```bash
git push origin feature/amazing-feature
```

10. **Create a Pull Request** on GitHub

### Pull Request Guidelines

- **Clear description**: Explain what your PR does and why
- **Link issues**: Reference any related issues (#123)
- **Tests**: Ensure all tests pass
- **Documentation**: Update docs if needed
- **Small PRs**: Keep changes focused and reviewable
- **Follow style**: Adhere to project code style

### Code Review Process

1. Maintainer reviews your PR
2. Address any feedback
3. Once approved, PR will be merged
4. Your contribution will be acknowledged in release notes

## Additional Resources

### Related Documentation

- [CLAUDE.md](../CLAUDE.md) - AI assistant development guidelines
- [README.md](../README.md) - User documentation
- [docs/chroot-setup.md](chroot-setup.md) - Chroot setup guide

### External Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Wine Documentation](https://www.winehq.org/documentation)
- [schroot Manual](https://manpages.debian.org/testing/schroot/schroot.1.en.html)
- [Rich Library](https://rich.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Code review**: Tag maintainers in your PRs for review

## License

This project is licensed under GPL-3.0-or-later. By contributing, you agree that your contributions will be licensed under the same terms.
