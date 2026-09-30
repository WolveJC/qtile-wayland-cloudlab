# ~/.config/qtile/core/groups.py
from typing import List
from libqtile.config import Group, Key
from libqtile.lazy import lazy

from core.keys import keys, mod
import core.autoscratch  # noqa: F401 (Registra los hooks de la terminal de relleno)

# Workspaces estándar (1 al 5)
groups: List[Group] = [Group(i) for i in ["1", "2", "3", "4", "5"]]

# Asociación de atajos de teclado para Workspaces estándar
for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen(), desc=f"Ir al grupo {i.name}"),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name), desc=f"Mover ventana al grupo {i.name}"),
    ])

# La terminal de "relleno" para escritorios vacíos ya no es un ScratchPad/DropDown
# (esos SIEMPRE son flotantes en libqtile, sin excepción -- ver core/autoscratch.py).
# Es una ventana normal, gestionada por completo desde core/autoscratch.py vía
# qtile.spawn(..., group=...) + hooks. No hay bind de toggle manual (Mod+grave queda
# libre; si querés reasignarlo a otra cosa, avisame).
#
# Sí hace falta UN grupo: el "storage" donde autoscratch.py esconde la terminal
# (en vez de matarla) cuando se abre una app real en su lugar -- moverla ahí, sin
# switch_group, la saca de la vista sin tocar su proceso (si la app que abriste
# nació DESDE esa terminal, como su hijo, seguiría corriendo). Se declara al final
# para no tocar cuál grupo queda visible por defecto en la pantalla al arrancar.
# El nombre empieza con "scratchpad" a propósito: así el filtro que ya existe en
# core/eww_ipc.py (pensado originalmente para el viejo ScratchPad) lo excluye de la
# barra sin tener que tocar ese archivo también.
groups.append(Group(core.autoscratch.HIDDEN_GROUP_NAME))
