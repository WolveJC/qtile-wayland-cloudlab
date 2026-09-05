# ~/.config/qtile/core/layouts.py
from libqtile import layout

layout_theme = {
    "border_width": 2,
    "margin": 8,
    "border_focus": "#89b4fa",
    "border_normal": "#1e1e2e",
}

layouts = [
    layout.MonadTall(**layout_theme),
    layout.Columns(**layout_theme),
    layout.Max(),
]