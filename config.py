# ~/.config/qtile/config.py
import os
import subprocess
from libqtile import hook, layout
from libqtile.config import Screen, Match

# Importación modular
from core.keys import keys
from core.groups import groups
from core.layouts import layouts
from core.widgets import init_bar

# Configuración de pantallas y barra de estado
screens = [
    Screen(bottom=init_bar())
]

# Modos de integración flotante por defecto (diálogos, emergentes)
floating_layout = layout.Floating(
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
dnd_rules = []
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# Hook de Autoarranque (Ejecuta autostart.sh)
@hook.subscribe.startup_once
def autostart():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.expanduser(base_dir, 'autostart.sh')
    if os.path.exists(script):
        subprocess.Popen([script])

wmname = "LG3D"
