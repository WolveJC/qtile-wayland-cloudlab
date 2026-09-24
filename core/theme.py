# ~/.config/qtile/core/theme.py
"""Tema dinamico: cada grupo tiene su wallpaper y los colores salen de ese wallpaper.

Al cambiar de grupo (hook `setgroup`):
  1. pone el wallpaper del grupo (swaybg nuevo -> se mata el viejo: sin parpadeo),
  2. recolorea en caliente bordes de layouts, barra y widgets (sin reload_config),
  3. en un hilo aparte, aplica el esquema (pywal + capa de contraste) al resto del sistema:
     terminales abiertas, plantillas en ~/.cache/wal, hook opcional del usuario.
     Tambien se reaplica al abrirse una ventana nueva (una terminal nueva nace sin colores).

pywal tarda segundos en calcular un esquema: NUNCA se ejecuta en el hilo de Qtile. Si la paleta
del grupo aun no esta calculada, se pone el wallpaper, se calcula en un hilo y se re-aplica al acabar.

Se importa desde config.py; los hooks se registran al importar. Todo esta envuelto en
try/except: un fallo aqui NUNCA debe tumbar la config de Qtile.
"""
import os
import shutil
import signal
import subprocess
import threading
from typing import Optional, TypedDict

from libqtile import hook, qtile
from libqtile.log_utils import logger

from core import wallpapers

_DEBOUNCE_GROUP = 0.12   # cambiar de grupo rapido no lanza un swaybg por cada salto
_DEBOUNCE_START = 0.40   # dar tiempo a que la barra termine de configurarse
_DEBOUNCE_CLIENT = 1.0   # una ventana nueva necesita un instante para tener su pty
class ThemeState(TypedDict):
    wallpaper: Optional[str]                    # ultimo wallpaper puesto (para no relanzar swaybg igual)
    palette: Optional[wallpapers.Palette]        # ultima paleta aplicada a la barra/bordes
    proc: Optional[subprocess.Popen[bytes]]      # ultimo proceso swaybg lanzado (sin text=True: bytes)
    warned: bool                                 # ya se avisó una vez de que falta swaybg
    scheme_wp: Optional[str]                     # wallpaper cuyo esquema ya se mando a aplicar
    gen: int                                     # generacion actual (invalida aplicaciones obsoletas)
    computing: set[str]                          # wallpapers cuya paleta se esta calculando ahora
    warned_scheme: bool                          # ya se avisó una vez de que pywal no aplico el esquema


_pending = None
_reapply = None
_state: ThemeState = {"wallpaper": None, "palette": None, "proc": None, "warned": False,
                       "scheme_wp": None, "gen": 0, "computing": set(), "warned_scheme": False}

# (atributo del layout, clave de la paleta)
_LAYOUT_ATTRS = (
    ("border_focus", "accent"),
    ("border_normal", "border_normal"),
    ("border_focus_stack", "accent"),
    ("border_normal_stack", "border_normal"),
)


