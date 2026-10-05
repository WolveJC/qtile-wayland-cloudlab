#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_eww_widgets.sh
#
# Levanta el demonio de Eww para los widgets DECORATIVOS de escritorio (ya no
# la barra -- eso pasó a Waybar). Reusa el mismo criterio de idempotencia +
# SIGKILL que el lanzador de la vieja barra de Eww tuvo que aprender a las
# patadas con un demonio fantasma -- 'eww kill' solo no alcanzaba.
#
# PENDIENTE: este script todavía no abre ninguna ventana. eww/eww.yuck ya se
# vació del contenido viejo de la barra -- falta definir qué widgets
# decorativos van a vivir ahí y agregar el 'eww open <ventana>'
# correspondiente acá.
#
# Nota sobre logs: a diferencia de swww/Waybar/SwayNC, Eww SÍ tiene su propio
# log persistente siempre, sin importar cómo lo lancemos -- `eww logs` (lee
# ~/.cache/eww/eww_<hash>.log). El redirect de abajo es una copia extra, por
# si algo falla ANTES de que el logger interno de Eww llegue a inicializarse.

if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

if ! command -v eww &> /dev/null; then
    echo "[launch_eww_widgets] 'eww' no está instalado; se omiten los widgets de escritorio." >&2
    exit 0
fi

LOCK="/tmp/qtile-eww-widgets-launch-${WAYLAND_DISPLAY:-default}.lock"
exec 9>"$LOCK"
if ! flock -n 9; then
    echo "[launch_eww_widgets] ya hay otra instancia de este script en curso; se omite." >&2
    exit 0
fi

if eww active-windows &> /dev/null; then
    exit 0  # demonio ya vivo; falta decidir qué ventana(s) abrir -- ver PENDIENTE arriba
fi

LOG_DIR="$HOME/.local/share/qtile/logs"
mkdir -p "$LOG_DIR"
source "$(dirname "${BASH_SOURCE[0]}")/lib_log.sh"

pkill -9 -x eww 2>/dev/null
sleep 0.5
run_logged "$LOG_DIR/eww-widgets.log" eww daemon
sleep 0.5

# TODO: 'eww open <ventana-decorativa>' una vez que eww.yuck tenga contenido real.