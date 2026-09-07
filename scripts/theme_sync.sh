#!/usr/bin/env bash
# ~/.config/qtile/scripts/theme_sync.sh

WALLPAPER="$1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$( dirname "$SCRIPT_DIR" )"
RAM_DIR="/dev/shm/qtile_overview"

if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
    echo "Uso: $0 /ruta/al/wallpaper.jpg"
    exit 1
fi

mkdir -p "$RAM_DIR"

# 1. Procesar paleta con Pywal
if command -v wal &> /dev/null; then
    wal -i "$WALLPAPER" -n -q -s -t --backend wal
fi

# 2. Re-generar palette.json en /dev/shm pasando la ruta del wallpaper
VENV_PY="$BASE_DIR/venv/bin/python"
if [ ! -f "$VENV_PY" ]; then
    VENV_PY=$(command -v python3)
fi

if [ -f "$SCRIPT_DIR/generate_palettes.py" ]; then
    "$VENV_PY" "$SCRIPT_DIR/generate_palettes.py" "$WALLPAPER"
fi

# 3. Recargar colores en tiempo real en Kitty
if command -v kitty &> /dev/null; then
    if [ -f "$HOME/.cache/wal/colors-kitty.conf" ]; then
        kitty @ set-colors -a "$HOME/.cache/wal/colors-kitty.conf" 2>/dev/null || pkill -USR1 kitty 2>/dev/null
    fi
fi

# 4. Transición fluida de Wallpaper en Wayland (noVNC / swaybg)
if command -v swaybg &> /dev/null; then
    OLD_PIDS=$(pgrep swaybg)
    swaybg -i "$WALLPAPER" -m fill &
    NEW_SWAY_PID=$!
    sleep 0.1
    for pid in $OLD_PIDS; do
        if [ "$pid" != "$NEW_SWAY_PID" ]; then
            kill "$pid" 2>/dev/null
        fi
    done
fi

# 5. Recargar configuración/colores de Qtile vía IPC
if command -v qtile &> /dev/null; then
    qtile cmd-obj -o cmd -f reload_config 2>/dev/null || qtile cmd-obj -o root -f reload_config 2>/dev/null
fi