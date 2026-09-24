#!/usr/bin/env bash
# ~/.config/qtile/autostart.sh
# Se ejecuta una vez por sesion de Qtile (hook startup_once en config.py).

# Ruta base del repositorio (funciona clonado en cualquier lugar)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PY="$(command -v python3)"

# Deteccion de prueba anidada: si heredamos KDE, Qtile corre como ventana dentro de Plasma.
# En una sesion real (SDDM/TTY) esta variable no dice KDE.
NESTED=0
[[ "$XDG_CURRENT_DESKTOP" == *KDE* ]] && NESTED=1

# =============================================================================
# 0. ENTORNO DE SESION
# =============================================================================
# Qtile no define XDG_CURRENT_DESKTOP; los portales (xdg-desktop-portal) y
# muchas apps lo usan. En pruebas anidadas dentro de KDE se respeta el existente.
export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-qtile}"

# Compartir el entorno grafico con D-Bus / systemd --user para que las apps
# lanzadas por activacion D-Bus (portales, notificaciones) encuentren Wayland.
if command -v dbus-update-activation-environment &> /dev/null; then
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &
fi

# =============================================================================
# 1. CLUTCH: limpiar autologin temporal de SDDM (si venimos de un cambio de sesion)
# =============================================================================
if [ -f "$SCRIPT_DIR/scripts/clutch.py" ]; then
    "$PY" "$SCRIPT_DIR/scripts/clutch.py" --clear &
fi

# =============================================================================
# 2. PREPARACION EN RAM (/dev/shm)
# =============================================================================
RAM_DIR="/dev/shm/qtile_overview"
mkdir -p "$RAM_DIR"

# Paleta por defecto si no existe, para evitar errores de lectura al inicio
if [ ! -f "$RAM_DIR/palette.json" ]; then
    cat <<EOF > "$RAM_DIR/palette.json"
{
  "border_active": "#89b4fa",
  "border_inactive": "rgba(255, 255, 255, 0.1)",
  "bg_card_active": "rgba(49, 50, 68, 0.8)",
  "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
  "text_color": "#cdd6f4",
  "bg_overlay": "rgba(15, 15, 23, 0.5)"
}
EOF
fi

#  =============================================================================
# 3. DEMONIOS DE SESION
# =============================================================================
# Notificaciones (se omite en pruebas anidadas: KDE ya tiene su propio demonio)
if [ "$NESTED" = 0 ] && command -v mako &> /dev/null; then
    mako &
fi

# Historial del portapapeles
if command -v cliphist &> /dev/null && command -v wl-paste &> /dev/null; then
    wl-paste --watch cliphist store &
fi

# Agente de autenticacion polkit (pide contrasena en apps graficas que la necesiten).
# Opcional: solo arranca si esta instalado (paquete: polkit-kde-agent).
POLKIT_AGENT="/usr/lib/polkit-kde-authentication-agent-1"
if [ "$NESTED" = 0 ] && [ -x "$POLKIT_AGENT" ]; then
    "$POLKIT_AGENT" &
fi
