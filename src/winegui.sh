#!/usr/bin/env bash
# Script para ejecutar comandos de Wine dentro del chroot

# Nombre del chroot
CHROOT_NAME="${CHROOT_NAME:-debian-amd64}"

# Ruta del chroot
CHROOT_PATH="${CHROOT_PATH:-/srv/$CHROOT_NAME}"

# Directorio de runtime para aplicaciones Qt/KDE (evita errores de QStandardPaths)
RUNTIME_DIR="/tmp/runtime-$(id -u)"

# Crear directorio de runtime dentro del chroot si no existe
if [ ! -d "$CHROOT_PATH$RUNTIME_DIR" ]; then
    mkdir -p "$CHROOT_PATH$RUNTIME_DIR" 2>/dev/null || \
        sudo mkdir -p "$CHROOT_PATH$RUNTIME_DIR"
    chmod 700 "$CHROOT_PATH$RUNTIME_DIR" 2>/dev/null || \
        sudo chmod 700 "$CHROOT_PATH$RUNTIME_DIR"
    chown "$(id -u):$(id -g)" "$CHROOT_PATH$RUNTIME_DIR" 2>/dev/null || \
        sudo chown "$(id -u):$(id -g)" "$CHROOT_PATH$RUNTIME_DIR"
fi

# Permitir conexiones locales al servidor X
xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot con todas las variables de entorno necesarias
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    DISPLAY="$DISPLAY" \
    XAUTHORITY="$XAUTHORITY" \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    wine "$@"
