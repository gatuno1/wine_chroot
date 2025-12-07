#!/usr/bin/env bash
# Script para ejecutar comandos dentro del chroot

# Nombre default del chroot
CHROOT_NAME="${CHROOT_NAME:-debian-amd64}"
# Ruta default del chroot
CHROOT_PATH="${CHROOT_PATH:-/srv/$CHROOT_NAME}"
# Usuario objetivo (el que ejecutará Wine)
USER="${USER:-$(whoami)}"
# Obtener UID y GID del usuario objetivo (no del proceso actual)
TARGET_UID=$(id -u "$USER")
TARGET_GID=$(id -g "$USER")
TARGET_HOME=$(getent passwd "$USER" | cut -d: -f6)
# DISPLAY / XAUTHORITY desde el host
DISPLAY_VAR="${DISPLAY:-:0}"
XAUTH_VAR="${XAUTHORITY:-$TARGET_HOME/.Xauthority}"
# Directorio de runtime para aplicaciones Qt/KDE
# Usar /tmp en lugar de /run porque schroot crea un tmpfs nuevo en /run
# en lugar de bind-montar el /run del host, causando problemas de ownership.
# /tmp funciona correctamente preservando permisos y ownership del host.
RUNTIME_DIR="/tmp/runtime-$USER"

# Crear directorio en el HOST si no existe (será visible automáticamente en chroot)
if [ ! -d "$RUNTIME_DIR" ]; then
    mkdir -p "$RUNTIME_DIR"
    chmod 700 "$RUNTIME_DIR"
fi

# Permitir conexiones locales al servidor X
xhost +SI:localuser:"$USER" >/dev/null 2>&1 || xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot con todas las variables de entorno necesarias
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    DISPLAY="$DISPLAY_VAR" \
    XAUTHORITY="$XAUTH_VAR" \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    "$@"
