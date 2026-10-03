#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/bluetooth_devices.sh
#
# Emite el estado completo de Bluetooth para el popup (separado de
# bluetooth_listen.sh, que solo alimenta el resumen chico de la barra): si el
# adaptador está encendido, y la lista de dispositivos emparejados con su
# estado de conexión. Disparado por señales D-Bus de BlueZ, mismo patrón que
# bluetooth_listen.sh (no por bluetoothctl interactivo -- ver ese script para
# el motivo).

emit() {
    local enabled="false"
    if bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
        enabled="true"
    fi

    local devices="[" first=1 mac name connected
    while read -r _word mac name; do
        [ -z "$mac" ] && continue
        connected="false"
        if bluetoothctl info "$mac" 2>/dev/null | grep -q "Connected: yes"; then
            connected="true"
        fi
        if [ "$first" -eq 0 ]; then
            devices+=","
        fi
        first=0
        name="${name//\"/\\\"}"
        devices+="{\"mac\":\"$mac\",\"name\":\"$name\",\"connected\":$connected}"
    done < <(bluetoothctl devices 2>/dev/null)
    devices+="]"

    printf '{"enabled":%s,"devices":%s}\n' "$enabled" "$devices"
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
