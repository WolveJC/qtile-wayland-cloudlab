# ~/.config/qtile/core/theme.py
"""Tema dinamico: cada grupo tiene su wallpaper y los colores salen de ese wallpaper.

Al cambiar de grupo (hook `setgroup`):
1. pone el wallpaper del grupo (awww img, con transición de fundido -- awww-daemon
   debe estar corriendo ya, ver scripts/launch_swww.sh),
2. recolorea en caliente bordes de layouts (con animacion gradual RGB), barra y widgets (sin reload_config),
3. en un hilo aparte, aplica el esquema (pywal + capa de contraste) al resto del sistema:
   terminales abiertas, plantillas en ~/.cache/wal, hook opcional del usuario.
   Tambien se reaplica al abrirse una ventana nueva (una terminal nueva nace sin colores).

pywal tarda segundos en calcular un esquema: NUNCA se ejecuta en el hilo de Qtile. Si la paleta
del grupo aun no esta calculada, se pone el wallpaper, se calcula en un hilo y se re-aplica al acabar.

Se importa desde config.py; los hooks se registran al importar. Todo esta envuelto en
try/except: un fallo aqui NUNCA debe tumbar la config de Qtile.
"""
import json
import os
import shutil
import subprocess
import threading
from typing import Any, Optional, TypedDict, cast

from libqtile import hook, qtile as _qtile_obj
from libqtile.log_utils import logger

from core import wallpapers

# Solución pragmática al stub interno de Qtile (_UndefinedQtile)
qtile: Any = _qtile_obj

_DEBOUNCE_GROUP: float = 0.12   # cambiar de grupo rapido no lanza un awww img por cada salto
_DEBOUNCE_START: float = 0.40   # dar tiempo a que la barra termine de configurarse
_DEBOUNCE_CLIENT: float = 1.0   # una ventana nueva necesita un instante para tener su pty

# --------------------------------------------------------------------------- Duración del "camaleón"
# Un solo número controla TODO el cambio de color al saltar de grupo:
#   - la animación de bordes de Qtile (interpolación RGB, fotograma a fotograma), y
#   - la transición CSS de Waybar/SwayNC (se exporta como $transition_ms en
#     _variables.scss; waybar.scss/swaync.scss lo usan en vez de tener valores
#     sueltos hardcodeados por selector).
# Subilo si te parece muy rápido, bajalo si te parece lento -- no hace falta tocar nada más.
THEME_TRANSITION_SECONDS: float = 0.6

_ANIM_FRAME_INTERVAL: float = 0.025  # ~40 fps; esto define la fluidez, no la duración total


class ThemeState(TypedDict):
    wallpaper: Optional[str]                    # ultimo wallpaper puesto (para no repetir el mismo awww img)
    palette: Optional[wallpapers.Palette]        # ultima paleta aplicada a la barra/bordes
    warned: bool                                 # ya se avisó una vez de que falta awww
    scheme_wp: Optional[str]                     # wallpaper cuyo esquema ya se mando a aplicar
    gen: int                                     # generacion actual (invalida aplicaciones obsoletas)
    computing: set[str]                          # wallpapers cuya paleta se esta calculando ahora
    warned_scheme: bool                          # ya se avisó una vez de que pywal no aplico el esquema


_pending: Any = None
_reapply: Any = None
_border_anim_timer: Any = None  # Temporizador para la animación de bordes de ventanas

_state: ThemeState = {
    "wallpaper": None,
    "palette": None,
    "warned": False,
    "scheme_wp": None,
    "gen": 0,
    "computing": set(),
    "warned_scheme": False
}

# (atributo del layout, clave de la paleta)
_LAYOUT_ATTRS = (
    ("border_focus", "accent"),
    ("border_normal", "border_normal"),
    ("border_focus_stack", "accent"),
    ("border_normal_stack", "border_normal"),
)


