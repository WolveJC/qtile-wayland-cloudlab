# ~/.config/qtile/core/groups.py
from libqtile.config import Group, Key
from libqtile.lazy import lazy
from core.keys import keys, mod

groups = [Group(i) for i in ["1", "2", "3", "4", "5"]]

for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen(), desc=f"Ir al grupo {i.name}"),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name), desc=f"Mover ventana al grupo {i.name}"),
    ])