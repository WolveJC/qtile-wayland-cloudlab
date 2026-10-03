#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/audio_apps.sh
#
# Emite la lista de apps reproduciendo audio en este momento (sink-inputs) como
# JSON: [{"id":N,"name":"...","volume":N,"muted":bool}, ...]. Esto es el
# mezclador por app (independiente del volumen general): cada app tiene su
# propio volumen/mute en PipeWire, separado del volumen de la salida.

emit() {
    pactl list sink-inputs 2>/dev/null | awk '
        BEGIN { id=""; name=""; volume=0; muted="false"; first=1; printf "[" }
        /^Sink Input #/ {
            if (id != "") emit()
            sub(/^Sink Input #/, ""); id=$0
            name=""; volume=0; muted="false"
        }
        /application\.name = / {
            match($0, /"[^"]*"/)
            if (RSTART > 0) name = substr($0, RSTART+1, RLENGTH-2)
        }
        /^[ \t]*Volume:/ {
            match($0, /[0-9]+%/)
            if (RSTART > 0) volume = substr($0, RSTART, RLENGTH-1)
        }
        /^[ \t]*Mute(d)?:/ {
            if ($0 ~ /yes/) muted="true"; else muted="false"
        }
        END { if (id != "") emit(); print "]" }
        function emit() {
            if (!first) printf ","
            first = 0
            gsub(/"/, "\\\"", name)
            if (name == "") name = "(desconocido)"
            printf "{\"id\":%s,\"name\":\"%s\",\"volume\":%s,\"muted\":%s}", id, name, volume, muted
        }
    '
}

emit

pactl subscribe 2>/dev/null | while read -r line; do
    case "$line" in
        *"sink-input"*)
            emit
            ;;
    esac
done
