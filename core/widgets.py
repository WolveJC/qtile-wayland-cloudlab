# ~/.config/qtile/core/widgets.py
from libqtile import bar, widget

def init_bar():
    return bar.Bar(
        [
            widget.GroupBox(highlight_method='line', background="#11111b"),
            widget.WindowName(foreground="#cdd6f4"),
            widget.Clock(format="%Y-%m-%d %H:%M", foreground="#f9e2af"),
        ],
        28,
        background="#181825",
    )