#!/usr/bin/env bash
# ~/.config/qtile/scripts/eww/wifi_toggle.sh
# Prende/apaga el radio Wi-Fi (toggle sobre el estado actual).

if nmcli radio wifi 2>/dev/null | grep -q "^enabled$"; then
    nmcli radio wifi off
else
    nmcli radio wifi on
fi
