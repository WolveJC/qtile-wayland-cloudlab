# ~/.config/qtile/core/keys.py
import os
from libqtile.config import Key
from libqtile.lazy import lazy

# --- Variables Principales ---
mod = "mod4"  # Tecla Super (Windows)

terminal = "kitty"
launcher = "rofi -show drun -theme ./scripts/ghost.rasi"

# Expansión correcta de la ruta para Python / Qtile
overview_script = os.path.expanduser("~/.config/qtile/overview/overview.py")
overview_cmd = f"python3 {overview_script}"

keys = [
    # -------------------------------------------------------------------------
    # Lanzadores del Entorno & GUI Custom
    # -------------------------------------------------------------------------
    Key([mod], "Return", lazy.spawn(terminal), desc="Abrir Terminal Kitty"),
    Key([mod], "space", lazy.spawn(launcher), desc="Lanzador Rofi Wayland"),
    
    # Modo Exposición / Overview (PySide6 Camaleónico)
    Key([mod], "Tab", lazy.spawn(overview_cmd), desc="Activar Modo Exposición"),

    # -------------------------------------------------------------------------
    # Gestión de Notificaciones (Mako)
    # -------------------------------------------------------------------------
    Key(["control"], "space", lazy.spawn("makoctl dismiss"), desc="Descartar notificación"),
    Key(["control", "shift"], "space", lazy.spawn("makoctl dismiss -a"), desc="Descartar todas las notificaciones"),

    # -------------------------------------------------------------------------
    # Navegación entre Ventanas (Foco)
    # -------------------------------------------------------------------------
    Key([mod], "h", lazy.layout.left(), desc="Mover foco a la izquierda"),
    Key([mod], "l", lazy.layout.right(), desc="Mover foco a la derecha"),
    Key([mod], "j", lazy.layout.down(), desc="Mover foco abajo"),
    Key([mod], "k", lazy.layout.up(), desc="Mover foco arriba"),

    # -------------------------------------------------------------------------
    # Desplazamiento de Ventanas (Mosaico / Layout)
    # -------------------------------------------------------------------------
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Mover ventana a la izquierda"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Mover ventana a la derecha"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Mover ventana abajo"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Mover ventana arriba"),

    # -------------------------------------------------------------------------
    # Gestión de Ventanas y Sistema Qtile
    # -------------------------------------------------------------------------
    Key([mod], "q", lazy.window.kill(), desc="Cerrar ventana activa"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Recargar configuración de Qtile"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Cerrar sesión de Qtile"),
]
