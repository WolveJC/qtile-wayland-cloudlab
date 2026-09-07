# ~/.config/qtile/core/keys.py
import os
import sys
from libqtile.config import Key
from libqtile.lazy import lazy

# --- Variables Principales ---
mod = "mod4"  # Tecla Super (Windows)

terminal = "kitty"

# Obtener la ruta base del repositorio dinámicamente
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ghost_theme = os.path.join(base_dir, "scripts", "ghost.rasi")
launcher = f"rofi -show drun -theme {ghost_theme}"
venv_python_candidate = os.path.join(base_dir, "venv", "bin", "python")
if os.path.exists(venv_python_candidate):
    VENV_PYTHON = venv_python_candidate
else:
    VENV_PYTHON = sys.executable
overview_script = os.path.join(base_dir, "overview", "overview.py")

overview_cmd = f"{VENV_PYTHON} {overview_script}"

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
