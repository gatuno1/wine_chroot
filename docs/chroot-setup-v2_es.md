# Configuración de un Entorno Chroot con Wine para ARM64 - Versión 2 (Simplificada)

Este documento describe cómo ejecutar aplicaciones Windows x86/x64 en un sistema Debian Trixie ARM64 (por ejemplo, Orange Pi 5 Plus) usando un entorno chroot amd64 con Wine x64/x86 completo.

**⚡ Versión 2 - Cambios principales:**
- ✅ Usa `preserve-environment=true` en schroot para heredar variables del host automáticamente
- ✅ Script `run-chroot` más simple (solo configura XDG_RUNTIME_DIR y WINEPREFIX)
- ✅ Comandos gráficos de Wine funcionan directamente desde dentro del chroot (opcional)
- ✅ Nombre del chroot: `alt-alt-debian-amd64` (para testing sin afectar configuración existente)

El objetivo es reemplazar la necesidad de emuladores parciales (como Box64 o FEX-Emu) mediante un entorno chroot real con soporte multi-arquitectura i386+amd64, ejecutado sobre QEMU user-static.

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

donde los paquetes son:

- `debootstrap`: Crea un sistema Debian base.
- `schroot`: Administra entornos chroot.
- `qemu-user-static`: Permite ejecutar binarios de otra arquitectura.
- `binfmt-support`: Integra `qemu-user-static` con el kernel para ejecución transparente.

### 2. Crear el sistema base (amd64)

Crea el directorio para el chroot y descarga el sistema base de Debian:

```bash
sudo debootstrap --arch=amd64 trixie /srv/alt-alt-debian-amd64 http://deb.debian.org/debian
```

donde `alt-alt-debian-amd64` es el nombre elegido para el entorno chroot (v2 de testing), y:

- `--arch=amd64`: Especifica la arquitectura del chroot.
- `trixie`: La versión de Debian a instalar.
- `/srv/alt-alt-debian-amd64`: El directorio donde se alojará el chroot.

### 3. Configurar `schroot`

Crea el archivo de configuración para tu chroot en `/etc/schroot/chroot.d/alt-alt-debian-amd64.conf`:

```ini
[alt-alt-debian-amd64]
description=Debian amd64 chroot virtual environment (v2 - simplified)
directory=/srv/alt-alt-debian-amd64
type=directory
# Usuarios permitidos
users=<tu_usuario>
groups=<tu_usuario>
root-users=<tu_usuario>
personality=linux
# ⚡ CLAVE: Heredar variables del host (DISPLAY, XAUTHORITY, etc.)
preserve-environment=true
```

- Reemplaza `<tu_usuario>` con tu nombre de usuario en el sistema host arm64.
- `directory` apunta a la ruta del sistema chroot creado, usando el nombre del chroot.
- `personality=linux`: Asegura la compatibilidad del entorno.
- **`preserve-environment=true`**: Propaga variables de entorno como `DISPLAY`, `XAUTHORITY`, `LANG` del host al chroot automáticamente.

### 4. Configurar `fstab` del Chroot

Define los puntos de montaje que el chroot compartirá con el host. Edita `/etc/schroot/default/fstab`:

```fstab
# fstab: static file system information for chroots.
# <file system> <mount point>   <type>  <options>  <dump>  <pass>
# habilitar acceso a dispositivos para wine
/dev            /dev            none    rw,bind    0       0
# habilitar pseudo-terminales para wine
/dev/pts        /dev/pts        none    rw,bind    0       0
# habilitar acceso a home del usuario
/home           /home           none    rw,bind    0       0
# habilitar acceso a sistema de archivos virtuales
/proc           /proc           none    rw,bind    0       0
/run            /run            none    rw,bind    0       0
/sys            /sys            none    rw,bind    0       0
/tmp            /tmp            none    rw,bind    0       0
# habilitar acceso a sockets X11 para aplicaciones gráficas
/tmp/.X11-unix  /tmp/.X11-unix  none    rw,bind    0       0
```

**Nota importante sobre `/run` y `/tmp`:** Aunque `/run` está configurado como bind-mount, schroot en realidad crea un tmpfs nuevo en lugar de bind-montar el `/run` del host. Esto causa problemas de ownership con directorios como `/run/user/$UID`. Por esta razón, el script `run-chroot` usa `/tmp/runtime-$USER` en lugar de `/run/user/$UID`, ya que `/tmp` sí funciona correctamente preservando permisos y ownership.

