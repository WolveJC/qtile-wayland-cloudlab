# ~/.config/qtile/core/layouts.py
from libqtile import layout
from core.bsp_preselect import PreselectBsp
from core.wallpapers import DEFAULT_PALETTE as C  # colores iniciales; core/theme.py los cambia en vivo

layout_theme = {
    "border_width": 2,
    "margin": 8,
    "border_focus": C["accent"],
    "border_normal": C["border_normal"],
}

layouts = [
    PreselectBsp(**layout_theme),
    layout.MonadTall(**layout_theme),
    layout.Columns(**layout_theme),
    layout.Max(),
]
