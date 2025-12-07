#!/usr/bin/env bash
# Script simplificado para ejecutar comandos dentro del chroot
# Versión 2 - Aprovecha preserve-environment=true en schroot

# Nombre default del chroot
CHROOT_NAME="${CHROOT_NAME:-alt-debian-amd64}"

# Usuario objetivo (el que ejecutará Wine)
USER="${USER:-$(whoami)}"

# Directorio de runtime para aplicaciones Qt/KDE
# Usar /tmp en lugar de /run porque schroot crea un tmpfs nuevo en /run
# en lugar de bind-montar el /run del host, causando problemas de ownership.
RUNTIME_DIR="/tmp/runtime-$USER"

# Crear directorio en el HOST si no existe
# (será visible automáticamente en el chroot vía bind-mount de /tmp)
if [ ! -d "$RUNTIME_DIR" ]; then
    mkdir -p "$RUNTIME_DIR"
    chmod 700 "$RUNTIME_DIR"
fi

# Permitir conexiones locales al servidor X
xhost +SI:localuser:"$USER" >/dev/null 2>&1 || xhost +local: >/dev/null 2>&1 || true

# Ejecuta el comando en el chroot
# Con preserve-environment=true, DISPLAY y XAUTHORITY se heredan automáticamente del host
# Solo necesitamos configurar XDG_RUNTIME_DIR (que apunta a /run/user/$UID en el host)
# y WINEPREFIX para indicar dónde está el prefijo de Wine
schroot -c "$CHROOT_NAME" --user=$USER -- env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    WINEPREFIX="/home/$USER/.wine" \
    "$@"
