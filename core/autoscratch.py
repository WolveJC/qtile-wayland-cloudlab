# ~/.config/qtile/core/autoscratch.py
"""Terminal de "relleno" para escritorios vacíos.

Es una ventana normal, tileada por el layout como cualquier otra (no un
ScratchPad/DropDown de libqtile: esos SIEMPRE son flotantes, sin excepción -- ver
libqtile/scratchpad.py, WindowVisibilityToggler.show()).

- Si cambiás a un grupo completamente vacío, se abre una terminal ahí.
- Si abrís una app real en ese mismo grupo, la terminal se ESCONDE -- se mueve al
  grupo interno HIDDEN_GROUP_NAME, nunca se muestra en pantalla -- para que la app
  real quede sola en el layout.
- Si cerrás esa app y el grupo vuelve a quedar vacío, la terminal escondida vuelve
  a su grupo original (o se lanza una nueva si por algún motivo no hay ninguna
  guardada para ese grupo).
- Si el grupo ya tiene la terminal de relleno (o cualquier ventana), no se abre
  una segunda.

Por qué "esconder" y no "cerrar" (como en la primera versión de este archivo):
si la app que abriste la lanzaste DESDE la propia terminal (como hijo de su shell
-- por ejemplo tipeando el comando a mano), cerrar/matar la terminal le manda una
señal de cierre a todo lo que colgaba de su pty, y la app recién abierta muere con
ella. Esconder (mover de grupo, sin tocar el proceso) no tiene ese problema: la
terminal y cualquier cosa lanzada desde ella siguen vivas, solo que fuera de vista.

Se identifica por wm_class ("scratchpad_term").
"""
from typing import Any
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.config import Match
from libqtile.group import _Group

TERMINAL_WM_CLASS = "scratchpad_term"
TERMINAL_CMD = ["kitty", "--class", TERMINAL_WM_CLASS]

# Grupo interno donde se esconde la terminal; nunca se muestra en pantalla (ningún
# bind ni hook lo lleva a un screen). Declarado en core/groups.py. El nombre empieza
# con "scratchpad" a propósito, para reusar el filtro que ya excluye ese prefijo de
# la barra en core/eww_ipc.py, sin tener que tocar ese archivo también.
HIDDEN_GROUP_NAME = "scratchpad_hidden"

_FILLER_MATCH = Match(wm_class=TERMINAL_WM_CLASS)

# Grupos para los que ya se pidió un spawn y todavía no aparece la ventana.
_spawn_pending: set[str] = set()

# Grupo original -> ventana de relleno escondida ahí (para poder devolverla al
# grupo correcto cuando la app que la desplazó se cierre).
_hidden_fillers: dict[str, Window] = {}


def _is_filler(window: Window) -> bool:
    return _FILLER_MATCH.compare(window)


def _group_has_filler(group: _Group) -> bool:
    return any(_is_filler(w) for w in group.windows)


def _spawn_filler(group_name: str) -> None:
    if qtile is None or group_name in _spawn_pending:
        return
    _spawn_pending.add(group_name)
    qtile.spawn(TERMINAL_CMD, group=group_name)


def _ensure_filler(group_name: str) -> None:
    """Garantiza que group_name tenga la terminal de relleno: la trae de vuelta si
    había una escondida por este mismo grupo, o lanza una nueva si no hay ninguna."""
    if qtile is None:
        return

    group = qtile.groups_map.get(group_name)
    if group is not None and _group_has_filler(group):
        return  # ya tiene una, no hace falta nada

    hidden = _hidden_fillers.pop(group_name, None)
    if hidden is not None:
        try:
            hidden.togroup(group_name)
            return
        except Exception:
            pass  # la ventana escondida ya no existe; se cae al spawn de abajo

    _spawn_filler(group_name)


def _hide_filler(window: Window, origin_group_name: str) -> None:
    _hidden_fillers[origin_group_name] = window
    window.togroup(HIDDEN_GROUP_NAME, switch_group=False)


@hook.subscribe.client_managed
def on_client_managed(window: Window) -> None:
    """Si se abre una app real en un grupo que tenía la terminal de relleno, la esconde."""
    if qtile is None or window.group is None:
        return

    group: _Group = window.group

    if _is_filler(window):
        # Esta ventana ES la terminal que acabamos de pedir (o que volvió de estar
        # escondida): ya cumplió su propósito de "pendiente".
        _spawn_pending.discard(group.name)
        return

    # Se abrió una app real: si había una terminal de relleno en este grupo,
    # se esconde (no se mata) para que la app quede sola en el layout.
    for w in list(group.windows):
        if w is not window and _is_filler(w):
            _hide_filler(w, group.name)


@hook.subscribe.client_killed
def on_client_killed(window: Window) -> None:
    """Si se cierra la última app real de un grupo, trae de vuelta (o lanza) la terminal."""
    if qtile is None or window.group is None:
        return

    group: _Group = window.group

    if _is_filler(window):
        # Se cerró la terminal misma (a mano, o murió estando escondida): sacarla de
        # cualquier registro de "escondida" para no intentar devolver una ventana
        # que ya no existe.
        for name in [n for n, w in _hidden_fillers.items() if w == window]:
            _hidden_fillers.pop(name, None)
        return

    # client_killed se dispara ANTES de desvincular la ventana del grupo
    remaining = [w for w in group.windows if w != window]
    if len(remaining) == 0:
        _ensure_filler(group.name)


@hook.subscribe.setgroup
def on_setgroup(*args: Any, **kwargs: Any) -> None:
    """Si cambiás a un grupo completamente vacío, le asegura la terminal de relleno."""
    if qtile is None:
        return

    current_screen = qtile.current_screen
    if current_screen is None or current_screen.group is None:
        return

    group: _Group = current_screen.group
    if group.name == HIDDEN_GROUP_NAME:
        return

    if len(group.windows) == 0:
        _ensure_filler(group.name)
