# ~/.config/qtile/core/eww_ipc.py
"""Módulo de comunicación IPC entre Qtile y Eww.

Escucha los hooks de Qtile para notificar cambios de grupos y ventanas enfocadas
directamente a las variables de Eww.
"""
import json
import os
import shutil
import subprocess
from typing import Any

from libqtile import hook, qtile

# Qtile suele arrancar con el $PATH angosto que le da la sesión gráfica (SDDM, systemd
# --user, etc.), que casi nunca incluye ~/.cargo/bin. Si 'eww' se instaló con
# `cargo install eww` (el caso mas comun, no suele estar en los repos de las distros),
# shutil.which("eww") falla ahi aunque en tu shell interactiva ande perfecto. Por eso se
# revisan tambien las ubicaciones tipicas antes de rendirse.
_EWW_FALLBACK_PATHS = [
    os.path.expanduser("~/.cargo/bin/eww"),
    "/usr/local/bin/eww",
    "/usr/bin/eww",
]


def _eww_exe() -> str | None:
    exe = shutil.which("eww")
    if exe:
        return exe
    for candidate in _EWW_FALLBACK_PATHS:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


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
    # var_window se consume como texto plano en el .yuck (no con sintaxis jq/for),
    # así que se manda tal cual. json.dumps() aquí dejaría las comillas visibles en la barra.
    _run_eww_update("var_window", title)


# Un mismo cambio de grupo puede disparar varios de los hooks de abajo casi en
# simultáneo (setgroup + client_focus + focus_change, por ejemplo). Cada uno lanzaba
# su propio proceso 'eww update' async, sin orden garantizado entre ellos -- uno
# calculado con el estado viejo podía llegarle a Eww DESPUÉS de uno con el estado
# nuevo, dejando la barra pisada con datos viejos hasta el próximo evento. Se agrupan
# las ráfagas con call_later (mismo patrón que ya usa core/theme.py) para que, sin
# importar cuántos hooks disparen juntos, solo se mande una actualización, calculada
# una vez que el estado ya se asentó.
_DEBOUNCE_SECONDS = 0.05
_pending_groups_timer: Any = None
_pending_window_timer: Any = None


def _schedule_update_groups(*args: Any, **kwargs: Any) -> None:
    global _pending_groups_timer
    if qtile is None:
        return
    if _pending_groups_timer is not None:
        try:
            _pending_groups_timer.cancel()
        except Exception:
            pass
    _pending_groups_timer = qtile.call_later(_DEBOUNCE_SECONDS, update_groups)


def _schedule_update_window_title(*args: Any, **kwargs: Any) -> None:
    global _pending_window_timer
    if qtile is None:
        return
    if _pending_window_timer is not None:
        try:
            _pending_window_timer.cancel()
        except Exception:
            pass
    _pending_window_timer = qtile.call_later(_DEBOUNCE_SECONDS, update_window_title)


def init_eww_ipc() -> None:
    """Registra las funciones en la tabla de hooks de Qtile."""
    # Cambios de grupo y de clientes
    hook.subscribe.setgroup(_schedule_update_groups)
    hook.subscribe.changegroup(_schedule_update_groups)
    hook.subscribe.client_managed(_schedule_update_groups)
    hook.subscribe.client_killed(_schedule_update_groups)

    # Cambios en la ventana activa
    hook.subscribe.client_focus(_schedule_update_window_title)
    hook.subscribe.client_focus(_schedule_update_groups)
    hook.subscribe.focus_change(_schedule_update_window_title)
    hook.subscribe.focus_change(_schedule_update_groups)

    # Estado inicial al arrancar/recargar Qtile
    hook.subscribe.startup_complete(_schedule_update_groups)
    hook.subscribe.startup_complete(_schedule_update_window_title)
