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
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP
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
  "bg_overlay": "rgba(17, 17, 27, 0.6)"
}
EOF
fi

# SCSS compartido por defecto (Waybar + SwayNC lo importan): evita que
# style/build.sh falle si corre antes de que core/theme.py escriba el real.
if [ ! -f "$RAM_DIR/_variables.scss" ]; then
    cat <<EOF > "$RAM_DIR/_variables.scss"
\$accent: #89b4fa;
\$accent2: #f5e0dc;
\$bg: #1e1e2e;
\$bg_alt: #181825;
\$border_normal: #313244;
\$text: #cdd6f4;
\$text_dim: #a6adc8;
\$transition_ms: 600ms;
EOF
fi

#  =============================================================================
# 3. WALLPAPERS (SWWW)
# =============================================================================
# Solo levanta el demonio; el wallpaper real de cada grupo lo pone
# core/theme.py en cuanto Qtile dispara sus hooks de arranque.
if [ -f "$SCRIPT_DIR/scripts/launch_swww.sh" ]; then
    bash "$SCRIPT_DIR/scripts/launch_swww.sh" &
fi

#  =============================================================================
# 4. ESTILOS COMPARTIDOS (WAYBAR + SWAYNC)
# =============================================================================
# Primera compilación: con los valores por defecto de arriba hasta que
# core/theme.py escriba la paleta real del wallpaper (dispara su propio
# build.sh en cada cambio, esto es solo para que no arranquen sin estilos).
if [ -f "$SCRIPT_DIR/style/build.sh" ]; then
    bash "$SCRIPT_DIR/style/build.sh"
fi

#  =============================================================================
# 5. BARRA (WAYBAR)
# =============================================================================
if [ -f "$SCRIPT_DIR/scripts/launch_waybar.sh" ]; then
    bash "$SCRIPT_DIR/scripts/launch_waybar.sh" &
fi

#  =============================================================================
# 6. NOTIFICACIONES Y CENTRO DE MANDO (SWAYNC)
# =============================================================================
if [ -f "$SCRIPT_DIR/scripts/launch_swaync.sh" ]; then
    bash "$SCRIPT_DIR/scripts/launch_swaync.sh" &
fi

#  =============================================================================
# 7. WIDGETS DECORATIVOS DE ESCRITORIO (EWW)
# =============================================================================
if [ -f "$SCRIPT_DIR/scripts/launch_eww.sh" ]; then
    bash "$SCRIPT_DIR/scripts/launch_eww.sh" &
fi

#  =============================================================================
# 8. BLOQUEO POR INACTIVIDAD (SWAYIDLE + HYPRLOCK) -- PENDIENTE, A PROPOSITO
# =============================================================================
# El script ya existe y funciona (scripts/launch_lock_idle.sh), pero se deja
# sin activar por ahora. Descomentar cuando se retome ese frente.
# if [ -f "$SCRIPT_DIR/scripts/launch_lock_idle.sh" ]; then
#     bash "$SCRIPT_DIR/scripts/launch_lock_idle.sh" &
# fi

#  =============================================================================
# 9. DEMONIOS DE SESION
# =============================================================================
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
