#!/usr/bin/env bash
# ~/.config/qtile/scripts/theme_sync.sh

WALLPAPER="$1"

if [ -z "$WALLPAPER" ]; then
    echo "Uso: $0 /ruta/al/wallpaper.jpg"
    exit 1
fi

# 1. Procesar paleta usando Pywal en silencio
wal -i "$WALLPAPER" -n -q -s -t --backend wal

# 2. Guardar JSON procesado en RAM (/dev/shm)
cat ~/.cache/wal/colors.json > /dev/shm/current_palette.json

# 3. Cambiar el fondo en caliente con swaybg en Wayland
killall swaybg 2>/dev/null
swaybg -i "$WALLPAPER" -m fill &

# 4. Recargar configuración de Qtile vía IPC
qtile cmd-obj -o root -f reload_config