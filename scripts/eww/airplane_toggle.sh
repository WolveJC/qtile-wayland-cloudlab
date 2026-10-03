#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/airplane_toggle.sh
#
# Modo avión: si Wi-Fi o Bluetooth está encendido, apaga los dos. Si los dos ya
# estaban apagados, los vuelve a prender los dos. No es un estado propio
# guardado en ningún lado -- se deriva de si alguno de los dos radios está
# encendido en este momento.

wifi_on="false"
if nmcli radio wifi 2>/dev/null | grep -q "^enabled$"; then
    wifi_on="true"
fi

bt_on="false"
if bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
    bt_on="true"
fi

if [ "$wifi_on" = "true" ] || [ "$bt_on" = "true" ]; then
    nmcli radio wifi off
    bluetoothctl power off
else
    nmcli radio wifi on
    bluetoothctl power on
fi
