#!/usr/bin/env bash
# Script simplificado para ejecutar comandos dentro del chroot
# Versión 1.1

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
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    "$@"
