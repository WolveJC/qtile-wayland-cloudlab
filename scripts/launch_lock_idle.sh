#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_lock_idle.sh
#
# Arranca swayidle con una lista de acciones por inactividad:
#   - a los 5 min: bloquea la pantalla con hyprlock (funciona standalone, no
#     depende de estar corriendo Hyprland -- es solo la pantalla de bloqueo).
#   - poco despues: apaga los monitores, SI hay 'wlopm' instalado (protocolo
#     wlr-output-power-management, generico de cualquier compositor wlroots,
#     no especifico de Hyprland/Sway -- si no esta instalado, se omite ese
#     paso puntual y el resto sigue funcionando).
#   - al reanudar: vuelve a prender los monitores.
#   - antes de suspender: bloquea tambien.
#
# Los tiempos (300s / 310s) son un default razonable, no estan pensados en
# piedra -- ajustalos si te quedan muy cortos o muy largos.

if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

if ! command -v swayidle &> /dev/null; then
    echo "[launch_lock_idle] 'swayidle' no está instalado; se omite bloqueo por inactividad." >&2
    exit 0
fi

if ! command -v hyprlock &> /dev/null; then
    echo "[launch_lock_idle] 'hyprlock' no está instalado; se omite bloqueo por inactividad." >&2
    exit 0
fi

if pgrep -x swayidle &> /dev/null; then
    exit 0
fi

DPMS_OFF_CMD="true"
DPMS_ON_CMD="true"
if command -v wlopm &> /dev/null; then
    DPMS_OFF_CMD="wlopm --off '*'"
    DPMS_ON_CMD="wlopm --on '*'"
fi

LOG_DIR="$HOME/.local/share/qtile/logs"
mkdir -p "$LOG_DIR"
source "$(dirname "${BASH_SOURCE[0]}")/lib_log.sh"

run_logged "$LOG_DIR/swayidle.log" swayidle -w \
    timeout 300 "hyprlock" \
    timeout 310 "$DPMS_OFF_CMD" \
    resume "$DPMS_ON_CMD" \
    before-sleep "hyprlock"