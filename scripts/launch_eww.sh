#!/usr/bin/env bash

# Si la sesión actual es KDE/Plasma, abortar ejecución
if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

# Cerrar instancias previas de Eww
eww kill 2>/dev/null

# Iniciar el demonio de Eww si no está corriendo
eww daemon

# Abrir la ventana del panel definida en eww.yuck
eww open bar