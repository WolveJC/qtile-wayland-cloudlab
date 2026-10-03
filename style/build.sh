#!/usr/bin/env bash
# ~/.config/qtile/style/build.sh
#
# Compila el SCSS compartido (_variables.scss, que escribe core/theme.py en cada
# cambio de paleta, + waybar.scss / swaync.scss propios de cada herramienta) a
# CSS plano, y recarga Waybar y SwayNC.
#
# A diferencia de Eww (que compila su propio SCSS al vuelo, internamente),
# Waybar y SwayNC solo saben leer CSS -- este paso de compilación explícito es
# necesario para los dos. Lo dispara core/theme.py después de escribir
# _variables.scss.

STYLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$STYLE_DIR")"

if ! command -v sass &> /dev/null; then
    echo "[style/build.sh] 'sass' no está instalado; no se puede compilar el SCSS." >&2
    exit 1
fi

mkdir -p "$CONFIG_DIR/waybar" "$CONFIG_DIR/swaync"

sass "$STYLE_DIR/waybar.scss" "$CONFIG_DIR/waybar/style.css" --no-source-map \
    || echo "[style/build.sh] fallo compilando waybar.scss" >&2
sass "$STYLE_DIR/swaync.scss" "$CONFIG_DIR/swaync/style.css" --no-source-map \
    || echo "[style/build.sh] fallo compilando swaync.scss" >&2

# Recargar cada herramienta, solo si está corriendo
if pgrep -x waybar &> /dev/null; then
    pkill -SIGUSR2 waybar 2>/dev/null
fi

if command -v swaync-client &> /dev/null; then
    swaync-client -rs &> /dev/null
fi