# --------------------------------------------------------------------------- Interpolación RGB (Módulo 10: Camaleón)
def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convierte un color en formato hexadecimal (#RRGGBB) a una tupla de enteros RGB."""
    clean_hex = hex_str.lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join(c * 2 for c in clean_hex)
    if len(clean_hex) != 6:
        return (0, 0, 0)
    try:
        return (int(clean_hex[0:2], 16), int(clean_hex[2:4], 16), int(clean_hex[4:6], 16))
    except ValueError:
        return (0, 0, 0)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convierte una tupla de enteros RGB a formato hexadecimal (#RRGGBB)."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _interpolate_hex(start_hex: str, end_hex: str, factor: float) -> str:
    """Interpola linealmente entre dos colores hexadecimales según un factor de 0.0 a 1.0."""
    r1, g1, b1 = _hex_to_rgb(start_hex)
    r2, g2, b2 = _hex_to_rgb(end_hex)

    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)

    # Clampeo de valores dentro del rango estándar de 8 bits [0, 255]
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return _rgb_to_hex((r, g, b))

# --------------------------------------------------------------------------- Exportación de estilos
# Ruta del repo (no de RAM): style/build.sh compila y recarga Waybar/SwayNC.
_STYLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "style")


def _export_style(p: wallpapers.Palette) -> None:
    """Escribe la paleta como SCSS compartido (en RAM, igual que antes con Eww) y
    dispara style/build.sh, que compila ese SCSS a CSS plano para Waybar y SwayNC
    y los recarga. A diferencia de Eww (que compilaba su propio SCSS al vuelo,
    y por eso alcanzaba con 'eww update'), Waybar y SwayNC solo leen CSS ya
    compilado -- este paso explícito de compilación es necesario para los dos.
    """
    try:
        ram_dir = "/dev/shm/qtile_overview"
        os.makedirs(ram_dir, exist_ok=True)

        variables_path = os.path.join(ram_dir, "_variables.scss")
        transition_ms = round(THEME_TRANSITION_SECONDS * 1000)
        content = (
            "\n".join(f"${key}: {value};" for key, value in p.items())
            + f"\n$transition_ms: {transition_ms}ms;\n"
        )

        # Si el contenido es idéntico al existente, no sobreescribir ni ejecutar build.sh
        # para evitar bucles infinitos con observadores de archivos (watchers / inotify).
        if os.path.isfile(variables_path):
            try:
                with open(variables_path, "r", encoding="utf-8") as f:
                    if f.read() == content:
                        return
            except Exception:
                pass

        with open(variables_path, "w", encoding="utf-8") as f:
            f.write(content)

        build_script = os.path.join(_STYLE_DIR, "build.sh")
        if os.path.isfile(build_script):
            subprocess.Popen(
                ["bash", build_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        logger.exception("theme: no pude exportar la paleta al pipeline de estilos compartido")

# --------------------------------------------------------------------------- wallpaper
def _set_wallpaper(path: str) -> None:
    """Le pide a awww-daemon (debe estar corriendo ya -- ver scripts/launch_swww.sh)
    que muestre este wallpaper, con una transición de fundido. A diferencia de
    swaybg, no hace falta lanzar un proceso nuevo y matar el viejo a mano: el
    daemon de awww ya sabe hacer la transición él mismo entre la imagen actual
    y la nueva, por eso esta función quedó mucho más chica que su versión
    anterior con swaybg.
    """
    if not shutil.which("awww"):
        if not _state["warned"]:
            logger.warning("theme: awww no esta instalado; no se cambiaran wallpapers (ver instrucciones de instalacion de awww)")
            _state["warned"] = True
        return

    try:
        subprocess.Popen(
            [
                "awww", "img", path,
                "--transition-type", "fade",
                "--transition-duration", str(THEME_TRANSITION_SECONDS),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        logger.exception("theme: no pude pedirle a awww que cambie el wallpaper")


# --------------------------------------------------------------------------- colores en caliente & animación
def _recolor_widget(w: Any, p: wallpapers.Palette) -> None:
    name = type(w).__name__
    if name == "GroupBox":
        w.active = p["text"]
        w.inactive = p["text_dim"]
        w.this_current_screen_border = p["accent"]
        w.this_screen_border = p["border_normal"]
        w.other_screen_border = p["accent2"]
        w.highlight_color = [p["bg_alt"], p["border_normal"]]
        w.background = p["bg_alt"]
    else:
        color = p["accent2"] if name == "Clock" else p["text"]
        if hasattr(w, "foreground"):
            w.foreground = color
        layout = getattr(w, "layout", None)  # los widgets de texto guardan el color aqui
        if layout is not None and hasattr(layout, "colour"):
            layout.colour = color
    w.draw()


def _apply_layout_palette_step(p_step: dict[str, str]) -> None:
    """Aplica un estado puntual de color (estático o interpolado) a los layouts activos."""
    if qtile is None:
        return

    # Actualizar layouts de todos los grupos
    for group in qtile.groups:
        for lay in [*group.layouts, group.floating_layout]:
            for attr, key in _LAYOUT_ATTRS:
                if hasattr(lay, attr) and key in p_step:
                    setattr(lay, attr, p_step[key])

    # Re-renderizar bordes de las ventanas en pantalla
    for screen in qtile.screens:
        try:
            screen.group.layout_all(focus=False)
        except Exception:
            logger.exception("theme: no pude repintar bordes")


def _animate_borders(old_p: wallpapers.Palette, new_p: wallpapers.Palette, step: int = 1, total_steps: Optional[int] = None) -> None:
    """Anima suavemente la transición de color de bordes mediante fotogramas interpolados.

    La duración total sale de THEME_TRANSITION_SECONDS (un solo lugar para ajustarla),
    dividida en fotogramas de _ANIM_FRAME_INTERVAL segundos cada uno.
    """
    global _border_anim_timer
    if qtile is None:
        return

    if total_steps is None:
        total_steps = max(1, round(THEME_TRANSITION_SECONDS / _ANIM_FRAME_INTERVAL))

    factor = step / total_steps
    step_palette: dict[str, str] = {}

    for key in ("accent", "border_normal", "accent2"):
        if key in old_p and key in new_p:
            step_palette[key] = _interpolate_hex(old_p[key], new_p[key], factor)
        elif key in new_p:
            step_palette[key] = new_p[key]

    _apply_layout_palette_step(step_palette)

    if step < total_steps:
        _border_anim_timer = qtile.call_later(
            _ANIM_FRAME_INTERVAL,
            _animate_borders,
            old_p,
            new_p,
            step + 1,
            total_steps,
        )


def _apply_palette(p: wallpapers.Palette) -> None:
    if qtile is None:
        return

    global _border_anim_timer

    # Cancelar animación previa si aún estaba corriendo
    if _border_anim_timer is not None:
        try:
            _border_anim_timer.cancel()
        except Exception:
            pass
        _border_anim_timer = None

    old_palette = _state["palette"]

    # Si ya existía una paleta previa, animamos los bordes; de lo contrario, aplicamos directo
    if old_palette is not None:
        _animate_borders(old_palette, p)
    else:
        _apply_layout_palette_step(cast(dict[str, str], p))

    # Actualizar fondos de barra y widgets de la barra nativa (si existe).
    # NOTA: desde que Eww reserva espacio en la pantalla vía layer-shell, Qtile puede
    # poblar screen.top/bottom/... con un bar.Gap (para llevar la cuenta del espacio
    # reservado) en vez de dejarlo en None. Un Gap no tiene .widgets -- solo se procesa
    # acá si de verdad es una Bar con widgets (la barra nativa, si en algún momento
    # se vuelve a usar en paralelo a Eww).
    for screen in qtile.screens:
        for b in (screen.top, screen.bottom, screen.left, screen.right):
            if b is None or not hasattr(b, "widgets"):
                continue
            b.background = p["bg"]
            for w in b.widgets:
                try:
                    _recolor_widget(w, p)
                except Exception:
                    logger.exception("theme: no pude recolorear %s", type(w).__name__)
            b.draw()


# --------------------------------------------------------------------------- orquestacion
def _compute_async(wp: str) -> None:
    """Calcula la paleta en un hilo y, al acabar, vuelve a aplicar el tema en el hilo de Qtile."""
    if wp in _state["computing"]:
        return
    _state["computing"].add(wp)

    def work() -> None:
        try:
            wallpapers.palette_for(wp)
        except Exception:
            logger.exception("theme: fallo calculando la paleta de %s", wp)
        finally:
            _state["computing"].discard(wp)
            try:
                if qtile is not None:
                    qtile.call_soon_threadsafe(_schedule, 0.05)
            except Exception:
                logger.exception("theme: no pude reprogramar el tema")

    threading.Thread(target=work, daemon=True).start()


def _kick_scheme(wp: str) -> None:
    """Aplica el esquema completo (terminales, plantillas) fuera del hilo de Qtile."""
    _state["gen"] += 1
    gen = _state["gen"]

    def work() -> None:
        try:
            ok = wallpapers.apply_scheme(wp, is_stale=lambda: _state["gen"] != gen)
            if not ok and _state["gen"] == gen and not _state["warned_scheme"]:
                _state["warned_scheme"] = True
                logger.warning("theme: no se aplico el esquema a las terminales "
                               "(pywal no instalado o fallo; Qtile si esta tematizado)")
        except Exception:
            logger.exception("theme: error aplicando el esquema")

    threading.Thread(target=work, daemon=True).start()


def _apply() -> None:
    global _pending
    _pending = None
    if qtile is None:
        return
    try:
        name = qtile.current_group.name
        names = [g.name for g in qtile.groups]
        wp = wallpapers.wallpaper_for_group(name, names)
        if wp and wp != _state["wallpaper"]:
            _set_wallpaper(wp)
            _state["wallpaper"] = wp

        palette: Optional[wallpapers.Palette] = None
        if wp:
            palette = wallpapers.cached_palette(wp)
            if palette is None:          # aun no calculada: no bloquear a Qtile
                _compute_async(wp)
                return
        else:
            palette = cast(wallpapers.Palette, dict(wallpapers.DEFAULT_PALETTE))

        if palette is None:
            return

        if palette != _state["palette"]:
            _apply_palette(palette)
            _state["palette"] = palette
            wallpapers.write_overview_palette(palette)
            _export_style(palette)
        if wp and wp != _state["scheme_wp"]:
            _state["scheme_wp"] = wp
            _kick_scheme(wp)
    except Exception:
        logger.exception("theme: error aplicando el tema")


def _schedule(delay: float) -> None:
    global _pending
    if qtile is None:
        return
    try:
        if _pending is not None:
            _pending.cancel()
        _pending = qtile.call_later(delay, _apply)
    except Exception:
        logger.exception("theme: no pude programar el tema")


@hook.subscribe.setgroup
def _on_setgroup() -> None:
    _schedule(_DEBOUNCE_GROUP)


def _reapply_scheme() -> None:
    global _reapply
    _reapply = None
    if _state["wallpaper"]:
        _kick_scheme(_state["wallpaper"])


@hook.subscribe.client_managed
def _on_client_managed(client: Any) -> None:
    # Una terminal NUEVA nace con sus colores por defecto (pywal solo recolorea las que ya existen).
    # Se repite el esquema cuando la ventana ya tiene su pty; el debounce agrupa varias aperturas.
    global _reapply
    if qtile is None:
        return
    try:
        if _state["scheme_wp"] is None:
            return
        if _reapply is not None:
            _reapply.cancel()
        _reapply = qtile.call_later(_DEBOUNCE_CLIENT, _reapply_scheme)
    except Exception:
        logger.exception("theme: no pude programar el re-aplicado de colores")


@hook.subscribe.startup
def _on_startup() -> None:
    # Se dispara en el arranque Y en cada reload_config (las barras son objetos nuevos):
    # hay que volver a pintar aunque la paleta no haya cambiado.
    _state["palette"] = None
    _schedule(_DEBOUNCE_START)


@hook.subscribe.startup_complete
def _on_startup_complete() -> None:
    if wallpapers.wal_is_pywal16() is False:
        logger.warning("theme: el 'wal' instalado parece ser el pywal original (abandonado), "
                       "no pywal16. Instala python-pywal16 y desinstala pywal para evitar bugs "
                       "de esa version sin mantenimiento.")
    if wallpapers.ensure_cache_symlink() == "existe-en-disco":
        logger.warning("theme: ~/.cache/wal es un directorio real en DISCO (uso anterior de pywal). "
                       "Para usar la RAM: mv ~/.cache/wal ~/.cache/wal.bak")
    threading.Thread(target=wallpapers.warm_cache, daemon=True).start()
    _schedule(_DEBOUNCE_START)
