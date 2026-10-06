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

# Directorios de destino globales en ~/.config
WAYBAR_DEST="$HOME/.config/waybar"
SWAYNC_DEST="$HOME/.config/swaync"

# Este script lo llaman tres lugares distintos (autostart.sh, core/theme.py en
# cada cambio de paleta, on_theme_change.sh) -- y core/theme.py lo invoca con
# stdout/stderr descartados. Para que el log exista sin importar quién lo
# llame, se loguea desde ACÁ ADENTRO (append, así no se pierde el historial
# de corridas anteriores en la misma sesión), con timestamp por línea -- no
# solo un encabezado por corrida.
LOG_DIR="$HOME/.local/share/qtile/logs"
mkdir -p "$LOG_DIR"
exec >> "$LOG_DIR/style-build.log" 2>&1

_ts() {
    while IFS= read -r line; do
        printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
    done
}

echo "=== build.sh iniciado ===" | _ts

if ! command -v sass &> /dev/null; then
    echo "[style/build.sh] 'sass' no está instalado; no se puede compilar el SCSS." | _ts
    exit 1
fi

# Asegurar carpetas de destino en ~/.config
mkdir -p "$WAYBAR_DEST" "$SWAYNC_DEST"

# Compilar a las rutas finales
sass "$STYLE_DIR/waybar.scss" "$WAYBAR_DEST/style.css" --no-source-map 2>&1 | _ts
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "[style/build.sh] fallo compilando waybar.scss" | _ts
fi

sass "$STYLE_DIR/swaync.scss" "$SWAYNC_DEST/style.css" --no-source-map 2>&1 | _ts
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "[style/build.sh] fallo compilando swaync.scss" | _ts
fi

# Recargar cada herramienta, solo si está corriendo
if pgrep -x waybar &> /dev/null; then
    pkill -SIGUSR2 waybar 2>/dev/null
fi

if command -v swaync-client &> /dev/null; then
    swaync-client -rs &> /dev/null
fi
