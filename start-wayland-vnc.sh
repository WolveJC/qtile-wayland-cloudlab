#!/usr/bin/env bash

# Directorios de ejecución
export XDG_RUNTIME_DIR=/tmp/runtime-nix
mkdir -p $XDG_RUNTIME_DIR
chmod 0700 $XDG_RUNTIME_DIR

# 1. Configurar variables de renderizado sin pantalla física
export WLR_BACKENDS=headless
export WLR_LIBINPUT_NO_DEVICES=1
export WLR_RENDERER=pixman

# 2. Iniciar Qtile en modo Wayland en segundo plano
echo "Iniciando Qtile Wayland..."
qtile start -b wayland -c ./config.py &
QTILE_PID=$!

# Esperar a que el socket de Wayland sea creado por Qtile
echo "Esperando socket de Wayland..."
while [ ! -S "$XDG_RUNTIME_DIR/wayland-0" ] && [ ! -S "$XDG_RUNTIME_DIR/wayland-1" ]; do
    sleep 0.5
    done

    # Asignar la variable de entorno para que wayvnc la reconozca
    if [ -S "$XDG_RUNTIME_DIR/wayland-0" ]; then
        export WAYLAND_DISPLAY=wayland-0
        else
            export WAYLAND_DISPLAY=wayland-1
            fi

            echo "Wayland iniciado en $WAYLAND_DISPLAY"
            

sleep 2

# 3. Iniciar WayVNC para capturar el compositor Wayland
echo "Iniciando Servidor WayVNC..."
wayvnc 0.0.0.0 5900 &
WAYVNC_PID=$!

sleep 1

# 4. Iniciar noVNC en el puerto 6080 para acceder mediante el navegador web
echo "Iniciando puerto noVNC en http://localhost:6080 ..."
novnc --vnc localhost:5900 --listen 6080
