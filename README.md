# Wine Chroot Project

Proyecto con dos implementaciones: Python 3.10+ y Bash, diseñado para ejecutarse en Debian Linux.

## Estructura del Proyecto

```asciiart
wine_chroot/
├── python/                            # Implementación en Python
│   ├── make_wine_chroot_desktop.py    # Script principal de Python
│   └── requirements.txt               # Dependencias de Python (legacy)
├── bash/                              # Implementación en Bash
│   └── make_wine_chroot_desktop.sh    # Script principal de Bash
├── .github/
│   └── copilot-instructions.md
├── pyproject.toml                     # Configuración del proyecto Python (uv)
├── .gitignore
└── README.md
```

## Requisitos del Sistema

### En el Host (donde se ejecutan estos scripts)

- **Sistema Operativo**: Debian Linux (o distribuciones basadas en Debian como Ubuntu)
- **Permisos**: Usuario con capacidad de ejecutar scripts y sudo
- **Schroot**: Para gestionar y acceder al entorno chroot
- **icoutils**: Herramientas para extraer iconos del .exe (wrestool, icotool)

### Dentro del Chroot (debian-amd64)

- **Wine**: Instalado dentro del schroot para ejecutar aplicaciones Windows
- El schroot debe estar configurado y listo para usar (se asume ya creado)

### Para la implementación Python

- **Python**: 3.10 o superior
- **Dependencias Python**: `rich`, `rich-argparse` (se instalan automáticamente con uv)
- **uv**: Gestor de paquetes Python ultrarrápido (opcional pero recomendado)

### Para la implementación Bash

- **Bash**: 4.0 o superior (normalmente preinstalado en Debian)

## Instalación en Debian

### 1. Instalar uv

```bash
# Instalar uv (recomendado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# O usando pip
pip install uv
```

### 2. Verificar versiones instaladas

```bash
# Verificar uv
uv --version

# Verificar Python
python3 --version

# Verificar Bash
bash --version
```

### 3. Instalar dependencias del sistema en el HOST

```bash
# Actualizar lista de paquetes
sudo apt update

# Instalar Python 3.10+ si no está disponible
sudo apt install python3

# Instalar herramientas necesarias en el host
sudo apt install schroot icoutils

# Verificar instalación
schroot --version
wrestool --version
icotool --version
```

### 4. Configurar Wine en el CHROOT

Wine debe estar instalado **dentro del schroot**, no en el host:

```bash
# Entrar al chroot
sudo schroot -c debian-amd64

# Dentro del chroot, instalar wine
apt update
apt install wine

# Verificar instalación
wine --version

# Salir del chroot
exit
```

**Nota:** Este README asume que ya tienes el schroot debian-amd64 creado y configurado. La creación del schroot se documentará en el futuro.

## Uso

### Implementación Python

El script genera archivos `.desktop` para lanzar aplicaciones Windows a través de Wine en un entorno schroot.

#### Sintaxis básica

```bash
uv run python/make_wine_chroot_desktop.py \
    --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe" \
    --name "Nombre de la Aplicación"
```

#### Opciones adicionales

```bash
# Con extracción de icono
uv run python/make_wine_chroot_desktop.py \
    --exe "/ruta/al/programa.exe" \
    --name "Mi Aplicación" \
    --icon

# Con schroot personalizado
uv run python/make_wine_chroot_desktop.py \
    --exe "/ruta/al/programa.exe" \
    --name "Mi Aplicación" \
    --schroot "mi-chroot"

# Ver todas las opciones
uv run python/make_wine_chroot_desktop.py --help
```

### Métodos de ejecución

#### Opción 1: Usando uv (Recomendado)

```bash
# Ejecutar directamente con uv
uv run python/make_wine_chroot_desktop.py --exe <ruta> --name <nombre>

# O si instalaste el proyecto
uv run wine-chroot --exe <ruta> --name <nombre>
```

#### Opción 2: Con entorno virtual de uv

```bash
# Crear entorno virtual con uv
uv venv

# Activar entorno virtual
source .venv/bin/activate

# Instalar el proyecto y dependencias
uv pip install -e .

# Ejecutar el script
python python/make_wine_chroot_desktop.py

# Desactivar entorno virtual cuando termines
deactivate
```

#### Opción 3: Ejecución directa (sin uv)

```bash
# Navegar al directorio python
cd python

# Ejecutar el script
python3 make_wine_chroot_desktop.py
```

### Implementación Bash

El script Bash proporciona la misma funcionalidad que la versión Python.

#### Uso básico

```bash
./bash/make_wine_chroot_desktop.sh \
    --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/App/app.exe" \
    --name "Nombre de la Aplicación"
```

#### Opciones del script Bash

```bash
# Con extracción de icono
./bash/make_wine_chroot_desktop.sh \
    --exe "/ruta/al/programa.exe" \
    --name "Mi Aplicación" \
    --icon

# Con schroot personalizado
./bash/make_wine_chroot_desktop.sh \
    --exe "/ruta/al/programa.exe" \
    --name "Mi Aplicación" \
    --schroot "mi-chroot"

# Ver todas las opciones
./bash/make_wine_chroot_desktop.sh --help
```

**Nota:** Asegúrate de que el script tenga permisos de ejecución:

```bash
chmod +x bash/make_wine_chroot_desktop.sh
```

## Solución de Problemas

### uv: "command not found"

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reiniciar terminal o recargar shell
source ~/.zshrc  # o ~/.bashrc
```

### Python: "command not found"

```bash
# Instalar Python 3
sudo apt install python3
```

### Bash: "Permission denied"

```bash
# Dar permisos de ejecución
chmod +x bash/make_wine_chroot_desktop.sh
```

### Python: Versión incorrecta

```bash
# Verificar versión instalada
python3 --version

# uv puede usar diferentes versiones de Python
uv python install 3.11
uv python pin 3.11
```

### Herramientas faltantes en el HOST

```bash
# Si wrestool o icotool no están disponibles
sudo apt install icoutils

# Si schroot no está disponible
sudo apt install schroot
```

### Wine no funciona dentro del chroot

```bash
# Entrar al chroot
sudo schroot -c debian-amd64

# Verificar si wine está instalado
which wine

# Si no está, instalarlo
apt update
apt install wine

# Probar wine
wine --version

# Salir del chroot
exit
```

## Licencia

Este proyecto se distribuye bajo los términos de la **GNU General Public License**
versión 3 (o, a tu elección, cualquier versión posterior). Consulta el archivo
`LICENSE` para obtener el texto completo de la licencia.

Al contribuir con este repositorio aceptas que tus aportaciones se publicarán
bajo la misma licencia GPL-3.0-or-later.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, asegúrate de que tu código funcione correctamente en Debian Linux antes de enviar cambios.
