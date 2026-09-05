# ~/.config/qtile/scripts/update_palette.py
import json
import os

RAM_PALETTE = "/dev/shm/qtile_overview/palette.json"
os.makedirs(os.path.dirname(RAM_PALETTE), exist_ok=True)

# Ejemplo: Generar paleta basada en colores extraídos
def generate_ram_palette(primary_hex, bg_hex, text_hex):
    palette = {
        "border_active": primary_hex,             # Color acento dinámico
        "border_inactive": "rgba(255, 255, 255, 0.1)",
        "bg_card_active": "rgba(30, 30, 46, 0.85)",
        "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
        "text_color": text_hex,                  # Texto adaptado
        "bg_overlay": f"{bg_hex}aa"               # Oscurecimiento con transparencia
    }
    
    with open(RAM_PALETTE, "w", encoding="utf-8") as f:
        json.dump(palette, f, indent=2)

# Ejemplo de uso estático o tras ejecutar pywal
generate_ram_palette("#f5e0dc", "#11111b", "#cdd6f4")