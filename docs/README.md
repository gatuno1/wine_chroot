# Wine Chroot Documentation

Welcome to the Wine Chroot documentation! This directory contains comprehensive guides for using and developing Wine Chroot.

## 📚 Documentation Index

### User Documentation

- **[Main README](../README.md)** - Start here! Overview, installation, and basic usage
  - Features and architecture
  - Quick start guide
  - Common usage examples
  - Troubleshooting

- **[Chroot Setup Guide](chroot-setup.md)** - Detailed instructions for creating the chroot environment
  - System architecture overview
  - Step-by-step installation
  - Configuration details
  - Wine installation inside chroot
  - (Spanish: "Notas de creación ambiente chroot")

### Developer Documentation

- **[Development Guide](DEVELOPMENT.md)** - Everything you need to contribute
  - Development environment setup
  - Project architecture
  - Code style guidelines
  - Testing framework
  - Contributing workflow
  - Building and packaging

- **[CLAUDE.md](../CLAUDE.md)** - AI assistant development guidelines
  - Project vision and principles
  - Design decisions (e.g., sudo vs pkexec)
  - Implementation phases
  - Future enhancements

### Configuration

- **[Example Config](../wine-chroot.toml.example)** - Sample configuration file
  - All available options
  - Default values
  - Comments explaining each setting

## 🎯 Quick Navigation

**I want to...**

- **Use wine-chroot** → [Main README](../README.md)
- **Set up the chroot** → [Chroot Setup Guide](chroot-setup.md)
- **Contribute code** → [Development Guide](DEVELOPMENT.md)
- **Report a bug** → [GitHub Issues](https://github.com/gatuno/wine_chroot/issues)
- **Ask a question** → [GitHub Discussions](https://github.com/gatuno/wine_chroot/discussions)

## 📖 Documentation Standards

All documentation in this project follows these principles:

- **Clear and concise**: Direct language, minimal jargon
- **Example-driven**: Code examples for every feature
- **Up-to-date**: Maintained alongside code changes
- **Accessible**: Multiple languages when appropriate (Spanish/English)

## 🌐 Languages

- **English**: Primary language for all documentation
- **Spanish**: Available for [Chroot Setup Guide](chroot-setup.md)

## 🔗 External Resources

- [Wine Documentation](https://www.winehq.org/documentation)
- [Debian schroot Documentation](https://manpages.debian.org/testing/schroot/schroot.1.en.html)
- [QEMU User Emulation](https://qemu-project.gitlab.io/qemu/user/main.html)
- [uv Package Manager](https://docs.astral.sh/uv/)

## 📝 Contributing to Documentation

Found an error or want to improve the docs? Contributions are welcome!

1. Fork the repository
2. Make your changes to the relevant `.md` file
3. Submit a pull request

See the [Development Guide](DEVELOPMENT.md) for more details on contributing.

## License

Documentation is licensed under GPL-3.0-or-later, same as the code.