### 5. Probar que schroot ve el ambiente

- **Listar el ambiente dentro del schroot**

  Desde el host, ejecuta:

  ```bash
  $ schroot --list
  chroot:alt-debian-amd64
  ```

- **Verificar las arquitecturas**

  Desde el host, ejecuta:

  ```bash
  # arquitectura del host
  $ uname -m
  aarch64
  # arquitectura dentro del ambiente chroot 
  $ sudo schroot -c alt-debian-amd64 -- uname -m
  x86_64
  ```

  El primero muestra 'aarch64' que es arm64 para este caso, mientras que la emulada es 'x86_64'.

- **Listar sesiones activas**

   Inicia una sesión interactiva en el chroot:

   ```bash
   sudo schroot -c alt-debian-amd64
   ```

   Luego, en otra terminal del host, lista las sesiones activas:

   ```bash
   $ schroot --list --all-sessions
   session:alt-debian-amd64-cc4874c1-892f-4627-a9c7-5b9956bd7de7
   ```

#### ¿Como 'reiniciarlo' si hay problemas?

- **Finalizar todas las sesiones activas**

  Desde el host, ejecuta:

  ```bash
  sudo schroot --end-session --all-sessions
  ```

- **Finalizar sesión específica**

  Desde el host, ejecuta:

  ```bash
  sudo schroot --end-session -c <nombre-sesion>
  ```

- **Matar procesos huérfanos del chroot**

  Esto ayuda muchísimo cuando Wine dejó procesos colgados.

  ```bash
  sudo schroot -c alt-debian-amd64 -- pkill -9 wine
  ```

- **Limpiar lockfiles**

  ```bash
  sudo rm -f '/run/schroot/*' '/var/lib/schroot/session/*' '/var/lib/schroot/mount/*' 2>/dev/null
  ```

- **Volver a cargar la configuración**: como “reiniciar” schroot

  Si cambiaste archivos en:

  - `/etc/schroot/chroot.d/*`
  - `/etc/schroot/schroot.conf`
  - `/etc/schroot/default/*`

  Entonces:

  ```bash
  sudo schroot --debug-level=notice --info
  ```

  Si quieres asegurarte:

  ```bash
  sudo schroot -c alt-debian-amd64 -- true
  ```

  Si entra sin errores, la configuración ya está aplicada.

- **Reinicio “completo” del sistema chroot**: equivalente a reboot**

  ```bash
  sudo schroot --end-session --all-sessions
  sudo umount -R /srv/alt-debian-amd64
  sudo mount -a   # vuelve a montar bind mounts incluyendo los del chroot
  ```

### 6. Entrar y Configurar el Chroot

Accede al chroot para configurarlo, usando el shell por defecto:

```bash
sudo schroot -c alt-debian-amd64
```

Una vez dentro, ejecuta los siguientes comandos:

**a. Configurar locales y repositorios:**

```bash
apt update
# instalar locales primero para evitar problemas con paquetes que dependen de la localización
apt install locales
dpkg-reconfigure locales  # Selecciona tu localización (ej. es_CL.UTF-8, en_US.UTF-8)
apt install gnupg2 wget
```

debería tener algo así en `/etc/environment`:

```text
LANG="es_CL.UTF-8"
LC_ALL="es_CL.UTF-8"
```

**b. Editar `/etc/apt/sources.list`:**
Asegúrate de que tu `sources.list` contenga los repositorios `main`, `contrib`, `non-free` y `non-free-firmware` para Trixie.

```source-list
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

Verifica que esté activa:

```bash
$ dpkg --print-foreign-architectures
i386
```

**d. Instalar Wine y herramientas:**

```bash
apt install -y wine wine32 wine64 winetricks wine-binfmt fonts-wine q4wine xterm icoutils --install-recommends
```

donde:

- `wine`, `wine32`, `wine64`: Ejecutores de aplicaciones Windows.
- `winetricks`: Script para instalar librerías y componentes adicionales.
- `fonts-wine`: Fuentes tipográficas comunes para aplicaciones Windows.
- `q4wine`: Interfaz gráfica para gestionar configuraciones de Wine.
- `xterm`: Terminal para ejecutar aplicaciones gráficas de Wine.
- `icoutils`: Herramientas para extraer iconos de archivos ejecutables de Windows.

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
```

