#!/usr/bin/env bash

# Detectar la ruta base del repositorio y la ubicación del entorno virtual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PY="$SCRIPT_DIR/venv/bin/python"

# Fallback al python3 del sistema de forma compatible con entornos POSIX/Docker
if [ ! -f "$VENV_PY" ]; then
    VENV_PY=$(command -v python3)
fi

# =============================================================================
# 1. PREPARACIÓN EN RAM DE RAMDISK (/dev/shm)
# =============================================================================
RAM_DIR="/dev/shm/qtile_overview"
mkdir -p "$RAM_DIR"

# Generar paleta por defecto si no existe en RAM para evitar errores de lectura al inicio
if [ ! -f "$RAM_DIR/palette.json" ]; then
    cat <<EOF > "$RAM_DIR/palette.json"
{
  "border_active": "#89b4fa",
  "border_inactive": "rgba(255, 255, 255, 0.1)",
  "bg_card_active": "rgba(49, 50, 68, 0.8)",
  "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
  "text_color": "#cdd6f4",
  "bg_overlay": "rgba(15, 15, 23, 0.5)"
}
EOF
fi

# =============================================================================
# 2. GENERADOR DE PALETAS EN SEGUNDO PLANO (VENV)
# =============================================================================
# Procesa los fondos e inicializa los esquemas JSON en RAM
if [ -f "$SCRIPT_DIR/scripts/generate_palettes.py" ]; then
    "$VENV_PY" "$SCRIPT_DIR/scripts/generate_palettes.py" &
fi

# =============================================================================
# 3. DEMONIOS DEL SISTEMA Y NOTIFICACIONES
# =============================================================================
if command -v mako &> /dev/null; then
    mako &
fi

# Gestor de Papelera / Portapapeles
if command -v cliphist &> /dev/null && command -v wl-paste &> /dev/null; then
    wl-paste --watch cliphist store &
fi

# =============================================================================
# 4. FONDO DE PANTALLA INICIAL (WAYLAND)
# =============================================================================
INITIAL_WP="$SCRIPT_DIR/wallpapers/wp_1.jpg"
if [ -f "$INITIAL_WP" ] && command -v swaybg &> /dev/null; then
    swaybg -i "$INITIAL_WP" -m fill &
fi