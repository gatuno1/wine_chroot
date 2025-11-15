# Configuración de un Entorno Chroot con Wine para ARM64

Este documento describe cómo ejecutar aplicaciones Windows x86/x64 en un sistema Debian Trixie ARM64 (por ejemplo, Orange Pi 5 Plus) usando un entorno chroot amd64 con Wine x64/x86 completo.

El objetivo es reemplazar la necesidad de emuladores parciales (como Box64 o FEX-Emu) mediante un entorno chroot real con soporte multi-arquitectura i386+amd64, ejecutado sobre QEMU user-static.

> **Nota**: Este documento describe el proceso manual. Para una instalación automatizada, puedes usar el comando `wine-chroot init`. Consulta el `README.md` para más detalles.

## Arquitectura del Sistema

| Componente             | Rol                                                | Descripción                                |
| ---------------------- | -------------------------------------------------- | ------------------------------------------ |
| **Host**               | Debian Trixie ARM64                                | Sistema operativo base (físico)            |
| **Chroot**             | Debian Trixie AMD64                                | Entorno de usuario emulado                 |
| **Emulación**          | `qemu-user-static` + `binfmt-support`              | Traduce llamadas de amd64 a ARM64          |
| **Gestor**             | `schroot`                                          | Controla sesiones y montajes (bind-mounts) |
| **Software Principal** | `wine`, `wine64`, `wine32`, `winetricks`, `q4wine` | Ejecuta y gestiona apps de Windows         |

## Guía de Instalación

### 1. Preparar el Entorno en el Host (ARM64)

Instala las herramientas necesarias en tu sistema ARM64:

```bash
sudo apt install debootstrap schroot qemu-user-static binfmt-support
```

- `debootstrap`: Crea un sistema Debian base.
- `schroot`: Administra entornos chroot.
- `qemu-user-static`: Permite ejecutar binarios de otra arquitectura.
- `binfmt-support`: Integra `qemu-user-static` con el kernel para ejecución transparente.

### 2. Crear el sistema base (amd64)

Crea el directorio para el chroot y descarga el sistema base de Debian:

```bash
sudo debootstrap --arch=amd64 trixie /srv/debian-amd64 http://deb.debian.org/debian
```

donde `debian-amd64` es el nombre elegido para el entorno chroot, y:

- `--arch=amd64`: Especifica la arquitectura del chroot.
- `trixie`: La versión de Debian a instalar.
- `/srv/debian-amd64`: El directorio donde se alojará el chroot.

### 3. Configurar `schroot`

Crea el archivo de configuración para tu chroot en `/etc/schroot/chroot.d/debian-amd64.conf`:

```ini
[debian-amd64]
description=Debian Trixie amd64 chroot
directory=/srv/debian-amd64
type=directory
users=<tu_usuario>
root-users=<tu_usuario>
personality=linux
preserve-environment=true
```

- Reemplaza `<tu_usuario>` con tu nombre de usuario en el sistema host.
- `directory` apunta a la ruta del sistema chroot creado, usando el nombre del chroot.
- `personality=linux`: Asegura la compatibilidad del entorno.
- `preserve-environment=true`: Propaga variables de entorno como `DISPLAY` y `HOME` del host al chroot.

### 4. Configurar `fstab` del Chroot

Define los puntos de montaje que el chroot compartirá con el host. Edita `/etc/schroot/default/fstab`:

```fstab
# fstab: static file system information for chroots.
# <file system> <mount point>   <type>  <options>  <dump>  <pass>
/dev            /dev            none    rw,bind    0       0
/dev/pts        /dev/pts        none    rw,bind    0       0
/home           /home           none    rw,bind    0       0
/proc           /proc           none    rw,bind    0       0
/sys            /sys            none    rw,bind    0       0
/tmp            /tmp            none    rw,bind    0       0
/tmp/.X11-unix  /tmp/.X11-unix  none    rw,bind    0       0
```

### 5. Entrar y Configurar el Chroot

Accede al chroot para configurarlo:

```bash
sudo schroot -c debian-amd64
```

Una vez dentro, ejecuta los siguientes comandos:

**a. Configurar locales y repositorios:**

```bash
apt update
apt install locales gnupg2 wget
dpkg-reconfigure locales  # Selecciona tu localización (ej. es_CL.UTF-8, en_US.UTF-8)
```

**b. Editar `/etc/apt/sources.list`:**
Asegúrate de que tu `sources.list` contenga los repositorios `main`, `contrib`, `non-free` y `non-free-firmware` para Trixie.

```text
# Main
deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware
# deb-src http://deb.debian.org/debian trixie main contrib non-free non-free-firmware

# Actualizaciones puntuales
deb http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware
# deb-src http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware

# Seguridad
deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
# deb-src http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware

# Backports
deb http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware
# deb-src http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware
```

**c. Habilitar arquitectura i386:**
Esto es crucial para el soporte de aplicaciones de 32 bits.

```bash
dpkg --add-architecture i386
apt update
```

