# ~/.config/qtile/core/wallpapers.py
"""Wallpaper por grupo + paleta de colores derivada del wallpaper.

Modulo puro (NO importa libqtile): lo usan core/theme.py (dentro de Qtile) y
overview/overview.py (proceso aparte).

Reglas:
  * Cada grupo usa un wallpaper de la carpeta wallpapers/, en orden natural
    (wp_2 antes que wp_10). Si hay mas grupos que imagenes, se reutilizan en ciclo.
  * Opcional: wallpapers/map.json fuerza uno concreto, p. ej. {"3": "wp_1.jpg"}.

Motor de colores (pywal + capa de contraste):
  1. `wal -i imagen` genera el esquema de 16 colores en una carpeta temporal en RAM.
  2. normalize_scheme() sube el contraste de los colores que quedarian ilegibles (WCAG), sin
     cambiar su tono. Sin esto, en un wallpaper casi monocromo pywal deja colores ANSI que son
     invisibles sobre su propio fondo (ver LEEME).
  3. Del esquema corregido salen (a) la paleta de Qtile/overview y (b) todo lo demas: al aplicarlo
     con `wal -f esquema.json` pywal recolorea las terminales abiertas y renderiza sus plantillas
     (kitty, rofi, mako, fish, VS Code, y las propias de ~/.config/wal/templates/).
  * Si `wal` no esta instalado se usa el extractor anterior (Pillow/ImageMagick): Qtile sigue
    tematizado, pero no hay sincronizacion con terminales.

Todo vive en RAM (tmpfs), nunca en el disco: $XDG_RUNTIME_DIR/qtile-theme-<uid>/ (o /dev/shm).
Tras un reinicio se recalcula en un hilo de fondo (pywal tarda ~1-4 s por imagen la primera vez).
"""
import colorsys
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from typing import Any, Literal, Optional, TypedDict, cast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP_DIR = os.path.join(BASE_DIR, "wallpapers")
_RAM_BASE = os.environ.get("XDG_RUNTIME_DIR") or "/dev/shm"
if not os.path.isdir(_RAM_BASE):
    _RAM_BASE = "/dev/shm"
RAM_DIR = os.path.join(_RAM_BASE, f"qtile-theme-{os.getuid()}")
CACHE_FILE = os.path.join(RAM_DIR, "palettes.json")   # paletas + esquemas normalizados por wallpaper
WAL_CACHE_HOME = os.path.join(RAM_DIR, "xdg")          # XDG_CACHE_HOME del `wal` que aplica el tema
WAL_DIR = os.path.join(WAL_CACHE_HOME, "wal")          # aqui quedan colors.json, sequences, colors-kitty.conf...
STD_WAL_LINK = os.path.expanduser("~/.cache/wal")      # ruta estandar que esperan shells y extensiones
HOOK_SCRIPT = os.path.join(BASE_DIR, "scripts", "on_theme_change.sh")  # opcional: se ejecuta tras aplicar
OVERVIEW_PALETTE = "/dev/shm/qtile_overview/palette.json"
EXTENSIONS = (".jpg", ".jpeg", ".png")  # lo que swaybg abre sin plugins extra
ALGO_VERSION = 2  # subirlo invalida la cache si cambia el algoritmo

# Look original (Catppuccin). Se usa sin wallpapers, en grises puros o si falla la extraccion.
class Palette(TypedDict):
    """Los 7 colores que consumen Qtile (barra/bordes) y overview.py."""
    accent: str
    accent2: str
    bg: str
    bg_alt: str
    border_normal: str
    text: str
    text_dim: str


class OverviewPalette(TypedDict):
    """Las 6 claves que espera overview.py en su palette.json (ver overview_palette())."""
    border_active: str
    border_inactive: str
    bg_card_active: str
    bg_card_inactive: str
    text_color: str
    bg_overlay: str


class SchemeSpecial(TypedDict):
    background: str
    foreground: str
    cursor: str


