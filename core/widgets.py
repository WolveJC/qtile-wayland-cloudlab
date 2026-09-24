# ~/.config/qtile/core/widgets.py
from libqtile import bar, widget
from core.wallpapers import DEFAULT_PALETTE as C  # colores iniciales; core/theme.py los cambia en vivo


def init_bar():
    return bar.Bar(
        [
            widget.GroupBox(
                highlight_method='line',
                background=C["bg_alt"],
                active=C["text"],
                inactive=C["text_dim"],
                this_current_screen_border=C["accent"],
                highlight_color=[C["bg_alt"], C["border_normal"]],
                ),
            widget.WindowName(foreground=C["text"]),
            widget.Clock(format="%Y-%m-%d %H:%M", foreground=C["accent2"]),
        ],
        28,
        background=C["bg"],
    )
