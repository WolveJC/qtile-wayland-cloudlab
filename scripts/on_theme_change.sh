#!/usr/bin/env bash
# ~/.config/qtile/scripts/on_theme_change.sh
# Ejecutado automáticamente por pywal (vía wallpapers.py) tras cambiar de paleta.

WAL_JSON="$HOME/.cache/wal/colors.json"
RAM_DIR="/dev/shm/qtile_overview"
STYLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/style"

mkdir -p "$RAM_DIR"

if [ -f "$WAL_JSON" ]; then
    # Generar _variables.scss compartido (lo importan waybar.scss y swaync.scss;
    # ya no hay colors.scss para Eww ni colors.css GTK aparte para SwayNC -- los
    # dos pasan por el mismo SCSS, compilado por style/build.sh).
    python3 -c "
import json
with open('$WAL_JSON') as f:
    data = json.load(f)
c = data['colors']
sp = data['special']
scss = f'''\$accent: {c['color4']};
\$accent2: {c['color6']};
\$bg: {sp['background']};
\$bg_alt: {c['color0']};
\$border_normal: {c['color8']};
\$text: {sp['foreground']};
\$text_dim: {c['color7']};
\$transition_ms: 600ms;
'''
with open('$RAM_DIR/_variables.scss', 'w') as out:
    out.write(scss)
"
fi

# Compilar el SCSS y recargar Waybar + SwayNC (ya no 'eww reload': Eww dejó de
# ser la barra, y los widgets decorativos que le queden no pasan por este
# pipeline de la misma forma -- ver eww/eww.yuck).
if [ -f "$STYLE_DIR/build.sh" ]; then
    bash "$STYLE_DIR/build.sh" &> /dev/null &
fi