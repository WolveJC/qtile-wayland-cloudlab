# ~/.config/qtile/core/groups.py
from typing import List
from libqtile.config import DropDown, Group, Key, ScratchPad
from libqtile.lazy import lazy

from core.keys import keys, mod
import core.autoscratch  # noqa: F401 (Registra los hooks de automanejo)

# Workspaces estándar (1 al 5)
groups: List[Group | ScratchPad] = [Group(i) for i in ["1", "2", "3", "4", "5"]]

# Asociación de atajos de teclado para Workspaces estándar
for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen(), desc=f"Ir al grupo {i.name}"),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name), desc=f"Mover ventana al grupo {i.name}"),
    ])

# Configuración del ScratchPad de Terminal Auto-Desplegable
scratchpad_config = ScratchPad(
    "scratchpad",
    [
        DropDown(
            "term",
            "kitty --class scratchpad_term -e fastfetch",
            x=0.15,
            y=0.15,
            width=0.70,
            height=0.70,
            on_focus_lost_hide=False,
            opacity=0.95,
            warp_pointer=False,
        ),
    ],
)

groups.append(scratchpad_config)

# Atajo de alternancia manual para la Scratchpad (Mod + grave / Tecla º/~)
keys.append(
    Key(
        [mod],
        "grave",
        lazy.group["scratchpad"].dropdown_toggle("term"),
        desc="Alternar visibilidad de Terminal Scratchpad",
    )
)