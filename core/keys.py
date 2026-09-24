# ~/.config/qtile/core/keys.py
import os
import sys
from libqtile.config import Key
from libqtile.lazy import lazy

# --- Variables Principales ---
mod = "mod1" if os.environ.get("QTILE_NESTED") else "mod4"  # Tecla window o Alt

terminal = "kitty"

# Obtener la ruta base del repositorio dinámicamente
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ghost_theme = os.path.join(base_dir, "scripts", "ghost.rasi")
launcher = f"rofi -show drun -theme {ghost_theme}"
clipboard_menu = f"rofi -dmenu -theme {ghost_theme} -p clipboard"
venv_python_candidate = os.path.join(base_dir, "venv", "bin", "python")
if os.path.exists(venv_python_candidate):
    VENV_PYTHON = venv_python_candidate
else:
    VENV_PYTHON = sys.executable
overview_script = os.path.join(base_dir, "overview", "overview.py")

overview_cmd = f"{VENV_PYTHON} {overview_script}"

# Clutch: cambio de sesion Qtile -> KDE (registra en ~/.local/share/qtile/clutch.log)
clutch_script = os.path.join(base_dir, "scripts", "clutch.py")
clutch_to_kde = f"python3 {clutch_script} kde"

# Historial de portapapeles (cliphist ya corre desde autostart.sh; esto solo abre el menu).
# shell=True porque la tuberia (|) necesita /bin/sh -c, no un solo comando.
clipboard_pick = f"cliphist list | {clipboard_menu} | cliphist decode | wl-copy"

keys = [
    # -------------------------------------------------------------------------
    # Lanzadores del Entorno & GUI Custom
    # -------------------------------------------------------------------------
    Key([mod], "Return", lazy.spawn(terminal), desc="Abrir Terminal Kitty"),
    Key([mod], "space", lazy.spawn(launcher), desc="Lanzador Rofi Wayland"),

    # Modo Exposición / Overview (PySide6 Camaleónico)
    Key([mod], "Tab", lazy.spawn(overview_cmd), desc="Activar Modo Exposición"),
    Key([mod, "shift"], "e", lazy.spawn(clutch_to_kde), desc="Cambiar a sesion KDE"),

    # -------------------------------------------------------------------------
    # Portapapeles (cliphist + rofi)
    # -------------------------------------------------------------------------
    Key([mod], "v", lazy.spawn(clipboard_pick, shell=True), desc="Historial de portapapeles"),

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
    # Preseleccion de direccion (solo tiene efecto en PreselectBsp; en otros
    # layouts, Qtile ignora en silencio el primer comando y solo abre rofi).
    # Un solo uso: se consume con la proxima ventana que se abra, la pidas o no.
    # -------------------------------------------------------------------------
    Key([mod, "control"], "h", lazy.layout.preselect("left"), lazy.spawn(launcher),
        desc="Preseleccionar izquierda + elegir app"),
    Key([mod, "control"], "l", lazy.layout.preselect("right"), lazy.spawn(launcher),
        desc="Preseleccionar derecha + elegir app"),
    Key([mod, "control"], "j", lazy.layout.preselect("down"), lazy.spawn(launcher),
        desc="Preseleccionar abajo + elegir app"),
    Key([mod, "control"], "k", lazy.layout.preselect("up"), lazy.spawn(launcher),
        desc="Preseleccionar arriba + elegir app"),

    # -------------------------------------------------------------------------
    # Gestión de Ventanas y Sistema Qtile
    # -------------------------------------------------------------------------
    Key([mod], "q", lazy.window.kill(), desc="Cerrar ventana activa"),
    Key([mod, "control"], "space", lazy.next_layout(), desc="Cambiar de layout (Bsp/MonadTall/...)"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Recargar configuración de Qtile"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Cerrar sesión de Qtile"),
]
