#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/audio_set_sink.sh
#
# Cambia la salida de audio default a la que se pasa como argumento, y mueve
# los streams que ya están sonando a esa salida nueva -- sin esto, seguirían
# saliendo por la salida vieja hasta que la app que los generó se reinicie.

sink="$1"
[ -z "$sink" ] && exit 1

pactl set-default-sink "$sink"

pactl list sink-inputs short 2>/dev/null | cut -f1 | while read -r id; do
    pactl move-sink-input "$id" "$sink" 2>/dev/null
done
