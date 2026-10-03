#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/audio_sinks.sh
#
# Emite la lista de salidas de audio disponibles (altavoces, auriculares
# Bluetooth, HDMI...) como JSON: [{"name":..,"description":..,"default":bool}, ..]
#
# Mismo disparador que volume_listen.sh (pactl subscribe), pero en su propio
# proceso -- cada script escucha solo lo que le importa a él; más simple de
# leer y debuggear por separado que meter las dos cosas juntas.

emit() {
    local default_sink
    default_sink="$(pactl get-default-sink 2>/dev/null)"

    pactl list sinks 2>/dev/null | awk -v default="$default_sink" '
        BEGIN { name=""; desc=""; first=1; printf "[" }
        /^Sink #/ { if (name != "") emit(); name=""; desc="" }
        /^[ \t]*Name: / { sub(/^[ \t]*Name: /, ""); name=$0 }
        /^[ \t]*Description: / { sub(/^[ \t]*Description: /, ""); desc=$0 }
        END { if (name != "") emit(); print "]" }
        function emit() {
            if (!first) printf ","
            first = 0
            is_default = (name == default) ? "true" : "false"
            gsub(/"/, "\\\"", desc)
            printf "{\"name\":\"%s\",\"description\":\"%s\",\"default\":%s}", name, desc, is_default
        }
    '
}

emit

pactl subscribe 2>/dev/null | while read -r line; do
    case "$line" in
        *"on sink"*|*"on server"*)
            emit
            ;;
    esac
done
