# Notas de creación ambiente chroot

Este documento describe cómo ejecutar aplicaciones Windows x86/x64 en un sistema Debian Trixie ARM64 (por ejemplo, Orange Pi 5 Plus) usando un entorno chroot amd64 con Wine x64/x86 completo.

El objetivo es reemplazar la necesidad de emuladores parciales (como Box64 o CrossWine) mediante un entorno chroot real con soporte multi-arquitectura i386+amd64, ejecutado sobre QEMU user-static.

> **Nota**: Este documento describe el proceso manual. Para instalación automatizada, usa el comando `wine-chroot init`. Ver [README.md](../README.md) para más información.

## Arquitectura del sistema

| Componente             | Rol                                                | Descripción                         |
| ---------------------- | -------------------------------------------------- | ----------------------------------- |
| **Host**               | Debian Trixie ARM64                                | Sistema base físico                 |
| **Chroot**             | Debian Trixie AMD64                                | Entorno de usuario emulado          |
| **Emulación**          | `qemu-user-static` + `binfmt-support`              | Traduce llamadas amd64→ARM64        |
| **Gestor**             | `schroot`                                          | Control de sesiones y bind-mounts   |
| **Software principal** | `wine`, `wine64`, `wine32`, `winetricks`, `q4wine` | Ejecución y gestión de apps Windows |

## Resultado final

El host ARM64 puede ejecutar programas Windows x86/x64 mediante:

- Wine 64 + Wine 32 dentro de un chroot amd64 real.
- QEMU user static como capa de emulación.
- Integración X11 directa con el escritorio Cinnamon.
- Accesos directos con íconos, gestionados por script Python.

## Guía de instalación

### 1. Preparar el entorno en host ARM64

```bash
sudo apt install debootstrap schroot qemu-user-static binfmt-support
```

donde:

- `debootstrap`: Crea sistemas Debian mínimos.
- `schroot`: Gestiona entornos chroot con bind-mounts.
- `qemu-user-static`: Emula binarios amd64 en ARM64.
- `binfmt-support`: Permite ejecutar binarios de otras arquitecturas automáticamente.

### 2. Crear el sistema base amd64

```bash
sudo debootstrap --arch=amd64 trixie /srv/debian-amd64 http://deb.debian.org/debian
```

donde `debian-amd64` es el nombre que elegí para el entorno chroot, y:

- `--arch=amd64`: Especifica la arquitectura del sistema chroot.
- `trixie`: Versión de Debian a instalar.
- `/srv/debian-amd64`: Ruta donde se instalará el sistema chroot.
- `http://deb.debian.org/debian`: URL del repositorio Debian.

### 3. Configurar `schroot`

Editar el archivo `/etc/schroot/chroot.d/debian-amd64.conf` para añadir la configuración del ambiente *chroot*:

```ini
[debian-amd64]
description=Debian Trixie amd64 chroot
directory=/srv/debian-amd64
type=directory
users=gatuno
root-users=gatuno
personality=linux
preserve-environment=true
```

donde:

- `gatuno` es el nombre del usuario que tendrá acceso al chroot.
- `directory` apunta a la ruta del sistema chroot creado.
- `personality=linux` asegura que el entorno se comporte como un sistema Linux estándar (no linux64).

### 4. Configurar `fstab` para el ambiente *chroot*

Crear el archivo `/etc/schroot/default/fstab` con el siguiente contenido, para montar los sistemas de archivos necesarios dentro del ambiente *chroot*:

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

### 5. Entrar al entorno amd64

Para acceder al ambiente *chroot*, ejecutar desde el host ARM64:

```bash
sudo schroot -c debian-amd64
```

### 6. Configurar locales y repositorios

Ejecutar dentro del ambiente *chroot*:

```bash
apt update
apt install locales gnupg2 wget
dpkg-reconfigure locales     # seleccionar es_CL.UTF-8 y adicionalmente en_US.UTF-8
```

Asumiendo *Debian Trixie* como base para los repositorios, editar `/etc/apt/sources.list` y añadir:

