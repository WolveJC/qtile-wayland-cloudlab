#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/wifi_scan.sh
#
# Emite el estado completo de Wi-Fi para el popup (separado de network_listen.sh,
# que solo alimenta el resumen chico de la barra): si el radio está encendido, y
# la lista de redes visibles. Disparado por 'nmcli monitor', igual que
# network_listen.sh.
#
# Misma limitación que network_listen.sh: el parseo asume que el SSID no
# contiene ':' (nmcli -t usa ':' como separador de campo).

emit() {
    local enabled="false"
    if nmcli radio wifi 2>/dev/null | grep -q "^enabled$"; then
        enabled="true"
    fi

    local networks
    networks="$(nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list 2>/dev/null | awk -F: '
        BEGIN { first=1; printf "[" }
        {
            if ($2 == "") next
            inuse = ($1 == "*") ? "true" : "false"
            ssid = $2
            signal = $3
            secured = ($4 != "" && $4 != "--") ? "true" : "false"
            if (!first) printf ","
            first = 0
            gsub(/"/, "\\\"", ssid)
            printf "{\"ssid\":\"%s\",\"signal\":%s,\"active\":%s,\"secured\":%s}", ssid, signal, inuse, secured
        }
        END { print "]" }
    ')"

    printf '{"enabled":%s,"networks":%s}\n' "$enabled" "${networks:-[]}"
}

emit

nmcli monitor 2>/dev/null | while read -r _line; do
    emit
done
