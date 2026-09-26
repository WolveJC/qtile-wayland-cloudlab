# ~/.config/qtile/core/autoscratch.py
from typing import Optional
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.group import _Group
from libqtile.scratchpad import ScratchPad

SCRATCH_GROUP_NAME: str = "scratchpad"
SCRATCH_DROPDOWN_NAME: str = "term"


def _get_scratchpad() -> Optional[ScratchPad]:
    """Obtiene el ScratchPad aplicando Type Narrowing explícito con isinstance."""
    if qtile is None:
        return None

    # groups_map retorna _Group, pero validamos si es la subclase ScratchPad
    group = qtile.groups_map.get(SCRATCH_GROUP_NAME)
    if isinstance(group, ScratchPad):
        return group

    return None


@hook.subscribe.client_managed
def on_client_managed(window: Window) -> None:
    """Oculta la terminal Scratchpad cuando se abre una aplicación en el grupo."""
    if qtile is None or window.group is None:
        return

    group: _Group = window.group
    if group.name == SCRATCH_GROUP_NAME:
        return

    scratch = _get_scratchpad()
    if scratch is None:
        return

    # Mypy sabe con certeza absoluta que 'scratch' es un ScratchPad
    dropdown = scratch.dropdowns.get(SCRATCH_DROPDOWN_NAME)
    if dropdown and dropdown.window:
        dropdown_info = dropdown.info()
        if isinstance(dropdown_info, dict) and dropdown_info.get("group") == group.name:
            scratch.hide(SCRATCH_DROPDOWN_NAME)


@hook.subscribe.client_killed
def on_client_killed(window: Window) -> None:
    """Muestra la terminal Scratchpad si la última aplicación del grupo se cierra."""
    if qtile is None or window.group is None:
        return

    group: _Group = window.group
    if group.name == SCRATCH_GROUP_NAME:
        return

    # client_killed se dispara ANTES de desvincular la ventana
    remaining_windows = [w for w in group.windows if w != window]

    if len(remaining_windows) == 0:
        scratch = _get_scratchpad()
        if scratch is None:
            return

        current_screen = qtile.current_screen
        if current_screen and current_screen.group and current_screen.group.name == group.name:
            scratch.show(SCRATCH_DROPDOWN_NAME)