Deberías ver algo como `wine-10.0 (Debian 10.0~repack-6)`.

**IMPORTANTE:** No ejecutes comandos gráficos de Wine (`winecfg`, `q4wine`, `wine notepad`) desde dentro del chroot directamente, ya que no tendrán acceso al servidor X11 ni las variables de entorno necesarias. En su lugar, usa el script `run-chroot` desde el host (ver secciones siguientes).

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
adduser <tu_usuario>
usermod -aG sudo <tu_usuario>  # Añadir al grupo sudo para permisos
```

**2. Inicializar Wine como usuario:**

⚠️ **IMPORTANTE:** Primero debes instalar el script `run-chroot-v2` (ver [sección siguiente](#1-crear-script-de-integración-x11-con-el-host-versión-simplificada)) antes de inicializar Wine, ya que este script maneja automáticamente todas las variables de entorno necesarias.

Una vez instalado el script `run-chroot-v2`, inicializa Wine desde el host:

```bash
# Inicializar Wine por primera vez (abrirá interfaz gráfica de configuración)
run-chroot-v2 winecfg
```

Esto creará el prefijo en `/home/<tu_usuario>/.wine` dentro del chroot, con todos los permisos y variables de entorno correctos.

**¿Qué hace `run-chroot-v2` automáticamente?**
- Crea el directorio runtime `/tmp/runtime-<tu_usuario>` con permisos 700
- Hereda `DISPLAY` y `XAUTHORITY` del host (gracias a `preserve-environment=true`)
- Configura `XDG_RUNTIME_DIR` y `WINEPREFIX` correctamente
- Ejecuta el comando como tu usuario (no como root)

### B. Instalación Global (Modo Root)

Menos recomendado. Wine se ejecuta como `root` y el prefijo se almacena en `/root/.wine` dentro del chroot. Es más simple pero menos seguro, y propenso a conflictos.

```bash
# Desde el host
sudo schroot -c alt-debian-amd64 -- winecfg
```

## Integración con el Escritorio

### 1. Crear script de integración X11 con el host (Versión Simplificada)

**Contenido del script (run-chroot-v2.sh):**

```bash
#!/usr/bin/env bash
# Script simplificado para ejecutar comandos dentro del chroot

# Nombre default del chroot
CHROOT_NAME="${CHROOT_NAME:-alt-debian-amd64}"

# Usuario objetivo (el que ejecutará Wine)
USER="${USER:-$(whoami)}"

# Directorio de runtime para aplicaciones Qt/KDE
RUNTIME_DIR="/tmp/runtime-$USER"

# Crear directorio en el HOST si no existe
if [ ! -d "$RUNTIME_DIR" ]; then
    mkdir -p "$RUNTIME_DIR"
    chmod 700 "$RUNTIME_DIR"
fi

# Permitir conexiones locales al servidor X
xhost +SI:localuser:"$USER" >/dev/null 2>&1 || xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot
# Con preserve-environment=true, DISPLAY y XAUTHORITY se heredan automáticamente
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    "$@"
```

### 2. Instalar el script run-chroot-v2 en el sistema

Crea el script y hazlo ejecutable:

```bash
# Crear el script run-chroot-v2
cat > /tmp/run-chroot-v2.sh << 'EOF'
#!/usr/bin/env bash
# Script simplificado para ejecutar comandos dentro del chroot

# Nombre default del chroot
CHROOT_NAME="${CHROOT_NAME:-alt-debian-amd64}"

# Usuario objetivo (el que ejecutará Wine)
USER="${USER:-$(whoami)}"

# Directorio de runtime para aplicaciones Qt/KDE
RUNTIME_DIR="/tmp/runtime-$USER"

# Crear directorio en el HOST si no existe
if [ ! -d "$RUNTIME_DIR" ]; then
    mkdir -p "$RUNTIME_DIR"
    chmod 700 "$RUNTIME_DIR"
fi

