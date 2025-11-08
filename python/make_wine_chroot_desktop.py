#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Wine Chroot Contributors
"""
make_wine_chroot_desktop.py

Genera un .desktop que ejecuta un .exe de Windows usando Wine dentro de un schroot.
El script se ejecuta en el host y crea accesos directos que lanzan aplicaciones
dentro del entorno chroot donde Wine está instalado.

Casos de uso:
- Ejecutar aplicaciones Windows x86/amd64 en hosts ARM64 usando un chroot Debian amd64
- Aislar aplicaciones Wine en entornos chroot separados

Uso:
    python3 make_wine_chroot_desktop.py \
        --exe "/srv/debian-amd64/root/.wine/drive_c/Program Files/WlkataStudio/WlkataStudio.exe" \
        --name "Wlkata Studio (Wine chroot)" \
        --icon

Requisitos:
- Host: schroot, icoutils (wrestool, icotool)
- Chroot: Wine instalado y configurado

Este programa es software libre: puedes redistribuirlo y/o modificarlo
según los términos de la GNU General Public License publicada por la Free
Software Foundation, ya sea la versión 3 de la licencia o (a tu elección)
cualquier versión posterior.
"""

from __future__ import annotations
import argparse
import re
import shutil
import subprocess
from pathlib import Path


def linux_path_to_win(path: str) -> str:
    """
    Si la ruta contiene 'drive_c/', la convertimos a C:\\... con backslashes.
    Si ya está en formato C:\\..., la devolvemos igual.
    """
    if re.match(r"^[A-Za-z]:\\", path):
        return path  # ya viene en formato Windows

    if "drive_c/" in path:
        after = path.split("drive_c/", 1)[1]
        win = after.replace("/", "\\")
        return f"C:\\{win}"
    # último recurso: devolver tal cual (wine soporta rutas unix)
    return path


def extract_icon(exe_path: Path, icon_dir: Path, desktop_basename: str) -> Path | None:
    """
    Intenta extraer el icono del .exe usando wrestool + icotool.
    Devuelve la ruta al PNG elegido o None si no se pudo.
    """
    tmp_ico = Path("/tmp") / f"{desktop_basename}.ico"

    # 1. wrestool
    try:
        subprocess.run(
            ["sudo", "wrestool", "-x", "-t14", str(exe_path), "-o", str(tmp_ico)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print("[!] No se pudo extraer .ico con wrestool:", e)
        return None

    if not tmp_ico.exists():
        print("[!] wrestool no produjo el .ico")
        return None

    # 2. icotool a /tmp/icoextract_py
    tmp_png_dir = Path("/tmp/icoextract_py")
    tmp_png_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["icotool", "-x", str(tmp_ico), "-o", str(tmp_png_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print("[!] No se pudo convertir .ico a .png:", e)
        return None

    pngs = sorted(tmp_png_dir.glob("*.png"))
    if not pngs:
        print("[!] No se encontraron PNGs extraídos")
        return None

    # Elegimos el "más grande" por nombre (suele ser el último)
    chosen_png = pngs[-1]
    icon_dir.mkdir(parents=True, exist_ok=True)
    final_icon = icon_dir / f"{desktop_basename}.png"
    shutil.copy(chosen_png, final_icon)
    print(f"[*] Ícono copiado a {final_icon}")
    return final_icon


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un .desktop que ejecuta un .exe con wine dentro de un schroot."
    )
    parser.add_argument(
        "--exe",
        required=True,
        help="Ruta al .exe vista desde el host dentro del árbol del schroot",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Nombre que aparecerá en el menú",
    )
    parser.add_argument(
        "--desktop",
        help="Nombre del archivo .desktop (por defecto derivado del nombre)",
    )
    parser.add_argument(
        "--icon",
        action="store_true",
        help="Intentar extraer el icono del .exe usando wrestool+icotool",
    )
    parser.add_argument(
        "--schroot",
        default="debian-amd64",
        help="Nombre del schroot a usar (default: debian-amd64)",
    )
    args = parser.parse_args()

    exe_path = Path(args.exe).expanduser()
    if not exe_path.exists():
        print(f"[!] El .exe no existe en esa ruta: {exe_path}")
        print("    Recuerda que debe ser la ruta vista desde el host, p.ej.")
        print("    /srv/debian-amd64/root/.wine/drive_c/Program Files/...")
        raise SystemExit(1)

    app_name = args.name
    # nombre de archivo .desktop
    if args.desktop:
        desktop_filename = args.desktop
    else:
        desktop_filename = re.sub(r"[^a-z0-9]+", "-", app_name.lower()).strip("-") + ".desktop"

    desktop_dir = Path.home() / ".local" / "share" / "applications"
    icon_dir = Path.home() / ".local" / "share" / "icons"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    # convertir la ruta linux del exe a ruta Windows (C:\...)
    win_exe_path = linux_path_to_win(str(exe_path))

    # icono opcional
    icon_path: Path | None = None
    if args.icon:
        icon_path = extract_icon(exe_path, icon_dir, desktop_filename.replace(".desktop", ""))

    desktop_file = desktop_dir / desktop_filename

    # contenido del .desktop
    lines = [
        "[Desktop Entry]",
        f"Name={app_name}",
        f"Comment=Ejecutar {app_name} dentro del schroot {args.schroot}",
        # comando exacto que usas tú:
        f'Exec=sudo schroot -c {args.schroot} -- wine "{win_exe_path}"',
        "Type=Application",
        "Categories=Wine;WindowsApps;",
        "StartupNotify=true",
        "Terminal=false",
        # esto ayuda a los DE a agrupar la ventana
        f"StartupWMClass={Path(win_exe_path).name}",
    ]
    if icon_path:
        lines.append(f"Icon={icon_path}")

    desktop_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[*] .desktop creado en: {desktop_file}")

    # intentar refrescar la base de datos de menús
    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        # no pasa nada si no está
        pass

    print("\n✅ Listo.")
    print(f"Busca “{app_name}” en el menú.")
    print("Si pide password al lanzar, agrega en sudoers algo como:")
    print("    TUUSUARIO ALL=(ALL) NOPASSWD: /usr/bin/schroot")


if __name__ == "__main__":
    main()
