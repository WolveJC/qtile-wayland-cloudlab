# ~/.config/qtile/config.py
import os
import subprocess
from core.floating import mouse
from libqtile import hook, layout
from libqtile.config import Screen, Match
from libqtile.backend.wayland import InputConfig

# Importación modular
from core.keys import keys
from core.groups import groups
from core.layouts import layouts
from core.wallpapers import DEFAULT_PALETTE as C, ensure_cache_symlink
from core import theme  # noqa: F401 (registra hooks de wallpaper por grupo y tema)
from core.eww_ipc import init_eww_ipc

# 1. Garantizar symlink ~/.cache/wal -> RAM
ensure_cache_symlink()

# 2. Inicializar hooks IPC para Eww (notificaciones en tiempo real)
init_eww_ipc()

# Configuración de pantallas (Eww gestiona la barra)
screens = [
    Screen()
]

# Reglas de ventanas flotantes
floating_layout = layout.Floating(
    border_focus=C["accent"],
    border_normal=C["border_normal"],
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),    # gitk
        Match(wm_class="maketag"),       # gitk
        Match(wm_class="ssh-askpass"),   # ssh-askpass
        Match(title="branchdialog"),     # gitk
        Match(title="pinentry"),         # GPG key password entry
    ]
)

# Opciones Generales
dnd_rules: list = []
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# Entradas Wayland (Teclado Latam + Touchpad)
wl_input_rules = {
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
