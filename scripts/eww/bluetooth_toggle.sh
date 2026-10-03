#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/bluetooth_toggle.sh
# Prende/apaga el adaptador Bluetooth (toggle sobre el estado actual).

if bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
    bluetoothctl power off
else
    bluetoothctl power on
fi
