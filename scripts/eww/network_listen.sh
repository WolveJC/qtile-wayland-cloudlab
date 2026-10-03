#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/network_listen.sh
#
# Emite el estado de Wi-Fi como JSON por stdout: una vez al arrancar, y de nuevo
# cada vez que 'nmcli monitor' avisa un cambio (conexión, desconexión, señal).
# Pensado para un (deflisten ...) de eww.yuck.
#
# Limitación conocida: el parseo asume que el SSID no contiene ':' (nmcli -t usa
# ':' como separador de campo). Un SSID con ':' en el nombre rompería el corte.

emit() {
    local line connected ssid signal
    connected="false"
    ssid=""
    signal=0

    line="$(nmcli -t -f ACTIVE,SSID,SIGNAL dev wifi 2>/dev/null | grep '^yes:' | head -n1)"
    if [ -n "$line" ]; then
        connected="true"
        ssid="$(echo "$line" | cut -d: -f2)"
        signal="$(echo "$line" | cut -d: -f3)"
        # Escapar comillas por si el SSID trae alguna
        ssid="${ssid//\"/\\\"}"
    fi

    printf '{"connected":%s,"ssid":"%s","signal":%s}\n' "$connected" "$ssid" "${signal:-0}"
}

emit

nmcli monitor 2>/dev/null | while read -r _line; do
    emit
done