# Permitir conexiones locales al servidor X
xhost +SI:localuser:"$USER" >/dev/null 2>&1 || xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot
# Con preserve-environment=true, DISPLAY y XAUTHORITY se heredan automáticamente
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    "$@"
EOF

# Copiar al sistema
sudo cp /tmp/run-chroot-v2.sh /usr/local/bin/run-chroot-v2
sudo chmod +x /usr/local/bin/run-chroot-v2
```

**Probar Wine con el script run-chroot:**

Ahora puedes ejecutar aplicaciones Windows desde cualquier terminal del host:

```bash
# Verificar versión de Wine
run-chroot-v2 wine --version

# Configurar Wine por primera vez (abrirá interfaz gráfica)
run-chroot-v2 winecfg

# Probar una aplicación simple
run-chroot-v2 wine notepad

# Ejecutar q4wine (gestor gráfico de Wine) - opcional
run-chroot-v2 q4wine
```

**Ejemplo con aplicación Windows instalada:**

```bash
# Si tienes Notepad++ instalado en Wine
run-chroot-v2 wine "C:\\Program Files\\Notepad++\\notepad++.exe"
```

### 3. Configurar `sudoers` para Ejecución sin Contraseña (Opcional)

Para que los accesos directos del menú no pidan contraseña al usar `schroot`, añade una regla a `sudoers`.

**Ejecuta `sudo visudo` en el host** y agrega las siguientes líneas, reemplazando `<tu_usuario>` con tu nombre de usuario:

```sudoers
# para no usar sudo al llamar integración con escritorio
<tu_usuario> ALL=(ALL) NOPASSWD: /usr/local/bin/run-chroot
# no pedir contraseña al usar `schroot` para entrar al shell del ambiente
<tu_usuario> ALL=(ALL) NOPASSWD: /usr/bin/schroot
```

- La primera línea permite ejecutar el script `run-chroot` sin contraseña, que es el que se usará en los accesos directos.
- La segunda línea permite usar `schroot` sin contraseña, útil para abrir una terminal dentro del chroot si es necesario.

## Configuración Adicional (Opcional)

### Instalar emulador de terminal mejorado para Wine

Aunque Wine puede funcionar con `xterm`, es recomendable instalar un emulador de terminal más avanzado como `gnome-terminal` o `konsole` para una mejor experiencia.

```bash
# Dentro del chroot
sudo schroot -c alt-debian-amd64
apt install -y gnome-terminal
# o
apt install -y konsole
# o
apt install -y mate-terminal
# o
apt install -y lxterminal
exit
```

### Configurar Q4Wine - cambiar terminal predeterminado

Una vez instalado el script `run-chroot` y un terminal mejorado, puedes configurar Q4Wine:

a) Abre Q4Wine usando el script `run-chroot`:

  ```bash
  run-chroot-v2 q4wine
  ```

  **Nota sobre errores de QStandardPaths:** El script `run-chroot` configura automáticamente `XDG_RUNTIME_DIR` apuntando a `/tmp/runtime-$USER`, evitando así problemas de ownership que ocurren con `/run/user/$UID` en entornos schroot. Por lo tanto, no deberías experimentar errores como "QStandardPaths: runtime directory '/run/user/1000' is not owned by UID 1000". Si aún así experimentas problemas, verifica que:

- El script `run-chroot` esté instalado correctamente en `/usr/local/bin/run-chroot`
- El directorio `/tmp` sea accesible y tenga permisos de escritura
- El usuario tenga permisos para crear directorios en `/tmp`

b) Ve a **Editar** > **Configuración** (o "Edit > Options" si está en inglés).

En la pestaña **Programas** o **Paths** (según el idioma), cambiar la ruta del terminal y los argumentos de la consola:

| Terminal       | Ruta típica             | Parámetros |
| -------------- | ----------------------- | :--------: |
| xterm          | /usr/bin/xterm          |   -e %s    |
| gnome-terminal | /usr/bin/gnome-terminal |   -- %s    |
| konsole        | /usr/bin/konsole        |   -e %s    |
| mate-terminal  | /usr/bin/mate-terminal  |   -e %s    |
| lxterminal     | /usr/bin/lxterminal     |   -e %s    |

**Ejemplo:** si hubiera instalado *gnome-terminal*, debería cambiar en campo **Console App** de `/usr/bin/xterm` a `/usr/bin/gnome-terminal` y en **Console Args** de `-e %s` a `-- %s`.

Guarda los cambios y continúa.

## Crear Accesos Directos del Escritorio

### a. Crear un archivo `.desktop` para una aplicación Windows

Se puede crear un archivo `.desktop` para cada aplicación Windows que desees ejecutar desde el menú de aplicaciones de tu escritorio. Aquí tienes un ejemplo de cómo crear un acceso directo para Notepad++:

Crea un archivo llamado `notepadpp.desktop` en `~/.local/share/applications/` con el contenido siguiente:

- Notar que debes ajustar las rutas, tanto del **ejecutable**, como del **icono** según tu instalación**:
  - Nota el uso de dobles barras invertidas (`\\`) en la ruta de Windows.
  - El icono lo puedes extraer del instalador de la aplicación como se muestra en [extraer iconos](#b-extraer-iconos-de-aplicaciones-windows), o usar uno genérico.

```ini
[Desktop Entry]
Name=Notepad++
Comment=Editor de texto Notepad++ ejecutado dentro del entorno Wine amd64 (schroot)
Exec=/usr/local/bin/run-chroot "C:\\Program Files\\Notepad++\\Notepad++.exe"
Icon=~/.local/share/icons/Notepad++.png
Terminal=false
Type=Application
StartupNotify=true
Categories=Utility;TextEditor;Wine;WindowsApps;
StartupWMClass=notepad++.exe
```

donde:

- `Name`: El nombre que aparecerá en el menú.
- `Comment`: Una breve descripción de la aplicación.
- `Exec`: La ruta al script `run-chroot` seguido del camino al ejecutable de la aplicación Windows.
- `Icon`: La ruta al icono que deseas usar para la aplicación. En este caso, se asume que has colocado un icono en `~/.local/share/icons/Notepad++.png`.
- `Terminal`: `false` indica que no se debe abrir una terminal al ejecutar la aplicación.
- `Type`: El tipo de entrada, en este caso una aplicación.
- `Categories`: Categorías para organizar la aplicación en el menú.
- `StartupNotify`: `true` permite que el sistema muestre notificaciones de inicio de la aplicación.
- `StartupWMClass`: El nombre de la clase de ventana para ayudar al gestor de ventanas a identificar la aplicación. El standard suele ser el nombre del ejecutable.

Esto creará un lanzador en el menú de aplicaciones de tu escritorio, donde `<tu_usuario>` es tu nombre de usuario en el host.

### b. Extraer iconos de aplicaciones Windows

[ ] **TODO:** corregir instrucciones para extraer iconos desde instaladores `.exe` o `.ico`

Ejecutando el instalador de la aplicación Windows dentro del chroot, puedes extraer los iconos usando herramientas como `wrestool` o `icotool` del paquete `icoutils` ya instalado dentro del ambiente chroot:

- Si se instala Notepad++ globalmente (en 'root'), el prefijo estará en `/root/.wine`.

  ```bash

  schroot -c alt-debian-amd64 -- wrestool -x -t14 "/srv/alt-debian-amd64/root/.wine/drive_c/Program Files/Notepad++/Notepad++.exe" -o /home/<tu-usuario>/Notepad++.ico
  sudo schroot -c alt-debian-amd64 -- sudo icotool -x /home/<tu-usuario>/Notepad++.ico -o /home/<tu-usuario>/.local/share/icons/Notepad++.png
  ```

- Si se instala como usuario, el prefijo estará en `/home/<tu-usuario>/.wine`.

  ```bash
  schroot -c alt-debian-amd64 --user=<tu-usuario> -- wrestool -x -t14 "/srv/alt-debian-amd64/home/<tu-usuario>/.wine/drive_c/Program Files/Notepad++/Notepad++.exe" -o /home/<tu-usuario>/Notepad++.ico
  sudo schroot -c alt-debian-amd64 --user=<tu-usuario> -- icotool -x /home/<tu-usuario>/Notepad++.ico -o /home/<tu-usuario>/.local/share/icons/Notepad++.png
  ```

### c. Refrescar el menú de aplicaciones

Ejecuta:

```bash
update-desktop-database ~/.local/share/applications
```

o simplemente cierra y abre sesión.

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
