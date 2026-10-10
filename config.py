# ~/.config/qtile/config.py
import os
import subprocess
from core.floating import mouse, floating_layout
from libqtile import hook
from libqtile.config import Screen
from libqtile.backend.wayland import InputConfig

# Importación modular
from core.keys import keys
from core.groups import groups
from core.layouts import layouts
from core.wallpapers import ensure_cache_symlink
from core import theme  # noqa: F401 (registra hooks de wallpaper por grupo y tema)

# 1. Garantizar symlink ~/.cache/wal -> RAM
ensure_cache_symlink()

# Configuración de pantallas (Waybar gestiona la barra; ver autostart.sh)
screens = [
    Screen()
]

# Opciones Generales
dnd_rules: list = []
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# Perfil: "vnc" (lo exporta start-wayland-vnc.sh) o "desktop" (por defecto)
PROFILE = os.environ.get("QTILE_PROFILE", "desktop")

# Entradas Wayland (Teclado Latam + Touchpad)
# En VNC no hay hardware: el teclado lo inyecta wayvnc, asi que no se fuerza layout.
wl_input_rules = {} if PROFILE == "vnc" else {
    "type:keyboard": InputConfig(kb_layout="latam"),
    "type:touchpad": InputConfig(tap=True, natural_scroll=True),
}

# Hook de Autoarranque (Ejecuta autostart.sh)
@hook.subscribe.startup_once
def autostart():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(base_dir, 'autostart.sh')
    if os.path.exists(script):
        subprocess.Popen(["bash", script])

wmname = "LG3D"