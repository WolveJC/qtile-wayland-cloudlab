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
qtile start -b wayland &
QTILE_PID=$!

sleep 2

# 3. Iniciar WayVNC para capturar el compositor Wayland
echo "Iniciando Servidor WayVNC..."
wayvnc 0.0.0.0 5900 &
WAYVNC_PID=$!

sleep 1

# 4. Iniciar noVNC en el puerto 6080 para acceder mediante el navegador web
echo "Iniciando puerto noVNC en http://localhost:6080 ..."
novnc --vnc localhost:5900 --listen 6080
