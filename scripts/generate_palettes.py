# ~/.config/qtile/scripts/generate_palettes.py
import os
import json
import subprocess

# Detección dinámica de rutas dentro del proyecto / venv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAM_DIR = "/dev/shm/qtile_overview"
RAM_PALETTE = os.path.join(RAM_DIR, "palette.json")
WP_DIR = os.path.join(BASE_DIR, "wallpapers")

os.makedirs(RAM_DIR, exist_ok=True)

def hex_to_rgba(hex_str: str, alpha: float = 1.0) -> str:
    """Convierte código Hexadecimal a formato rgba() de CSS/Qt."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"
    return hex_str

def get_fallback_palette() -> dict:
    """Paleta por defecto de alto contraste (Catppuccin Macchiato)."""
    return {
        "border_active": "#89b4fa",
        "border_inactive": "rgba(255, 255, 255, 0.15)",
        "bg_card_active": "rgba(49, 50, 68, 0.85)",
        "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
        "text_color": "#cdd6f4",
        "bg_overlay": "rgba(15, 15, 23, 0.6)"
    }

def extract_palette_from_wallpaper(image_path: str) -> dict:
    """Extrae colores del wallpaper seleccionado mediante Pywal si existe."""
    if not os.path.exists(image_path):
        return get_fallback_palette()

    # Si pywal está disponible en el entorno
    try:
        subprocess.run(["wal", "-i", image_path, "-n", "-q", "-s", "-t"], check=True)
        wal_colors_file = os.path.expanduser("~/.cache/wal/colors.json")
        
        if os.path.exists(wal_colors_file):
            with open(wal_colors_file, "r", encoding="utf-8") as f:
                c = json.load(f).get("colors", {})

            bg_hex = c.get("color0", "#11111b")
            primary_hex = c.get("color4", "#89b4fa")
            text_hex = c.get("color7", "#cdd6f4")

            return {
                "border_active": primary_hex,
                "border_inactive": "rgba(255, 255, 255, 0.15)",
                "bg_card_active": hex_to_rgba(bg_hex, 0.85),
                "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
                "text_color": text_hex,
                "bg_overlay": hex_to_rgba(bg_hex, 0.6)
            }
    except Exception:
        pass

    return get_fallback_palette()

def generate_ram_palette(wallpaper_index: int = 1):
    """Genera y guarda el archivo palette.json en /dev/shm."""
    # Determinar si pasaron una ruta completa o un índice
    if os.path.exists(target_input):
        wp_path = target_input
    else:
        wp_path = os.path.join(WP_DIR, f"wp_{target_input}.jpg")

    palette = extract_palette_from_wallpaper(wp_path)

    with open(RAM_PALETTE, "w", encoding="utf-8") as f:
        json.dump(palette, f, indent=2)

if __name__ == "__main__":
    # Lee la ruta del wallpaper pasada desde theme_sync.sh si existe
    input_arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    generate_ram_palette(input_arg)