```config
# Debian Trixie (testing / Debian 13) - repositorios principales
deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian trixie main contrib non-free non-free-firmware

# Actualizaciones puntuales
deb http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware

# Seguridad
deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
deb-src http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware

# Backports (útiles si algún paquete es muy nuevo, por ejemplo Wine o Mesa)
deb http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware
```

### 7. Habilitar arquitectura i386

Ejecutar dentro del ambiente *chroot*:

```bash
dpkg --add-architecture i386
apt update
```

### 8. Instalar Wine y herramientas relacionadas

Ejecutar dentro del ambiente *chroot*:

```bash
apt install -y wine wine32 wine64 winetricks wine-binfmt fonts-wine q4wine --install-recommends
```

donde:

- `wine`, `wine32`, `wine64`: Ejecutores de aplicaciones Windows.
- `winetricks`: Script para instalar librerías y componentes adicionales.
- `fonts-wine`: Fuentes tipográficas comunes para aplicaciones Windows.
- `q4wine`: Interfaz gráfica para gestionar configuraciones de Wine.

**Opcional**: repositorio WineHQ más reciente:

```bash
wget -nc https://dl.winehq.org/wine-builds/winehq.key
apt-key add winehq.key
echo "deb https://dl.winehq.org/wine-builds/debian/ trixie main" > /etc/apt/sources.list.d/winehq.list
apt update
apt install --install-recommends winehq-stable
```

### 9. Verificar instalación de Wine

Todavía dentro del ambiente *chroot*, ejecutar:

```bash
wine --version
winecfg
wine notepad
```

### 10. Salir del entorno *chroot*

Para salir del ambiente *chroot*, ejecutar:

```bash
exit
```

### 11. Crear accesos directos para aplicaciones Windows

El script Python `make_wine_chroot_desktop.py` genera accesos directos `.desktop` para ejecutar aplicaciones Windows dentro del chroot y extrae íconos vía wrestool + icotool.

```python
sudo schroot -c debian-amd64 -- wine "C:\Ruta\al\programa.exe"
```

Ejemplo de uso del script Python:

```bash
python3 make_wine_chroot_desktop.py \
  --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/Notepad++/notepad++.exe" \
  --name "Notepad++ (Wine chroot)" \
  --icon \
```

### 12. (Opcional) Script de Integración X11 con el host

Para facilitar la ejecución de aplicaciones Windows desde el host ARM64, se puede crear un script llamado `winegui.sh` con el siguiente contenido:

```bash
#!/usr/bin/env bash
xhost +local: >/dev/null 2>&1 || true
sudo schroot -c debian-amd64 -- env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY wine "$@"
```

donde:

- `DISPLAY` y `XAUTHORITY` se utilizan para permitir que las aplicaciones gráficas de Wine se muestren en el entorno gráfico del host ARM64.
- `"$@"` se utiliza para pasar todos los argumentos del script a la aplicación Wine.

Hacer el script ejecutable:

```bash
chmod +x winegui.sh
sudo mv ~/winegui.sh /usr/local/bin/winegui
```

Ejemplo de uso desde el host ARM64:

```bash
winegui "C:\Program Files\Notepad++\notepad++.exe"
```

## Resumen

Construir un entorno `chroot` Debian Trixie amd64 dentro de un host ARM64 usando `debootstrap`, `schroot` y `qemu-user-static`.
Dentro del chroot se instala Wine x64+x86, habilitando i386 y amd64.
Se montan `/home`, `/dev`, `/proc`, `/tmp` y `/tmp/.X11-unix` para compatibilidad gráfica.
Los programas se ejecutan mediante `sudo schroot -c debian-amd64 -- wine "C:\..."`.
Los accesos se generan automáticamente con `make_wine_chroot_desktop.py`, que extrae íconos del .exe.
Resultado: ejecución nativa de software Windows x86/x64 en ARM64 sin depender de Box64 ni CrossWine.

## Referencias externas

- [Guía oficial de Wine para Debian/Ubuntu](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu#preparation)
- [Wiki de Debian sobre Wine](https://wiki.debian.org/Wine)
- [README.debian de Wine en Salsa](https://salsa.debian.org/wine-team/wine/raw/master/debian/README.debian)
