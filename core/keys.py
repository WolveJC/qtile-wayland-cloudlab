# ~/.config/qtile/core/keys.py
import os
import sys
from typing import List
from libqtile.config import Key
from libqtile.lazy import lazy

# --- Variables Principales ---
mod: str = "mod1" if os.environ.get("QTILE_NESTED") else "mod4" # Tecla window o Alt
terminal: str = "kitty"

# Obtener la ruta base del repositorio dinámicamente
base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ghost_theme: str = os.path.join(base_dir, "scripts", "ghost.rasi")
launcher: str = f"rofi -show drun -theme {ghost_theme}"
clipboard_menu: str = f"rofi -dmenu -theme {ghost_theme} -p 'Clipboard'"

venv_python_candidate: str = os.path.join(base_dir, "venv", "bin", "python")
VENV_PYTHON: str = venv_python_candidate if os.path.exists(venv_python_candidate) else sys.executable

overview_script: str = os.path.join(base_dir, "overview", "overview.py")
overview_cmd: str = f"{VENV_PYTHON} {overview_script}"

clutch_script: str = os.path.join(base_dir, "scripts", "clutch.py")
clutch_to_kde: str = f"python3 {clutch_script} kde"

# Pipeline explícito para Cliphist (Módulo 3)
clipboard_pick: str = f"cliphist list | {clipboard_menu} | cliphist decode | wl-copy"

keys: List[Key] = [
    # -------------------------------------------------------------------------
    # Lanzadores del Entorno & GUI Custom
    # -------------------------------------------------------------------------
    Key([mod], "Return", lazy.spawn(terminal), desc="Abrir Terminal Kitty"),
    Key([mod], "space", lazy.spawn(launcher), desc="Lanzador Rofi Wayland"),
    Key([mod], "Tab", lazy.spawn(overview_cmd), desc="Activar Modo Exposición"),
    Key([mod, "shift"], "e", lazy.spawn(clutch_to_kde), desc="Cambiar a sesión KDE"),

    # -------------------------------------------------------------------------
    # Módulo 3: Portapapeles (Cliphist)
    # -------------------------------------------------------------------------
    Key([mod], "v", lazy.spawn(clipboard_pick, shell=True), desc="Historial de portapapeles"),

    # -------------------------------------------------------------------------
    # Gestión de Notificaciones
    # -------------------------------------------------------------------------
    Key(["control"], "space", lazy.spawn("swaync-client --close-latest"), desc="Cerrar última notificación"),
    Key(["control", "shift"], "space", lazy.spawn("swaync-client --close-all"), desc="Cerrar todas las notificaciones"),
    Key([mod, "shift"], "n", lazy.spawn("swaync-client -t -sw"), desc="Abrir/Cerrar Centro de Notificaciones"),
    # -------------------------------------------------------------------------
    # Navegación entre Ventanas (Foco)
    # -------------------------------------------------------------------------
    Key([mod], "h", lazy.layout.left(), desc="Mover foco a la izquierda"),
    Key([mod], "l", lazy.layout.right(), desc="Mover foco a la derecha"),
    Key([mod], "j", lazy.layout.down(), desc="Mover foco abajo"),
    Key([mod], "k", lazy.layout.up(), desc="Mover foco arriba"),

    # -------------------------------------------------------------------------
    # Desplazamiento de Ventanas (Mosaico)
    # -------------------------------------------------------------------------
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Mover ventana a la izquierda"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Mover ventana a la derecha"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Mover ventana abajo"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Mover ventana arriba"),

    # -------------------------------------------------------------------------
    # Módulo 1: Preselección en Layout BSP + Lanzador
    # -------------------------------------------------------------------------
    Key([mod, "control"], "h", lazy.layout.preselect("left"), lazy.spawn(launcher), desc="Preseleccionar división izquierda y abrir Rofi"),
    Key([mod, "control"], "l", lazy.layout.preselect("right"), lazy.spawn(launcher), desc="Preseleccionar división derecha y abrir Rofi"),
    Key([mod, "control"], "j", lazy.layout.preselect("down"), lazy.spawn(launcher), desc="Preseleccionar división abajo y abrir Rofi"),
    Key([mod, "control"], "k", lazy.layout.preselect("up"), lazy.spawn(launcher), desc="Preseleccionar división arriba y abrir Rofi"),

    # Alternancia de Layouts
    Key([mod, "control"], "space", lazy.next_layout(), desc="Cambiar layout (Bsp/MonadTall/...)"),

    # -------------------------------------------------------------------------
    # Gestión de Ventanas y Sistema Qtile
    # -------------------------------------------------------------------------
    Key([mod], "q", lazy.window.kill(), desc="Cerrar ventana activa"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Recargar configuración de Qtile"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Cerrar sesión de Qtile"),
]