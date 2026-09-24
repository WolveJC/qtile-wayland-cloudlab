# ~/.config/qtile/core/bsp_preselect.py
"""Bsp con preseleccion de direccion, al estilo bspwm.

Bsp decide la orientacion del split SOLO por el aspecto (ancho/alto) del hueco donde cae la
ventana nueva (ver libqtile.layout.bsp._BspNode.insert): no hay ningun parametro de "direccion"
que Qtile exponga. PreselectBsp guarda una direccion pendiente ("left"/"right"/"up"/"down"),
fijada por preselect(), y la usa UNA SOLA VEZ para la proxima ventana que se abra en el grupo;
si no hay ninguna pendiente, el comportamiento es exactamente el de Bsp normal (fair, ratio,
lower_right... todo se respeta igual).
"""
from typing import Optional

from libqtile.backend.base import Window
from libqtile.command.base import expose_command
from libqtile.layout.bsp import Bsp

# direccion -> (split horizontal (lado a lado) o vertical (arriba/abajo), posicion del NUEVO cliente)
_HORIZONTAL = {"left": True, "right": True, "up": False, "down": False}
_NEW_IDX = {"left": 0, "right": 1, "up": 0, "down": 1}


class PreselectBsp(Bsp):
    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._pending: Optional[str] = None

    @expose_command()
    def preselect(self, direction: str) -> None:
        """Fija la direccion en la que se abrira la PROXIMA ventana de este grupo."""
        if direction in _HORIZONTAL:
            self._pending = direction

    @expose_command()
    def preselect_cancel(self) -> None:
        self._pending = None

    def add_client(self, client: Window) -> None:
        direction = self._pending
        self._pending = None  # se consume: una sola vez, haya funcionado o no

        # Sin direccion pendiente, o grupo vacio (nada de que partir): comportamiento normal.
        if direction is None or self.current is None or self.current.client is None:
            super().add_client(client)
            return

        node = self.current
        new_leaf = node.insert(client, _NEW_IDX[direction], self.ratio)
        node.split_horizontal = _HORIZONTAL[direction]  # insert() lo infirio por aspecto; se corrige
        self.current = new_leaf
