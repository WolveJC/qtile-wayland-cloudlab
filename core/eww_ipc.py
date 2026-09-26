# ~/.config/qtile/core/eww_ipc.py
"""Módulo de comunicación IPC entre Qtile y Eww.

Escucha los hooks de Qtile para notificar cambios de grupos y ventanas enfocadas
directamente a las variables de Eww.
"""
import json
import shutil
import subprocess
from typing import Any

from libqtile import hook, qtile


def _eww_exe() -> str | None:
    return shutil.which("eww")


def _run_eww_update(var_name: str, payload: str) -> None:
    """Ejecuta `eww update` de forma asíncrona no bloqueante."""
    exe = _eww_exe()
    if not exe:
        return
    try:
        subprocess.Popen(
            [exe, "update", f"{var_name}={payload}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def update_groups(*args: Any, **kwargs: Any) -> None:
    """Serializa el estado de los grupos a JSON y lo envía a Eww."""
    if not qtile:
        return

    groups_data = []
    current_group = qtile.current_group.name if qtile.current_group else ""

    for g in qtile.groups:
        # Ignorar grupos ocultos o Scratchpads si existieran
        if g.name.startswith("scratchpad"):
            continue

        groups_data.append(
            {
                "name": g.name,
                "label": g.label or g.name,
                "focused": g.name == current_group,
                "occupied": len(g.windows) > 0,
            }
        )

    _run_eww_update("var_groups", json.dumps(groups_data))


def update_window_title(*args: Any, **kwargs: Any) -> None:
    """Envía el título de la ventana activa a Eww."""
    if not qtile:
        return

    window = qtile.current_window
    title = window.name if window and window.name else ""
    _run_eww_update("var_window", json.dumps(title))


def init_eww_ipc() -> None:
    """Registra las funciones en la tabla de hooks de Qtile."""
    # Cambios de grupo y de clientes
    hook.subscribe.setgroup(update_groups)
    hook.subscribe.changegroup(update_groups)
    hook.subscribe.client_managed(update_groups)
    hook.subscribe.client_killed(update_groups)

    # Cambios en la ventana activa
    hook.subscribe.client_focus(update_window_title)
    hook.subscribe.client_focus(update_groups)
    hook.subscribe.focus_change(update_window_title)
    hook.subscribe.focus_change(update_groups)

    # Estado inicial al arrancar/recargar Qtile
    hook.subscribe.startup_complete(update_groups)
    hook.subscribe.startup_complete(update_window_title)