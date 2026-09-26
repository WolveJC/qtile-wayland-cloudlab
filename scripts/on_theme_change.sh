#!/usr/bin/env bash
# ~/.config/qtile/scripts/on_theme_change.sh
# Ejecutado automáticamente por pywal (vía wallpapers.py) tras cambiar de paleta.

WAL_JSON="$HOME/.cache/wal/colors.json"
RAM_DIR="/dev/shm/qtile_overview"

mkdir -p "$RAM_DIR"

if [ -f "$WAL_JSON" ]; then
    # 1. Generar colors.scss para Eww
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
'''
with open('$RAM_DIR/colors.scss', 'w') as out:
    out.write(scss)
"

    # 2. Generar colors.css para SwayNC
    python3 -c "
import json
with open('$WAL_JSON') as f:
    data = json.load(f)
c = data['colors']
sp = data['special']
css = f'''@define-color accent {c['color4']};
@define-color accent2 {c['color6']};
@define-color bg {sp['background']};
@define-color bg_alt {c['color0']};
@define-color border_normal {c['color8']};
@define-color text {sp['foreground']};
@define-color text_dim {c['color7']};
'''
with open('$RAM_DIR/colors.css', 'w') as out:
    out.write(css)
"
fi

# 3. Recargar SwayNC
if command -v swaync-client &> /dev/null; then
    swaync-client -rs &> /dev/null &
fi

# 4. Recargar Eww
if command -v eww &> /dev/null; then
    eww reload &> /dev/null &
fi