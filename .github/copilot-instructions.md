# Wine Chroot Project - Copilot Instructions

## Resumen del Proyecto

Proyecto con dos implementaciones: Python 3.10+ y Bash, diseñado para ejecutarse en Debian Linux.
Genera archivos .desktop para ejecutar aplicaciones Windows con Wine en entornos schroot.
Utiliza **uv** como gestor de paquetes y entornos Python.
Licencia: GNU GPL v3 o posterior.

**Arquitectura:**
- Scripts se ejecutan en el **HOST** (Debian ARM64 u otra arquitectura)
- Wine se ejecuta **DENTRO del CHROOT** (Debian amd64)
- Permite ejecutar aplicaciones Windows x86/amd64 en hosts con otras arquitecturas

## Dependencias

### Python
- **Versión mínima**: Python 3.10+
- **Dependencias Python**: Ninguna (solo biblioteca estándar)
- **Módulos usados**: argparse, re, shutil, subprocess, pathlib

### Sistema - En el HOST
- schroot (gestionar entornos chroot)
- icoutils (wrestool, icotool para extraer iconos)

### Sistema - Dentro del CHROOT
- wine (ejecutar aplicaciones Windows)
- El chroot debe estar configurado y listo para usar

## Estructura del Proyecto

- `python/` - Implementación en Python 3.10+
  - `make_wine_chroot_desktop.py` - Script principal
- `bash/` - Implementación en Bash
  - `make_wine_chroot_desktop.sh` - Script principal
- `pyproject.toml` - Configuración del proyecto Python (uv)
- `README.md` - Documentación completa

## Tecnologías Utilizadas

- Python 3.10+
- Bash 4.0+
- uv (gestor de paquetes Python)
- Debian Linux

## Comandos Principales

### Python con uv

```bash
# Ejecutar script Python
uv run python/make_wine_chroot_desktop.py

# Agregar dependencias
uv add <paquete>

# Crear entorno virtual
uv venv

# Instalar proyecto
uv pip install -e .
```

### Bash

```bash
# Ejecutar script Bash
./bash/make_wine_chroot_desktop.sh

# Dar permisos de ejecución
chmod +x bash/make_wine_chroot_desktop.sh
```

## Mejores Prácticas

- Usar uv para todas las operaciones con Python
- Mantener compatibilidad con Python 3.10+
- Scripts Bash con `set -e` y `set -u`
- Documentar en español
- Probar en Debian Linux
