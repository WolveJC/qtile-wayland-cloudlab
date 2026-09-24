# ~/.config/qtile/scripts/theme.fish
# Recolorea cada terminal NUEVA con el esquema activo de Qtile (pywal + capa de contraste).
# Las terminales que ya estaban abiertas las recolorea Qtile solo, al cambiar de grupo.
#
# Uso: agrega esta linea a ~/.config/fish/config.fish
#     source ~/.config/qtile/scripts/theme.fish
#
# Solo actua en la sesion Qtile: en KDE (u otra) no toca nada.
if status is-interactive; and test "$XDG_CURRENT_DESKTOP" = qtile
    set -l _wal ~/.cache/wal
    if test -r $_wal/sequences
        cat $_wal/sequences
    end
    if test -r $_wal/colors.fish
        # `set -g` en vez de `set`: colors.fish usa `set` a secas y eso modificaria variables
        # universales de fish (se guardarian en disco y llegarian tambien a la sesion KDE).
        sed 's/^set /set -g /' $_wal/colors.fish | source
    end
end
