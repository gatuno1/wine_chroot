#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
#
# make_wine_chroot_desktop.sh
#
# Genera un .desktop que ejecuta un .exe de Windows usando Wine dentro de un schroot.
# El script se ejecuta en el host y crea accesos directos que lanzan aplicaciones
# dentro del entorno chroot donde Wine está instalado.
#
# Casos de uso:
# - Ejecutar aplicaciones Windows x86/amd64 en hosts ARM64 usando un chroot Debian amd64
# - Aislar aplicaciones Wine en entornos chroot separados
#
# Uso:
#   ./make_wine_chroot_desktop.sh --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/WlkataStudio/WlkataStudio.exe" \
#       --name "Wlkata Studio (Wine chroot)" --icon
#
# Opciones:
#   --exe RUTA        -> Ruta al .exe vista desde el host dentro del árbol del schroot (requerido)
#   --name NOMBRE     -> Nombre que aparecerá en el menú (requerido)
#   --desktop ARCHIVO -> Nombre del archivo .desktop (por defecto derivado del nombre)
#   --icon            -> Intentar extraer el icono del .exe usando wrestool+icotool
#   --schroot NOMBRE  -> Nombre del schroot a usar (default: debian-amd64)
#
# Requisitos:
# - Host: schroot, icoutils (wrestool, icotool)
# - Chroot: Wine instalado y configurado
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# según los términos de la GNU General Public License publicada por la Free
# Software Foundation, ya sea la versión 3 de la licencia o (a tu elección)
# cualquier versión posterior.

set -e
set -u

SCHROOT_NAME="debian-amd64"
EXE_PATH=""
APP_NAME=""
DESKTOP_NAME=""
DO_ICON=false

show_help() {
    cat << EOF
Uso: $(basename "$0") --exe EXE --name NAME [--desktop DESKTOP] [--icon] [--schroot SCHROOT]

Genera un .desktop que ejecuta un .exe con wine dentro de un schroot.

Argumentos requeridos:
  --exe EXE          Ruta al .exe vista desde el host dentro del árbol del schroot
  --name NAME        Nombre que aparecerá en el menú

Argumentos opcionales:
  --desktop DESKTOP  Nombre del archivo .desktop (por defecto derivado del nombre)
  --icon             Intentar extraer el icono del .exe usando wrestool+icotool
  --schroot SCHROOT  Nombre del schroot a usar (default: debian-amd64)
  -h, --help         Mostrar esta ayuda

EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --exe)
            EXE_PATH="$2"
            shift 2
            ;;
        --name)
            APP_NAME="$2"
            shift 2
            ;;
        --desktop)
            DESKTOP_NAME="$2"
            shift 2
            ;;
        --icon)
            DO_ICON=true
            shift 1
            ;;
        --schroot)
            SCHROOT_NAME="$2"
            shift 2
            ;;
        *)
            echo "Error: Opción desconocida: $1"
            echo "Usa --help para ver las opciones disponibles."
            exit 1
            ;;
    esac
done

if [[ -z "$EXE_PATH" ]]; then
    echo "Error: Falta el argumento requerido --exe"
    echo "Uso: $(basename "$0") --exe EXE --name NAME"
    echo "Usa --help para más información."
    exit 1
fi

if [[ -z "$APP_NAME" ]]; then
    echo "Error: Falta el argumento requerido --name"
    echo "Uso: $(basename "$0") --exe EXE --name NAME"
    echo "Usa --help para más información."
    exit 1
fi

# Verificar que el archivo .exe existe
if [[ ! -f "$EXE_PATH" ]]; then
    echo "[!] El .exe no existe en esa ruta: $EXE_PATH"
    echo "    Recuerda que debe ser la ruta vista desde el host, p.ej."
    echo "    /srv/debian-amd64/root/.wine/drive_c/Program Files/..."
    exit 1
fi

# Nombre del archivo .desktop
if [[ -z "$DESKTOP_NAME" ]]; then
    # Convertir nombre a formato válido (similar a Python: re.sub(r"[^a-z0-9]+", "-", ...))
    DESKTOP_NAME="$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/^-//;s/-$//')".desktop
fi

DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

