#!/usr/bin/env bash

# =============================================================================
# 1. PREPARACIÓN EN RAM DE RAMDISK (/dev/shm)
# =============================================================================
RAM_DIR="/dev/shm/qtile_overview"
mkdir -p "$RAM_DIR"

# Generar paleta por defecto si no existe en RAM para evitar errores de lectura
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
# 2. DEMONIOS DEL SISTEMA Y NOTIFICACIONES
# =============================================================================
# Notificaciones
mako &

# Gestor de Papelera / Portapapeles (Opcional si usas wl-clipboard/cliphist)
# cliphist daemon &

# =============================================================================
# 3. WALLPAPER Y GENERADOR DE COLORES CAMALEÓNICOS
# =============================================================================
# Si usas hyprpaper, swaybg o feh para tu fondo:
# swaybg -i ~/.config/qtile/wallpapers/wp_1.jpg -m fill &

# Si usas Pywal o un script custom para actualizar la paleta en RAM:
# python3 ~/.config/qtile/scripts/generate_palette.py &