class Scheme(TypedDict):
    """Formato colors.json de pywal: lo que produce/consume el comando `wal`."""
    special: SchemeSpecial
    colors: dict[str, str]  # claves "color0".."color15" (se accede via f-string, no literal)


Src = Literal["wal", "legacy"]
Stamp = tuple[int, int, int, str]  # (mtime_ns, size, ALGO_VERSION, motor usado)


class ComputedEntry(TypedDict):
    """Lo que devuelve _compute(): una paleta+esquema recien calculados, sin sello aun."""
    palette: Palette
    scheme: Optional[Scheme]
    src: Src


class CacheEntry(ComputedEntry):
    """ComputedEntry ya con su Stamp: la forma que se guarda en RAM y en CACHE_FILE."""
    stamp: Stamp


DEFAULT_PALETTE: Palette = {
    "accent": "#89b4fa",         # borde con foco, grupo activo
    "accent2": "#f9e2af",        # reloj, detalles
    "bg": "#181825",             # fondo de la barra
    "bg_alt": "#11111b",         # fondo de GroupBox
    "border_normal": "#1e1e2e",  # borde sin foco
    "text": "#cdd6f4",
    "text_dim": "#6c7086",
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_lock = threading.Lock()
_mem: dict[str, tuple[Stamp, CacheEntry]] = {}


# --------------------------------------------------------------------------- wallpapers
def _natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def list_wallpapers():
    """Rutas absolutas de las imagenes de wallpapers/, en orden natural."""
    try:
        names = os.listdir(WP_DIR)
    except OSError:
        return []
    files = [n for n in names if n.lower().endswith(EXTENSIONS) and not n.startswith(".")]
    files.sort(key=_natural_key)
    return [os.path.join(WP_DIR, n) for n in files]


def _overrides():
    try:
        with open(os.path.join(WP_DIR, "map.json"), encoding="utf-8") as f:
            return {str(k): str(v) for k, v in json.load(f).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def wallpaper_for_group(name, group_names):
    """Wallpaper del grupo `name` (posicion dentro de `group_names`). None si no hay imagenes."""
    wps = list_wallpapers()
    if not wps:
        return None
    forced = _overrides().get(str(name))
    if forced:
        path = os.path.join(WP_DIR, os.path.basename(forced))
        if os.path.isfile(path):
            return path
    try:
        idx = [str(g) for g in group_names].index(str(name))
    except ValueError:
        idx = 0
    return wps[idx % len(wps)]


# --------------------------------------------------------------------------- colores
def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _hex(r, g, b):
    return "#%02x%02x%02x" % (round(r), round(g), round(b))


def _from_hls(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, _clamp(l, 0, 1), _clamp(s, 0, 1))
    return _hex(r * 255, g * 255, b * 255)


def _rgb(hex_):
    return int(hex_[1:3], 16), int(hex_[3:5], 16), int(hex_[5:7], 16)


def _luminance(hex_):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """Ratio de contraste WCAG entre dos colores #rrggbb (1..21)."""
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _hue_dist(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1.0 - d)


# --------------------------------------------------------------------------- extraccion
def _clusters_pillow(path):
    """Colores dominantes [(r, g, b, peso)] con Pillow (rapido: JPEG se decodifica reducido)."""
    from PIL import Image

    with Image.open(path) as im:
        im.draft("RGB", (160, 160))
        im = im.convert("RGB")
        im.thumbnail((96, 96))
        q = im.quantize(colors=12, method=0)  # 0 = MEDIANCUT
        pal = q.getpalette() or []
        return [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2], n) for n, i in (q.getcolors() or [])]


_MAGICK_LINE = re.compile(r"^\s*(\d+):\s*\(\s*(\d+),\s*(\d+),\s*(\d+)")