# Convertir la ruta Linux del exe a ruta Windows (C:\...)
# Si la ruta contiene 'drive_c/', la convertimos a C:\... con backslashes.
# Si ya está en formato C:\..., la devolvemos igual.
WIN_EXE_PATH=""
if [[ "$EXE_PATH" =~ ^[A-Za-z]:\\ ]]; then
    # Ya está en formato Windows
    WIN_EXE_PATH="$EXE_PATH"
elif [[ "$EXE_PATH" == *"drive_c/"* ]]; then
    # Extraer la parte después de drive_c/
    AFTER_DRIVE=$(echo "$EXE_PATH" | sed 's#.*drive_c/##')
    # Cambiar / por \
    AFTER_DRIVE_WIN=$(echo "$AFTER_DRIVE" | sed 's#/#\\#g')
    WIN_EXE_PATH="C:\\$AFTER_DRIVE_WIN"
else
    # Último recurso: devolver tal cual (wine soporta rutas unix)
    WIN_EXE_PATH="$EXE_PATH"
fi

# Icono opcional
ICON_PATH=""
if $DO_ICON; then
    DESKTOP_BASENAME="$(basename "$DESKTOP_NAME" .desktop)"
    ICON_PATH="$ICON_DIR/${DESKTOP_BASENAME}.png"
    TMP_ICO="/tmp/${DESKTOP_BASENAME}.ico"
    TMP_PNG_DIR="/tmp/icoextract_bash"
    
    echo "[*] Extrayendo ícono desde $EXE_PATH ..."
    
    # 1. wrestool - extraer el .ico del .exe
    if sudo wrestool -x -t14 "$EXE_PATH" -o "$TMP_ICO" 2>/dev/null; then
        if [[ -f "$TMP_ICO" ]]; then
            # 2. icotool - convertir .ico a .png
            mkdir -p "$TMP_PNG_DIR"
            if icotool -x "$TMP_ICO" -o "$TMP_PNG_DIR" 2>/dev/null; then
                # Elegir el PNG más grande (el último en orden alfabético suele ser el más grande)
                CHOSEN_PNG=$(ls -1 "$TMP_PNG_DIR"/*.png 2>/dev/null | sort | tail -n 1 || true)
                if [[ -n "$CHOSEN_PNG" ]]; then
                    cp "$CHOSEN_PNG" "$ICON_PATH"
                    echo "[*] Ícono copiado a $ICON_PATH"
                else
                    echo "[!] No se encontraron PNGs extraídos"
                    ICON_PATH=""
                fi
            else
                echo "[!] No se pudo convertir .ico a .png"
                ICON_PATH=""
            fi
        else
            echo "[!] wrestool no produjo el .ico"
            ICON_PATH=""
        fi
    else
        echo "[!] No se pudo extraer .ico con wrestool"
        ICON_PATH=""
    fi
fi

DESKTOP_FILE="$DESKTOP_DIR/$DESKTOP_NAME"

# Contenido del .desktop
{
    echo "[Desktop Entry]"
    echo "Name=$APP_NAME"
    echo "Comment=Ejecutar $APP_NAME dentro del schroot $SCHROOT_NAME"
    echo "Exec=sudo schroot -c $SCHROOT_NAME -- wine \"$WIN_EXE_PATH\""
    echo "Type=Application"
    echo "Categories=Wine;WindowsApps;"
    echo "StartupNotify=true"
    echo "Terminal=false"
    echo "StartupWMClass=$(basename "$WIN_EXE_PATH")"
    if [[ -n "$ICON_PATH" ]]; then
        echo "Icon=$ICON_PATH"
    fi
} > "$DESKTOP_FILE"

echo "[*] .desktop creado en: $DESKTOP_FILE"

# Intentar refrescar la base de datos de menús
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "✅ Listo."
echo "Busca "$APP_NAME" en el menú."
echo "Si pide password al lanzar, agrega en sudoers algo como:"
echo "    TUUSUARIO ALL=(ALL) NOPASSWD: /usr/bin/schroot"

echo "[*] Acceso creado en: $DESKTOP_FILE"
echo "[*] Recargando base de datos de escritorio..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "Listo. Deberías ver “$APP_NAME” en el menú (categoría Wine)."
echo "Si te pide contraseña al lanzar, agrega en sudoers:"
echo "    TUUSUARIO ALL=(ALL) NOPASSWD: /usr/bin/schroot"