**d. Instalar Wine y herramientas:**

```bash
apt install -y wine wine32 wine64 winetricks wine-binfmt fonts-wine q4wine --install-recommends
```

donde:

- `wine`, `wine32`, `wine64`: Ejecutores de aplicaciones Windows.
- `winetricks`: Script para instalar librerías y componentes adicionales.
- `fonts-wine`: Fuentes tipográficas comunes para aplicaciones Windows.
- `q4wine`: Interfaz gráfica para gestionar configuraciones de Wine.

**e. (Opcional) Instalar desde el repositorio de WineHQ:**
Para obtener una versión más reciente de Wine.

```bash
wget -nc https://dl.winehq.org/wine-builds/winehq.key
apt-key add winehq.key
echo "deb https://dl.winehq.org/wine-builds/debian/ trixie main" > /etc/apt/sources.list.d/winehq.list
apt update
apt install --install-recommends winehq-stable
```

**f. Verificar instalación de Wine:**

```bash
# Muestra la versión instalada de Wine
wine --version
# Configura Wine por primera vez
winecfg
# Prueba una aplicación simple
wine notepad
```

**g. Salir del chroot:**

```bash
exit
```

## Modos de Instalación de Wine

### A. Instalación por Usuario (Recomendado)

Este modo aísla el entorno de Wine para cada usuario, lo que evita conflictos.

**1. Crear el usuario dentro del chroot:**
Asegúrate de que el nombre de usuario coincida con el del host.

```bash
# Estando dentro del chroot
adduser tu_usuario
usermod -aG sudo tu_usuario  # Añadir al grupo sudo para permisos
```

**2. Inicializar Wine como usuario:**
Sal del chroot (`exit`) y vuelve a entrar como el usuario recién creado para generar su prefijo de Wine.

```bash
# Desde el host
sudo schroot -c debian-amd64 --user=tu_usuario -- winecfg
```

Esto creará el prefijo en `/home/tu_usuario/.wine` dentro del chroot.

### B. Instalación Global (Modo Root)

Menos recomendado. Wine se ejecuta como `root` y el prefijo se almacena en `/root/.wine` dentro del chroot. Es más simple pero menos seguro, y propenso a conflictos.

```bash
# Desde el host
sudo schroot -c debian-amd64 -- winecfg
```

## Integración con el Escritorio

### 1. Configurar `sudoers` para Ejecución sin Contraseña

Para que los accesos directos del menú no pidan contraseña al usar `schroot`, añade una regla a `sudoers`.

**Ejecuta `sudo visudo` en el host** y agrega la siguiente línea, reemplazando `<tu_usuario>` con tu nombre de usuario:

```text
<tu_usuario> ALL=(ALL) NOPASSWD: /usr/bin/schroot
```

### 2. Crear Accesos Directos

El script `wine-chroot` (o el script manual `make_wine_chroot_desktop.py`) puede generar archivos `.desktop` para tus aplicaciones. Estos archivos ejecutan la aplicación de Windows a través del chroot.

**Ejemplo de uso del script:**

```bash
wine-chroot desktop \
  --exe "/srv/debian-amd64/home/<tu_usuario>/.wine/drive_c/Program Files/MiApp/app.exe" \
  --name "Mi Aplicación (Wine)"
```

Esto creará un lanzador en el menú de aplicaciones de tu escritorio, donde `<tu_usuario>` es tu nombre de usuario en el host.

### 3. Script Opcional de Ejecución Manual (`winegui`)

Si prefieres lanzar aplicaciones desde la terminal, puedes crear un script auxiliar.

Crea el archivo `~/winegui.sh`:

```bash
#!/usr/bin/env bash
# Script para ejecutar comandos de Wine dentro del chroot como tu usuario
CHROOT_NAME="debian-amd64"
CHROOT_USER="$(whoami)"

# Ejecuta el comando en el chroot
sudo schroot -c "$CHROOT_NAME" --user="$CHROOT_USER" -- wine "$@"
```

Dale permisos y muévelo a una ruta accesible:

```bash
chmod +x ~/winegui.sh
sudo mv ~/winegui.sh /usr/local/bin/winegui
```

**Ejemplo de uso:**

```bash
winegui "C:\Program Files\Notepad++\notepad++.exe"
```

## Resumen del Resultado

- Un entorno `chroot` amd64 funcional en un host ARM64.
- Wine con soporte para 32 y 64 bits instalado dentro del chroot.
- Aislamiento de prefijos de Wine por usuario para mayor estabilidad.
- Integración transparente con el escritorio mediante accesos directos y ejecución sin contraseña.
- Capacidad de ejecutar software de Windows x86/x64 de forma nativa en ARM64 sin emuladores de sistema completo.

## Referencias Externas

- [Guía oficial de Wine para Debian/Ubuntu](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu#preparation)
- [Wiki de Debian sobre Wine](https://wiki.debian.org/Wine)
- [README.debian de Wine en Salsa](https://salsa.debian.org/wine-team/wine/raw/master/debian/README.debian)
