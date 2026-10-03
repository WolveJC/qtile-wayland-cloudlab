#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_eww_widgets.sh
#
# Levanta el demonio de Eww para los widgets DECORATIVOS de escritorio (ya no
# la barra -- eso pasó a Waybar). Reusa el mismo criterio de idempotencia +
# SIGKILL que el lanzador de la vieja barra de Eww tuvo que aprender a las
# patadas con un demonio fantasma -- 'eww kill' solo no alcanzaba.
#
# PENDIENTE: este script todavía no abre ninguna ventana. eww/eww.yuck sigue
# teniendo el contenido viejo de la barra (bar + los tres popups) -- hay que
# vaciarlo y definir qué widgets decorativos van a vivir ahí antes de agregar
# el 'eww open <ventana>' correspondiente acá.

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

pkill -9 -x eww 2>/dev/null
sleep 0.5
eww daemon &> /dev/null &
sleep 0.5

# TODO: 'eww open <ventana-decorativa>' una vez que eww.yuck tenga contenido real.