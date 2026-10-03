#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/bluetooth_listen.sh
#
# Escucha señales D-Bus de BlueZ (PropertiesChanged en org.bluez.Device1 y
# org.bluez.Adapter1) como disparador -- el proceso queda dormido de verdad hasta
# que el bus lo despierta por un evento real (conexión, desconexión, encendido/
# apagado del adaptador), en vez de preguntar cada 5 segundos aunque no haya
# pasado nada (lo que hacía bluetooth_status.sh, el script de polling anterior).
#
# A propósito NO usa 'bluetoothctl' en modo interactivo como disparador: ese modo
# tiene problemas reales de scripting (puede cerrarse solo al llegar a EOF en su
# stdin, y su salida trae códigos de control pensados para una terminal
# interactiva, no para un pipe). 'dbus-monitor' es una herramienta hecha para
# quedarse escuchando el bus indefinidamente, sin ninguno de esos problemas.
#
# dbus-monitor es solo el disparador: 'bluetoothctl' sigue siendo quien responde
# el estado real en cada evento (misma lógica que el script de polling anterior).

emit() {
    local powered="false" connected
    if bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
        powered="true"
    fi
    connected="$(bluetoothctl devices Connected 2>/dev/null | wc -l)"
    printf '{"powered":%s,"connected":%s}\n' "$powered" "${connected:-0}"
}

emit

dbus-monitor --system \
    "type='signal',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged',arg0='org.bluez.Device1'" \
    "type='signal',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged',arg0='org.bluez.Adapter1'" \
    2>/dev/null | while read -r line; do
        case "$line" in
            signal*)
                emit
                ;;
        esac
    done
