#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/bluetooth_connect.sh
# Conecta/desconecta el dispositivo Bluetooth pasado como argumento (MAC),
# según su estado actual (toggle).

mac="$1"
[ -z "$mac" ] && exit 1

if bluetoothctl info "$mac" 2>/dev/null | grep -q "Connected: yes"; then
    bluetoothctl disconnect "$mac"
else
    bluetoothctl connect "$mac"
fi
