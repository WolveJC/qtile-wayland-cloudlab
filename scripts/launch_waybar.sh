#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_waybar.sh
#
# Levanta Waybar. Idempotente: si ya está corriendo, no la reinicia (evita el
# mismo tipo de parpadeo/duplicado que tuvimos que resolver con la barra vieja
# de Eww, cuando este script todavía la lanzaba a ella).

if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

if ! command -v waybar &> /dev/null; then
    echo "[launch_waybar] 'waybar' no está instalado; se omite la barra." >&2
    exit 0
fi

if pgrep -x waybar &> /dev/null; then
    exit 0
fi

waybar &> /dev/null &