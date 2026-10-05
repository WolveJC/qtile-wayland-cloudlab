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

# swww no tiene un log propio garantizado -- a diferencia de Eww o Qtile, solo
# imprime a su salida estándar. Si no lo capturamos acá, se pierde para
# siempre (antes iba a /dev/null). Mismo directorio para los lanzadores
# nuevos, así hay un solo lugar donde mirar, con timestamp por línea
# (ver lib_log.sh) para saber exactamente cuándo pasó cada cosa.
LOG_DIR="$HOME/.local/share/qtile/logs"
mkdir -p "$LOG_DIR"
source "$(dirname "${BASH_SOURCE[0]}")/lib_log.sh"

# swww-daemon ya evita duplicarse solo si se lo pide dos veces (se fija si el
# socket ya está en uso, confirmado en la documentación del propio proyecto);
# no hace falta la lógica de lock/SIGKILL que sí necesitó la barra vieja de Eww.
if ! pgrep -x swww-daemon &> /dev/null; then
    run_logged "$LOG_DIR/swww.log" swww-daemon
fi