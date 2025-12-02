#!/usr/bin/env bash
# Script para ejecutar comandos de Wine dentro del chroot

# Nombre default del chroot
CHROOT_NAME="${CHROOT_NAME:-debian-amd64}"
# Ruta default del chroot
CHROOT_PATH="${CHROOT_PATH:-/srv/$CHROOT_NAME}"
# Usuario actual
USER="${USER:-$(whoami)}"
# DISPLAY / XAUTHORITY desde el host
DISPLAY_VAR="${DISPLAY:-:0}"
XAUTH_VAR="${XAUTHORITY:-$HOME/.Xauthority}"
# Directorio de runtime para aplicaciones Qt/KDE
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$UID}"

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
xhost +SI:localuser:"$USER" >/dev/null 2>&1 || xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot con todas las variables de entorno necesarias
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    DISPLAY="$DISPLAY_VAR" \
    XAUTHORITY="$XAUTH_VAR" \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    wine "$@"