def _clusters_magick(path):
    """Alternativa sin Pillow: ImageMagick (dependencia de pywal)."""
    exe = shutil.which("magick") or shutil.which("convert")
    if not exe:
        return []
    cmd = [exe, path + "[0]", "-resize", "96x96", "-colorspace", "sRGB", "-colors", "12",
           "-depth", "8", "-format", "%c", "histogram:info:-"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    res = []
    for line in out.splitlines():
        m = _MAGICK_LINE.match(line)
        if m:
            n, r, g, b = (int(x) for x in m.groups())
            res.append((r, g, b, n))
    return res


def _clusters(path):
    for fn in (_clusters_pillow, _clusters_magick):
        try:
            found = fn(path)
            if found:
                return found
        except Exception:
            continue
    return []


def build_palette(clusters) -> Palette:
    """Deriva una paleta oscura y legible a partir de los colores dominantes."""
    total = sum(c[3] for c in clusters) or 1
    items = []
    for r, g, b, n in clusters:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        _, l, s_hls = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        items.append({"h": h, "s": s, "v": v, "l": l, "sl": s_hls, "share": n / total})

    def vivid(it):
        return it["v"] >= 0.30 and it["s"] >= 0.20

    def score(it):
        return (it["share"] ** 0.5) * it["s"] * (0.4 + 0.6 * it["v"])

    # Acento: el color mas vistoso (no el mas grande), llevado a un rango legible sobre fondo oscuro.
    cands = sorted((i for i in items if vivid(i)), key=score, reverse=True)
    if cands:
        a = cands[0]
        a_h, a_l, a_s = a["h"], _clamp(a["l"], 0.60, 0.72), _clamp(a["sl"], 0.50, 0.90)
    else:  # wallpaper casi gris: conservar el azul de siempre
        a_h, a_l, a_s = colorsys.rgb_to_hls(*(c / 255 for c in _rgb(DEFAULT_PALETTE["accent"])))[0], 0.72, 0.90

    # Segundo acento: otro tono claramente distinto Y vistoso (evita que un gris verdoso cualquiera
    # se cuele como "color"); si no hay, una version mas clara del propio acento (siempre armonica).
    others = [i for i in cands[1:] if _hue_dist(i["h"], a_h) >= 0.10 and i["s"] >= 0.30]
    if others:
        b = others[0]
        b_h, b_l, b_s = b["h"], _clamp(b["l"], 0.66, 0.78), _clamp(b["sl"], 0.50, 0.90)
    else:
        b_h, b_l, b_s = a_h, 0.80, _clamp(a_s * 0.75, 0.40, 0.70)

    # Base (fondos): el color dominante con algo de tono; si no, el del acento.
    tinted = [i for i in items if i["s"] >= 0.10 and i["v"] >= 0.15]
    if tinted:
        base = max(tinted, key=lambda i: i["share"])
        base_h, base_s = base["h"], _clamp(base["s"] * 0.5, 0.12, 0.38)
    else:
        base_h, base_s = a_h, 0.15

    return {
        "accent": _from_hls(a_h, a_l, a_s),
        "accent2": _from_hls(b_h, b_l, b_s),
        "bg": _from_hls(base_h, 0.085, base_s),
        "bg_alt": _from_hls(base_h, 0.055, base_s),
        "border_normal": _from_hls(base_h, 0.16, base_s * 0.9),
        "text": _from_hls(base_h, 0.88, 0.25),
        "text_dim": _from_hls(base_h, 0.48, 0.12),
    }


# --------------------------------------------------------------------------- cache
# --------------------------------------------------------------------------- capa de contraste
# Minimos WCAG sobre el fondo del esquema (los colores mas oscuros se aclaran conservando su tono).
MIN_TEXT = 7.0     # texto, color7, cursor
MIN_COLOR = 4.5    # colores ANSI 1-6 y 9-14 (lo que usan ls, git, resaltado de sintaxis...)
MIN_MUTED = 4.0    # color8 ("negro brillante": comentarios, autosugerencias)
BRIGHT_STEP = 0.08  # pywal repite los colores normales como "brillantes"; aqui se aclaran un poco
MONO_HUE_SPREAD = 45 / 360  # si color1-6 caben en un arco mas estrecho que esto, se consideran "el mismo color"


def ensure_contrast(color, bg, minimum):
    """`color` (#rrggbb) aclarado, sin cambiar su tono, hasta alcanzar `minimum`:1 contra `bg`."""
    if contrast(color, bg) >= minimum:
        return color
    r, g, b = _rgb(color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    for step in range(1, 100):
        cand = _from_hls(h, min(1.0, l + step * 0.01), s)
        if contrast(cand, bg) >= minimum:
            return cand
    return _from_hls(h, 1.0, s)


def _lighten(color, amount):
    r, g, b = _rgb(color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return _from_hls(h, min(1.0, l + amount), s)


def _valid_scheme(s: Any) -> bool:
    try:
        sp, co = s["special"], s["colors"]
        return (all(_HEX.match(sp[k]) for k in ("background", "foreground", "cursor"))
                and all(_HEX.match(co[f"color{i}"]) for i in range(16)))
    except (KeyError, TypeError):
        return False


def normalize_scheme(raw: Scheme) -> Scheme:
    """Devuelve una copia del esquema de pywal (formato colors.json) con todo legible."""
    s = cast(Scheme, json.loads(json.dumps(raw)))  # copia profunda; json.loads devuelve Any
    sp, co = s["special"], s["colors"]

    bg = sp["background"]
    h, l, sat = colorsys.rgb_to_hls(*(c / 255 for c in _rgb(bg)))
    if l > 0.14:  # el fondo siempre oscuro
        bg = _from_hls(h, 0.12, sat)
    sp["background"] = co["color0"] = bg

    sp["foreground"] = ensure_contrast(sp["foreground"], bg, MIN_TEXT)
    sp["cursor"] = ensure_contrast(sp.get("cursor", sp["foreground"]), bg, MIN_TEXT)
    for i in range(1, 7):
        co[f"color{i}"] = ensure_contrast(co[f"color{i}"], bg, MIN_COLOR)
    co["color7"] = ensure_contrast(co["color7"], bg, MIN_TEXT)
    co["color8"] = ensure_contrast(co["color8"], bg, MIN_MUTED)
    for i in range(9, 15):
        co[f"color{i}"] = ensure_contrast(_lighten(co[f"color{i - 8}"], BRIGHT_STEP), bg, MIN_COLOR)
    co["color15"] = ensure_contrast(co["color15"], bg, MIN_TEXT + 2)
    return s


def spread_hues_for_terminal(norm: Scheme) -> Scheme:
    """Copia de `norm` para PINTAR TERMINALES: si color1-6 son casi el mismo tono (wallpaper
    monocromo, p. ej. un fondo todo en rojos), los reparte cada 60 grados en la rueda ANSI
    (rojo/amarillo/verde/cian/azul/magenta), ancladas al tono real del wallpaper (color1 no se
    mueve). Sin esto son legibles pero indistinguibles entre si: en un `git diff` la linea
    borrada y la añadida se verian del mismo color, solo distinguibles por el signo +/-.

    La barra y los bordes de Qtile NO usan este resultado (siguen el tono autentico del
    wallpaper via palette_from_scheme sobre el esquema original): esto es solo para que el
    texto de una terminal sea legible."""
    hues = []
    for i in range(1, 7):
        r, g, b = _rgb(norm["colors"][f"color{i}"])
        hues.append(colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0])
    pairs = [(a, b) for i, a in enumerate(hues) for b in hues[i + 1:]]
    if max((_hue_dist(a, b) for a, b in pairs), default=0) >= MONO_HUE_SPREAD:
        return norm  # ya hay variedad de tono: no tocar

    out = cast(Scheme, json.loads(json.dumps(norm)))  # copia profunda; json.loads devuelve Any
    bg = out["special"]["background"]
    anchor_h = hues[0]
    offsets = (0, 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6)  # rojo, amarillo, verde, cian, azul, magenta
    for i in range(1, 7):
        r, g, b = _rgb(norm["colors"][f"color{i}"])
        _, sv, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h_new = (anchor_h + offsets[i - 1]) % 1.0
        nr, ng, nb = colorsys.hsv_to_rgb(h_new, max(sv, 0.45), v)
        out["colors"][f"color{i}"] = ensure_contrast(_hex(nr * 255, ng * 255, nb * 255), bg, MIN_COLOR)
    for i in range(9, 15):
        base = out["colors"][f"color{i - 8}"]
        out["colors"][f"color{i}"] = ensure_contrast(_lighten(base, BRIGHT_STEP), bg, MIN_COLOR)
    return out


def palette_from_scheme(s: Scheme) -> Palette:
    """Las 7 claves de color que usan la barra, los bordes y el overview, a partir del esquema."""
    sp, co = s["special"], s["colors"]
    bg_h, _, bg_sat = colorsys.rgb_to_hls(*(c / 255 for c in _rgb(sp["background"])))
    base_s = _clamp(bg_sat * 0.6, 0.12, 0.38)

    items = []
    for i in range(1, 7):
        c = co[f"color{i}"]
        h, sv, v = colorsys.rgb_to_hsv(*(x / 255 for x in _rgb(c)))
        _, l, sl = colorsys.rgb_to_hls(*(x / 255 for x in _rgb(c)))
        items.append({"h": h, "sv": sv, "v": v, "l": l, "sl": sl})
    vivid = sorted((it for it in items if it["sv"] >= 0.20), key=lambda it: it["sv"] * it["v"], reverse=True)

    if vivid:
        a = vivid[0]
        a_h, a_l, a_s = a["h"], _clamp(a["l"], 0.58, 0.72), _clamp(a["sl"], 0.50, 0.90)
    else:  # esquema casi gris: conservar el azul de siempre
        a_h = colorsys.rgb_to_hls(*(c / 255 for c in _rgb(DEFAULT_PALETTE["accent"])))[0]
        a_l, a_s = 0.72, 0.90

    others = [it for it in vivid[1:] if _hue_dist(it["h"], a_h) >= 0.10 and it["sv"] >= 0.30]
    if others:
        b = others[0]
        b_h, b_l, b_s = b["h"], _clamp(b["l"], 0.66, 0.78), _clamp(b["sl"], 0.50, 0.90)
    else:  # no hay un segundo color real: una version mas clara del acento (siempre armonica)
        b_h, b_l, b_s = a_h, 0.80, _clamp(a_s * 0.75, 0.40, 0.70)

    bar_bg = _from_hls(bg_h, 0.085, base_s)
    accent = ensure_contrast(_from_hls(a_h, a_l, a_s), bar_bg, MIN_COLOR)
    accent2 = ensure_contrast(_from_hls(b_h, b_l, b_s), bar_bg, MIN_COLOR)
    return {
        "accent": accent,
        "accent2": accent2,
        "bg": bar_bg,
        "bg_alt": _from_hls(bg_h, 0.055, base_s),
        "border_normal": _from_hls(bg_h, 0.16, base_s * 0.9),
        "text": ensure_contrast(sp["foreground"], bar_bg, MIN_TEXT),
        "text_dim": _from_hls(bg_h, 0.48, 0.12),
    }


# --------------------------------------------------------------------------- pywal
def _wal_exe():
    return shutil.which("wal")


_backend_cache: dict[str, Optional[bool]] = {}


def wal_is_pywal16():
    """True si el `wal` instalado es pywal16 (soporta --cols16); False si es el pywal original
    (abandonado); None si no hay `wal`. Se cachea: un solo `wal -h` por sesion."""
    exe = _wal_exe()
    if not exe:
        return None
    if exe not in _backend_cache:
        try:
            out = subprocess.run([exe, "-h"], capture_output=True, text=True, timeout=10).stdout
            _backend_cache[exe] = "--cols16" in out
        except (OSError, subprocess.SubprocessError):
            _backend_cache[exe] = None
    return _backend_cache[exe]


def _raw_scheme(path: str) -> Optional[Scheme]:
    """Esquema de 16 colores que pywal saca del wallpaper (sin normalizar). None si falla."""
    exe = _wal_exe()
    if not exe:
        return None
    os.makedirs(RAM_DIR, mode=0o700, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="raw-", dir=RAM_DIR)   # carpeta propia: llamadas en paralelo no chocan
    try:
        env = dict(os.environ, XDG_CACHE_HOME=scratch)
        subprocess.run([exe, "-i", path, "-n", "-q", "-s", "-t", "-e"], env=env,
                       capture_output=True, timeout=180, check=True)
        with open(os.path.join(scratch, "wal", "colors.json"), encoding="utf-8") as f:
            return cast(Scheme, json.load(f))  # json.load devuelve Any; se valida justo despues con _valid_scheme
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


# --------------------------------------------------------------------------- cache (RAM)
def _valid(p: Any) -> bool:
    return isinstance(p, dict) and all(isinstance(p.get(k), str) and _HEX.match(p[k]) for k in DEFAULT_PALETTE)


def _load_cache() -> dict[str, Any]:
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic_write(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


_path_locks: dict[str, threading.Lock] = {}


def _path_lock(path: str) -> threading.Lock:
    with _lock:
        return _path_locks.setdefault(path, threading.Lock())


def _stamp(path: str) -> Stamp:
    st = os.stat(path)
    # El motor entra en la marca: si instalas pywal despues, la paleta se recalcula con el motor bueno.
    return (st.st_mtime_ns, st.st_size, ALGO_VERSION, "wal" if _wal_exe() else "legacy")


def _lookup(path: str, stamp: Stamp) -> Optional[CacheEntry]:
    with _lock:
        hit = _mem.get(path)
        if hit and hit[0] == stamp:
            return hit[1]
        d = _load_cache().get(path)
        # Lo leido de CACHE_FILE viene de JSON: su "stamp" es una list, nunca una tuple.
        if (isinstance(d, dict) and tuple(d.get("stamp", [])) == stamp and _valid(d.get("palette"))
                and (d.get("scheme") is None or _valid_scheme(d["scheme"]))):
            # isinstance(d, dict) solo estrecha a dict[Any, Any]: la forma exacta de CacheEntry
            # ya quedo verificada en runtime justo arriba (stamp, palette, scheme), asi que el
            # cast aqui documenta algo ya comprobado, no lo da por hecho a ciegas.
            valid_entry = cast(CacheEntry, d)
            _mem[path] = (stamp, valid_entry)
            return valid_entry
    return None


def _store(path: str, stamp: Stamp, entry: ComputedEntry) -> CacheEntry:
    full: CacheEntry = {**entry, "stamp": stamp}
    with _lock:
        _mem[path] = (stamp, full)
        try:
            cache = _load_cache()
            cache[path] = full
            _atomic_write(CACHE_FILE, cache)
        except OSError:
            pass
    return full


def _compute(path: str) -> Optional[ComputedEntry]:
    raw = _raw_scheme(path)
    if raw and _valid_scheme(raw):
        norm = normalize_scheme(raw)
        # Qtile (barra/bordes) usa el tono autentico del wallpaper (norm). Las terminales
        # usan spread_hues_for_terminal(norm): igual salvo que, si el wallpaper es casi
        # monocromo, reparte color1-6 para que sean distinguibles entre si.
        return {"palette": palette_from_scheme(norm), "scheme": spread_hues_for_terminal(norm), "src": "wal"}
    clusters = _clusters(path)  # respaldo: extractor sin pywal (solo paleta de Qtile)
    if clusters:
        return {"palette": build_palette(clusters), "scheme": None, "src": "legacy"}
    return None


def _entry(path: str, compute: bool) -> Optional[CacheEntry]:
    stamp = _stamp(path)
    hit = _lookup(path, stamp)
    if hit or not compute:
        return hit
    with _path_lock(path):          # un solo calculo por imagen aunque lo pidan dos hilos
        hit = _lookup(path, stamp)
        if hit:
            return hit
        res = _compute(path)
        return _store(path, stamp, res) if res else None


def cached_palette(path: str) -> Optional[Palette]:
    """Paleta ya calculada, o None. NUNCA calcula: es segura para el hilo principal de Qtile."""
    try:
        e = _entry(path, compute=False)
        # dict(...) sobre un TypedDict devuelve una copia (para que quien llama no pueda mutar
        # la cache), pero mypy la generaliza a dict[str, object]: se corrige con cast.
        return cast(Palette, dict(e["palette"])) if e else None
    except Exception:
        return None


def palette_for(path: str) -> Palette:
    """Paleta del wallpaper (calcula si hace falta; puede tardar segundos). Nunca lanza."""
    try:
        e = _entry(path, compute=True)
        return cast(Palette, dict(e["palette"])) if e else cast(Palette, dict(DEFAULT_PALETTE))
    except Exception:
        return cast(Palette, dict(DEFAULT_PALETTE))


def scheme_for(path: str) -> Optional[Scheme]:
    """Esquema de 16 colores normalizado (formato colors.json), o None si no hay pywal."""
    try:
        e = _entry(path, compute=True)
        return cast(Scheme, json.loads(json.dumps(e["scheme"]))) if e and e.get("scheme") else None
    except Exception:
        return None


def warm_cache():
    """Precalcula todos los esquemas (se llama en un hilo al arrancar)."""
    for wp in list_wallpapers():
        palette_for(wp)


# --------------------------------------------------------------------------- aplicar al sistema
_apply_lock = threading.Lock()


def apply_scheme(path, is_stale=None):
    """Aplica el esquema del wallpaper a todo lo que pywal sabe alimentar.

    Recolorea las terminales abiertas (secuencias de escape a cada /dev/pts/*) y renderiza las
    plantillas en WAL_DIR (kitty, rofi, mako, fish, VS Code, ~/.config/wal/templates/...).
    Si existe scripts/on_theme_change.sh se ejecuta despues (punto de extension: GTK, Qt...).
    `is_stale()` permite abandonar el trabajo si mientras tanto el usuario cambio de grupo.
    """
    exe = _wal_exe()
    scheme = scheme_for(path) if exe else None
    if not scheme:
        return False
    with _apply_lock:
        if is_stale and is_stale():
            return False
        current = os.path.join(RAM_DIR, "current-scheme.json")
        _atomic_write(current, scheme)
        cmd = [exe, "-f", current, "-n", "-q", "-t", "-e"]
        if os.path.isfile(HOOK_SCRIPT):
            cmd += ["-o", HOOK_SCRIPT]
        env = dict(os.environ, XDG_CACHE_HOME=WAL_CACHE_HOME)
        try:
            return subprocess.run(cmd, env=env, capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False


def ensure_cache_symlink():
    """~/.cache/wal -> carpeta en RAM, para que shells y extensiones usen la ruta estandar.

    Devuelve "ok", "existe-en-disco" (hay un ~/.cache/wal real de un uso anterior de pywal: no se
    toca) o "error".
    """
    link = STD_WAL_LINK
    try:
        os.makedirs(WAL_DIR, mode=0o700, exist_ok=True)
        if os.path.islink(link):
            if os.readlink(link) == WAL_DIR:
                return "ok"
            os.unlink(link)
        elif os.path.exists(link):
            return "existe-en-disco"
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(WAL_DIR, link)
        return "ok"
    except OSError:
        return "error"


# --------------------------------------------------------------------------- overview
def _rgba(hex_, alpha):
    r, g, b = _rgb(hex_)
    return f"rgba({r}, {g}, {b}, {alpha})"


def overview_palette(p: Palette) -> OverviewPalette:
    """Mismas claves que lee overview/overview.py desde palette.json."""
    return {
        "border_active": p["accent"],
        "border_inactive": "rgba(255, 255, 255, 0.15)",
        "bg_card_active": _rgba(p["bg"], 0.85),
        "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
        "text_color": p["text"],
        "bg_overlay": _rgba(p["bg_alt"], 0.6),
    }


def write_overview_palette(p: Palette) -> None:
    try:
        _atomic_write(OVERVIEW_PALETTE, overview_palette(p))
    except OSError:
        pass
