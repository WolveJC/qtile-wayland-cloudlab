#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/volume_listen.sh
#
# Emite el estado de audio como una línea JSON por stdout: una vez al arrancar
# (para que el widget no arranque en blanco), y de nuevo cada vez que
# 'pactl subscribe' avisa un cambio de volumen/mute. Pensado para un
# (deflisten ...) de eww.yuck -- Eww lo arranca y lo mata solo, no pasa por Qtile.
#
# Requiere 'pamixer' instalado.

emit() {
    local vol muted
    vol="$(pamixer --get-volume 2>/dev/null)"
    muted="$(pamixer --get-mute 2>/dev/null)"
    printf '{"volume":%s,"muted":%s}\n' "${vol:-0}" "${muted:-false}"
}

# Estado inicial, antes de esperar el primer evento
emit

# 'pactl subscribe' emite una línea por CADA evento del server (streams
# abriéndose/cerrándose, cards, clientes...). Se filtra a sink/server para no
# spamear al widget con eventos de audio que no le importan.
pactl subscribe 2>/dev/null | while read -r line; do
    case "$line" in
        *"on sink"*|*"on server"*)
            emit
            ;;
    esac
done
