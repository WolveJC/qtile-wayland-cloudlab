#!/usr/bin/env bash
# ~/.config/qtile/scripts/launch_eww.sh
# Levanta el panel de Eww. Se invoca desde autostart.sh; también podés
# correrlo a mano para reiniciar el panel sin reiniciar Qtile.

# Si la sesión actual es KDE/Plasma, abortar ejecución
if [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$DESKTOP_SESSION" = "plasma" ]; then
    exit 0
fi

# Si Eww no está instalado, no hay nada que hacer (evita un "command not found" silencioso)
if ! command -v eww &> /dev/null; then
    echo "[launch_eww] 'eww' no está instalado o no está en el PATH; se omite el panel." >&2
    exit 0
fi

# Lock: si este script se dispara más de una vez en la misma sesión (algún reintento,
# el propio lanzador de sesión, lo que sea), solo la primera instancia hace kill+daemon.
# Sin esto, dos invocaciones casi simultáneas pueden ambas pasar el "eww kill" antes de
# que la otra levante su "eww daemon", y terminás con dos demonios corriendo a la vez.
LOCK="/tmp/qtile-eww-launch-${WAYLAND_DISPLAY:-default}.lock"
exec 9>"$LOCK"
if ! flock -n 9; then
    echo "[launch_eww] ya hay otra instancia de este script en curso; se omite." >&2
    exit 0
fi

# Si el demonio YA está vivo y respondiendo, no lo matamos ni lo reiniciamos: solo
# verificamos que la ventana 'bar' esté abierta. Matar un demonio sano en cada
# recarga de Qtile (startup_once solo corre una vez, pero por si acaso) es innecesario
# y es la otra forma de terminar con ventanas duplicadas.
if eww active-windows &> /dev/null; then
    if ! eww active-windows 2>/dev/null | grep -q "^bar"; then
        eww open bar 2>/dev/null
    fi
    exit 0
fi

# No hay demonio vivo (o el chequeo de arriba no lo encontró): forzar un estado limpio.
#
# 'eww kill' (shutdown amable vía IPC) demostró ser insuficiente en la práctica: puede
# dejar una superficie/proceso huérfano que ni el propio 'eww active-windows' del
# demonio nuevo conoce -- no responde a nada, no sale en ningún listado, y sigue
# pintada y congelada en pantalla. Solo un SIGKILL por nombre de proceso + reinicio
# limpio la elimina de verdad (confirmado a mano). Por eso acá se usa 'pkill -9 -x eww'
# en vez de 'eww kill'.
pkill -9 -x eww 2>/dev/null
sleep 0.5
eww daemon &
sleep 0.5

# 'eww daemon' arranca el proceso en segundo plano y vuelve enseguida, pero el socket
# IPC puede tardar un instante en quedar listo. Reintentar 'eww open' evita una carrera
# donde el primer intento falla porque el demonio todavía no contesta.
for _ in 1 2 3 4 5; do
    if eww open bar 2>/dev/null; then
        exit 0
    fi
    sleep 0.3
done

echo "[launch_eww] no se pudo abrir la ventana 'bar' tras varios intentos." >&2
exit 1
