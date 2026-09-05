# ~/.config/qtile/core/floating.py
from libqtile import layout
from libqtile.config import Click, Drag, Match
from libqtile.lazy import lazy
from core.keys import mod

# Atajos de Ratón para mover/redimensionar ventanas flotantes
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

# Reglas para forzar flotación automáticas en diálogos
floating_layout = layout.Floating(
    border_focus="#89b4fa",
    border_normal="#1e1e2e",
    border_width=2,
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # Diálogos git/reset
        Match(wm_class="makebranch"),
        Match(wm_class="maketag"),
        Match(wm_class="ssh-askpass"),   # Diálogos de clave SSH
        Match(title="branchdialog"),
        Match(title="pinentry"),         # Diálogos GPG/KWallet
        Match(wm_class="pavucontrol"),   # Control de volumen
    ]
)