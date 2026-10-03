#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_swaync.sh
#
# Levanta SwayNC. Idempotente: si ya está corriendo, no lo reinicia. Antes esto
# vivía suelto directo en autostart.sh (killall + swaync &, sin chequeo); se
# movió a su propio script para que tenga el mismo criterio que los demás
# lanzadores (swww, waybar, eww).

if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

if ! command -v swaync &> /dev/null; then
    echo "[launch_swaync] 'swaync' no está instalado; se omiten notificaciones/centro de mando." >&2
    exit 0
fi

if pgrep -x swaync &> /dev/null; then
    exit 0
fi

swaync &> /dev/null &