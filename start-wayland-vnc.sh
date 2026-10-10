#!/usr/bin/env bash
# Arranca Qtile (Wayland headless) + wayvnc + noVNC. Solo para el entorno VNC/Codespaces.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"

# Perfil: core/keys.py, config.py y autostart.sh se adaptan con esta variable
export QTILE_PROFILE=vnc

export XDG_RUNTIME_DIR=/tmp/runtime-nix
mkdir -p "$XDG_RUNTIME_DIR"
chmod 0700 "$XDG_RUNTIME_DIR"

# Renderizado sin pantalla fisica
export WLR_BACKENDS=headless
export WLR_LIBINPUT_NO_DEVICES=1
export WLR_RENDERER=pixman

# Apps Qt (overview.py) sobre Wayland
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

cleanup() { kill "${QTILE_PID:-}" "${WAYVNC_PID:-}" 2>/dev/null; }
trap cleanup EXIT INT TERM

echo "Iniciando Qtile Wayland..."
qtile start -b wayland -c ./config.py &
QTILE_PID=$!

echo "Esperando socket de Wayland..."
while [ ! -S "$XDG_RUNTIME_DIR/wayland-0" ] && [ ! -S "$XDG_RUNTIME_DIR/wayland-1" ]; do
    kill -0 "$QTILE_PID" 2>/dev/null || { echo "Qtile termino antes de crear el socket"; exit 1; }
    sleep 0.5
done

if [ -S "$XDG_RUNTIME_DIR/wayland-0" ]; then
    export WAYLAND_DISPLAY=wayland-0
else
    export WAYLAND_DISPLAY=wayland-1
fi
echo "Wayland iniciado en $WAYLAND_DISPLAY"
sleep 2

echo "Iniciando WayVNC..."
wayvnc 0.0.0.0 5900 &
WAYVNC_PID=$!
sleep 1

echo "Iniciando noVNC en http://localhost:6080 ..."
novnc --vnc localhost:5900 --listen 6080