# --------------------------------------------------------------------------- wallpaper
def _swaybg_pids():
    try:
        out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "swaybg"],
                             capture_output=True, text=True, timeout=5).stdout
        return [int(p) for p in out.split()]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def _set_wallpaper(path):
    if not shutil.which("swaybg"):
        if not _state["warned"]:
            logger.warning("theme: swaybg no esta instalado; no se cambiaran wallpapers (pacman -S swaybg)")
            _state["warned"] = True
        return
    old = _swaybg_pids()
    prev = _state["proc"]
    try:
        new = subprocess.Popen(["swaybg", "-i", path, "-m", "fill"], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    except OSError:
        logger.exception("theme: no pude lanzar swaybg")
        return
    _state["proc"] = new

    def _kill_old():
        for pid in old:
            if pid != new.pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
        if prev is not None:  # cosechar el proceso hijo para que no quede zombi
            threading.Thread(target=prev.wait, daemon=True).start()

    qtile.call_later(0.4, _kill_old)


# --------------------------------------------------------------------------- colores en caliente
def _recolor_widget(w, p):
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


def _apply_palette(p):
    # Layouts (y capa flotante) de TODOS los grupos: al mostrarlos ya usan el color nuevo.
    for group in qtile.groups:
        for lay in [*group.layouts, group.floating_layout]:
            for attr, key in _LAYOUT_ATTRS:
                if hasattr(lay, attr):
                    setattr(lay, attr, p[key])
    # Repintar bordes de lo que se ve ahora.
    for screen in qtile.screens:
        try:
            screen.group.layout_all(focus=False)
        except Exception:
            logger.exception("theme: no pude repintar bordes")
    # Barras.
    for screen in qtile.screens:
        for b in (screen.top, screen.bottom, screen.left, screen.right):
            if b is None:
                continue
            b.background = p["bg"]
            for w in b.widgets:
                try:
                    _recolor_widget(w, p)
                except Exception:
                    logger.exception("theme: no pude recolorear %s", type(w).__name__)
            b.draw()


# --------------------------------------------------------------------------- orquestacion
def _compute_async(wp):
    """Calcula la paleta en un hilo y, al acabar, vuelve a aplicar el tema en el hilo de Qtile."""
    if wp in _state["computing"]:
        return
    _state["computing"].add(wp)

    def work():
        try:
            wallpapers.palette_for(wp)
        except Exception:
            logger.exception("theme: fallo calculando la paleta de %s", wp)
        finally:
            _state["computing"].discard(wp)
            try:
                qtile.call_soon_threadsafe(_schedule, 0.05)
            except Exception:
                logger.exception("theme: no pude reprogramar el tema")

    threading.Thread(target=work, daemon=True).start()


def _kick_scheme(wp):
    """Aplica el esquema completo (terminales, plantillas) fuera del hilo de Qtile."""
    _state["gen"] += 1
    gen = _state["gen"]

    def work():
        try:
            ok = wallpapers.apply_scheme(wp, is_stale=lambda: _state["gen"] != gen)
            if not ok and _state["gen"] == gen and not _state["warned_scheme"]:
                _state["warned_scheme"] = True
                logger.warning("theme: no se aplico el esquema a las terminales "
                               "(pywal no instalado o fallo; Qtile si esta tematizado)")
        except Exception:
            logger.exception("theme: error aplicando el esquema")

    threading.Thread(target=work, daemon=True).start()


def _apply():
    global _pending
    _pending = None
    try:
        name = qtile.current_group.name
        names = [g.name for g in qtile.groups]
        wp = wallpapers.wallpaper_for_group(name, names)
        if wp and wp != _state["wallpaper"]:
            _set_wallpaper(wp)
            _state["wallpaper"] = wp

        if wp:
            palette = wallpapers.cached_palette(wp)
            if palette is None:          # aun no calculada: no bloquear a Qtile
                _compute_async(wp)
                return
        else:
            palette = dict(wallpapers.DEFAULT_PALETTE)

        if palette != _state["palette"]:
            _apply_palette(palette)
            _state["palette"] = palette
            wallpapers.write_overview_palette(palette)
        if wp and wp != _state["scheme_wp"]:
            _state["scheme_wp"] = wp
            _kick_scheme(wp)
    except Exception:
        logger.exception("theme: error aplicando el tema")


def _schedule(delay):
    global _pending
    try:
        if _pending is not None:
            _pending.cancel()
        _pending = qtile.call_later(delay, _apply)
    except Exception:
        logger.exception("theme: no pude programar el tema")


@hook.subscribe.setgroup
def _on_setgroup():
    _schedule(_DEBOUNCE_GROUP)


def _reapply_scheme():
    global _reapply
    _reapply = None
    if _state["wallpaper"]:
        _kick_scheme(_state["wallpaper"])


@hook.subscribe.client_managed
def _on_client_managed(client):
    # Una terminal NUEVA nace con sus colores por defecto (pywal solo recolorea las que ya existen).
    # Se repite el esquema cuando la ventana ya tiene su pty; el debounce agrupa varias aperturas.
    global _reapply
    try:
        if _state["scheme_wp"] is None:
            return
        if _reapply is not None:
            _reapply.cancel()
        _reapply = qtile.call_later(_DEBOUNCE_CLIENT, _reapply_scheme)
    except Exception:
        logger.exception("theme: no pude programar el re-aplicado de colores")


@hook.subscribe.startup
def _on_startup():
    # Se dispara en el arranque Y en cada reload_config (las barras son objetos nuevos):
    # hay que volver a pintar aunque la paleta no haya cambiado.
    _state["palette"] = None
    _schedule(_DEBOUNCE_START)


@hook.subscribe.startup_complete
def _on_startup_complete():
    if wallpapers.wal_is_pywal16() is False:
        logger.warning("theme: el 'wal' instalado parece ser el pywal original (abandonado), "
                       "no pywal16. Instala python-pywal16 y desinstala pywal para evitar bugs "
                       "de esa version sin mantenimiento.")
    if wallpapers.ensure_cache_symlink() == "existe-en-disco":
        logger.warning("theme: ~/.cache/wal es un directorio real en DISCO (uso anterior de pywal). "
                       "Para usar la RAM: mv ~/.cache/wal ~/.cache/wal.bak")
    threading.Thread(target=wallpapers.warm_cache, daemon=True).start()
    _schedule(_DEBOUNCE_START)
