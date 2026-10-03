#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_swww.sh
#
# Levanta el demonio de swww. El wallpaper real de cada grupo lo pone
# core/theme.py (`swww img ...`) en cuanto Qtile dispara sus hooks de arranque
# -- este script solo se asegura de que el demonio esté vivo antes de que eso
# pase. No pide ninguna imagen por su cuenta, para no pisar/duplicar la
# primera transición que va a pedir theme.py.

if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

if ! command -v swww &> /dev/null; then
    echo "[launch_swww] 'swww' no está instalado; no se gestionarán wallpapers." >&2
    exit 0
fi

# swww-daemon ya evita duplicarse solo si se lo pide dos veces (se fija si el
# socket ya está en uso, confirmado en la documentación del propio proyecto);
# no hace falta la lógica de lock/SIGKILL que sí necesitó la barra vieja de Eww.
if ! pgrep -x swww-daemon &> /dev/null; then
    swww-daemon &> /dev/null &
fi