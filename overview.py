
# ~/.config/qtile/overview/overview.py
"""Modo Exposicion (Super+Tab): navega los escritorios con flechas/H-L, Enter para entrar.

Todo el procesamiento de imagenes ocurre en RAM (BytesIO / QImageReader), nunca en el SSD.
Los wallpapers y la paleta de cada tarjeta se precargan una sola vez al abrir la ventana, asi
que moverse entre tarjetas con el teclado no vuelve a leer ni decodificar nada del disco.
"""
import sys
import os
import json
import subprocess
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QVBoxLayout, QLabel, QGraphicsBlurEffect)
from PySide6.QtGui import QPixmap, QImage, QImageReader, QIcon
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QRect, QEasingCurve

# --- Resolución Dinámica de Directorios ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Misma logica de wallpapers y paleta que usa Qtile (core/wallpapers.py, sin depender de libqtile)
sys.path.insert(0, BASE_DIR)
from core import wallpapers  # noqa: E402

PALETTE_FILE = wallpapers.OVERVIEW_PALETTE  # el mismo archivo que escribe core/theme.py
GROUP_NAMES = [str(n) for n in range(1, 6)]

CARD_SIZE = QSize(280, 160)

# wm_class -> nombre de icono del tema. Varias apps reportan su wm_class en minusculas y
# otras con mayusculas (xterm -class Firefox, GTK apps en minuscula, Qt en PascalCase...);
# la busqueda en resolve_icon_name ya normaliza a minusculas antes de mirar aqui.
ICON_MAP = {
    "kitty": "utilities-terminal",
    "alacritty": "utilities-terminal",
    "xterm": "utilities-terminal",
    "foot": "utilities-terminal",
    "firefox": "firefox",
    "chromium": "chromium",
    "google-chrome": "google-chrome",
    "code": "visual-studio-code",
    "vscodium": "vscodium",
    "spotify": "spotify",
    "thunar": "system-file-manager",
    "dolphin": "system-file-manager",
    "nautilus": "system-file-manager",
    "steam": "steam",
    "discord": "discord",
}


# --- Carga de Paleta Dinámica desde RAM ---
def load_color_palette() -> dict:
    """Carga los colores dinámicos desde RAM. Fallback igual al que usa Qtile si aun no existe."""
    default_palette = wallpapers.overview_palette(wallpapers.DEFAULT_PALETTE)

    if os.path.exists(PALETTE_FILE):
        try:
            with open(PALETTE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_palette.update(data)
        except Exception as e:
            print(f"Error leyendo paleta en RAM: {e}")

    return default_palette


def palette_for_wallpaper(bg_path: str) -> dict:
    """Paleta de UNA tarjeta segun su propio wallpaper (para el efecto camaleon al navegar).

    Usa solo la cache (cached_palette): nunca calcula, para no congelar el teclado si
    pywal aun no proceso esa imagen. En ese caso cae al color activo del grupo actual."""
    if bg_path:
        cached = wallpapers.cached_palette(bg_path)
        if cached:
            return wallpapers.overview_palette(cached)
    return load_color_palette()


def decode_scaled(path: str, target: QSize) -> QImage | None:
    """Decodifica una imagen YA reducida a `target` (o al tamaño que la llene, recortando
    despues), en vez de cargarla a resolucion completa: una JPEG de escritorio decodificada
    asi es varias veces mas rapida que a resolucion completa, y evita el flash de estirado
    de setScaledContents. Todo en memoria (QByteArray/QBuffer), nunca toca el disco dos veces."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None

    from PySide6.QtCore import QBuffer, QByteArray
    # QBuffer guarda internamente un PUNTERO al QByteArray, no una copia: `ba` debe seguir
    # viva (variable con nombre propio) mientras `buf`/`reader` existan, o esto segfaultea.
    ba = QByteArray(data)
    buf = QBuffer(ba)
    buf.open(QBuffer.ReadOnly)
    reader = QImageReader(buf)
    size = reader.size()
    if not size.isValid() or size.width() <= 0 or size.height() <= 0:
        image = QImage.fromData(data)
        return image if not image.isNull() else None

    # Relacion "cubrir": escala para que el lado mas corto llene `target` (se recorta despues).
    scale = max(target.width() / size.width(), target.height() / size.height())
    reader.setScaledSize(QSize(max(1, round(size.width() * scale)), max(1, round(size.height() * scale))))
    image = reader.read()
    if image.isNull():
        image = QImage.fromData(data)
    return image if not image.isNull() else None


def cover_pixmap(image: QImage, size: QSize) -> QPixmap:
    """De una imagen ya decodificada cerca del tamano final, recorta al centro para llenar
    `size` exactamente sin deformar (equivalente a `background-size: cover` en CSS)."""
    if image is None or image.isNull():
        return QPixmap()
    pm = QPixmap.fromImage(image)
    if pm.width() == 0 or pm.height() == 0:
        return pm
    scale = max(size.width() / pm.width(), size.height() / pm.height())
    if abs(scale - 1.0) > 0.01:
        pm = pm.scaled(max(1, round(pm.width() * scale)), max(1, round(pm.height() * scale)),
                        Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    x = max(0, (pm.width() - size.width()) // 2)
    y = max(0, (pm.height() - size.height()) // 2)
    return pm.copy(x, y, size.width(), size.height())


class AppIconBar(QWidget):
    """Barra inferior con iconos planos para representar apps abiertas (por wm_class real)."""
    def __init__(self, wm_classes, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignLeft)

        seen = set()
        for wm_class in wm_classes:
            icon_name = self.resolve_icon_name(wm_class)
            if icon_name in seen:  # no repetir el mismo icono 5 veces por 5 pestañas de Firefox
                continue
            seen.add(icon_name)
            icon = QIcon.fromTheme(icon_name)
            if not icon.isNull():
                lbl = QLabel(self)
                lbl.setPixmap(icon.pixmap(QSize(18, 18)))
                layout.addWidget(lbl)
            if len(seen) >= 5:
                break

    def resolve_icon_name(self, wm_class) -> str:
        # wm_class de Qtile es [instancia, clase] (p. ej. ["firefox", "Firefox"]) o None.
        # Se prueban ambos componentes, porque segun la app el nombre util viene en uno u otro.
        parts = wm_class if isinstance(wm_class, (list, tuple)) else [wm_class]
        for part in parts:
            if not part:
                continue
            key = str(part).lower().strip()
            if key in ICON_MAP:
                return ICON_MAP[key]
        return "application-x-executable"


class WorkspaceCard(QWidget):
    def __init__(self, bg_path, name, palette, wm_classes=None, is_active=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.bg_path = bg_path
        self.palette = palette
        self.is_selected = False
        self.setFixedSize(CARD_SIZE)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_title = QLabel(f"Workspace {name}", self)
        self.lbl_title.setStyleSheet(f"color: {self.palette['text_color']}; font-weight: bold; font-size: 12px;")
        self.main_layout.addWidget(self.lbl_title)

        self.lbl_bg = QLabel(self)
        # Sin setScaledContents: el pixmap ya viene recortado a medida (cover_pixmap), para
        # que el wallpaper se vea completo y sin deformar, no estirado al alto/ancho del label.
        self.main_layout.addWidget(self.lbl_bg, stretch=1)

        if wm_classes:
            self.icon_bar = AppIconBar(wm_classes, self)
            self.main_layout.addWidget(self.icon_bar)

        self.set_selected(is_active)

    def set_thumbnail(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self.lbl_bg.setPixmap(pixmap)
        else:
            self.lbl_bg.setText(f"Workspace {self.name}")
            self.lbl_bg.setAlignment(Qt.AlignCenter)

    def apply_palette(self, palette: dict):
        """Recolorea esta tarjeta con su propia paleta (efecto camaleon al enfocarla)."""
        self.palette = palette
        self.lbl_title.setStyleSheet(f"color: {palette['text_color']}; font-weight: bold; font-size: 12px;")
        self.set_selected(self.is_selected)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.setStyleSheet(f"""
                WorkspaceCard {{
                    border: 3px solid {self.palette['border_active']};
                    border-radius: 12px;
                    background: {self.palette['bg_card_active']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                WorkspaceCard {{
                    border: 2px solid {self.palette['border_inactive']};
                    border-radius: 12px;
                    background: {self.palette['bg_card_inactive']};
                }}
            """)


class OverviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.palette = load_color_palette()

        # Fondo Dinámico Desenfocado
        self.lbl_full_bg = QLabel(self)
        self.lbl_full_bg.lower()

        self.blur_effect = QGraphicsBlurEffect(self)
        self.blur_effect.setBlurRadius(35.0)
        self.blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
        self.lbl_full_bg.setGraphicsEffect(self.blur_effect)

        # Overlay dinámico
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet(f"background-color: {self.palette['bg_overlay']};")
        self.overlay.lower()

        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(20)
        self.cards = []
        self.card_palettes = []   # una paleta por tarjeta (su propio wallpaper), no la del grupo actual
        self.full_bg_cache = {}   # bg_path -> QImage a resolucion de pantalla (para el fondo difuminado)
        self.current_index = 0
        self.is_animating = False

        qtile_state = self.get_qtile_state()
        current_group = qtile_state.get("current_group", "1")
        groups_apps = qtile_state.get("groups_apps", {})

        screen_size = QApplication.primaryScreen().size() if QApplication.primaryScreen() else QSize(1920, 1080)

        for i in range(1, 6):
            group_name = str(i)
            # Mismo wallpaper que ve Qtile en ese grupo (mismo orden, mismo ciclo si faltan imagenes)
            bg_path = wallpapers.wallpaper_for_group(group_name, GROUP_NAMES) or ""

            is_active = (group_name == current_group)
            if is_active:
                self.current_index = i - 1

            card_palette = palette_for_wallpaper(bg_path)
            self.card_palettes.append(card_palette)

            card = WorkspaceCard(
                bg_path=bg_path,
                name=group_name,
                palette=card_palette,
                wm_classes=groups_apps.get(group_name, []),
                is_active=is_active,
                parent=self
            )
            # Precarga UNA vez: miniatura recortada a la medida exacta de la tarjeta.
            card.set_thumbnail(cover_pixmap(decode_scaled(bg_path, CARD_SIZE), CARD_SIZE))
            self.cards.append(card)
            self.layout.addWidget(card)

            # Precarga del fondo difuminado a resolucion de pantalla (no la del wallpaper
            # original, que puede ser mucho mayor): decodificar una sola vez por wallpaper
            # distinto (wp_1 se reutiliza en el grupo 4, por ejemplo: no se decodifica 2 veces).
            if bg_path and bg_path not in self.full_bg_cache:
                self.full_bg_cache[bg_path] = decode_scaled(bg_path, screen_size)

        self.update_background()
        # showFullScreen() dispara resizeEvent de inmediato: se llama al final, ya con
        # lbl_full_bg/overlay/cards creados (si no, revienta con AttributeError).
        self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.lbl_full_bg.resize(self.size())
        self.overlay.resize(self.size())
        self.update_background()  # el recorte "cover" depende del tamano final de la ventana

    def update_background(self):
        if not self.cards:
            return

        current_card = self.cards[self.current_index]
        image = self.full_bg_cache.get(current_card.bg_path)
        pm = cover_pixmap(image, self.size()) if image is not None else QPixmap()
        if not pm.isNull():
            self.lbl_full_bg.setPixmap(pm)
        else:
            self.lbl_full_bg.clear()

        # Efecto camaleon: los colores de la interfaz siguen al wallpaper ENFOCADO ahora,
        # no al del grupo con el que se abrio el overview.
        self.apply_chameleon(self.card_palettes[self.current_index])

    def apply_chameleon(self, palette: dict):
        self.palette = palette
        self.overlay.setStyleSheet(f"background-color: {palette['bg_overlay']};")
        self.cards[self.current_index].apply_palette(palette)

    # Animación Zoom de Entrada + Disparo de Sincronización Global
    def animate_zoom_and_exit(self, card: WorkspaceCard):
        self.is_animating = True
        card.raise_()

        start_rect = card.geometry()
        expansion = 60
        end_rect = QRect(
            start_rect.x() - (expansion // 2),
            start_rect.y() - (expansion // 2),
            start_rect.width() + expansion,
            start_rect.height() + expansion
        )

        self.anim = QPropertyAnimation(card, b"geometry")
        self.anim.setDuration(200)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_finished():
            # 1. Cambiar de Workspace en Qtile
            self.switch_qtile_group(card.name)

            # 2. (Wallpaper y colores: los aplica solo el hook `setgroup` de core/theme.py,
            #    disparado por el propio switch_qtile_group() de arriba)

            # 3. Cerrar la interfaz libera RAM de forma inmediata
            self.close()

        self.anim.finished.connect(on_finished)
        self.anim.start()

    def get_qtile_state(self) -> dict:
        """Grupo activo + apps por grupo (por wm_class real, no por titulo de ventana)."""
        state = {"current_group": "1", "groups_apps": {}}
        try:
            res_group = subprocess.check_output(["qtile", "cmd-obj", "-o", "group", "-f", "info"])
            group_data = json.loads(res_group.decode("utf-8"))
            state["current_group"] = str(group_data.get("name", "1"))

            res_windows = subprocess.check_output(["qtile", "cmd-obj", "-o", "cmd", "-f", "windows"])
            for win in json.loads(res_windows.decode("utf-8")):
                group = win.get("group")
                if not group:
                    continue
                state["groups_apps"].setdefault(str(group), []).append(win.get("wm_class"))

        except Exception as e:
            print(f"Error al leer estado IPC de Qtile: {e}")

        return state

    def switch_qtile_group(self, group_name: str):
        try:
            subprocess.Popen(["qtile", "cmd-obj", "-o", "group", group_name, "-f", "toscreen"])
        except Exception as e:
            print(f"Error al cambiar de grupo: {e}")

    def keyPressEvent(self, event):
        if self.is_animating:
            return

        key = event.key()

        if key in (Qt.Key_Left, Qt.Key_H):
            self.cards[self.current_index].set_selected(False)
            self.current_index = (self.current_index - 1) % len(self.cards)
            self.cards[self.current_index].set_selected(True)
            self.update_background()

        elif key in (Qt.Key_Right, Qt.Key_L):
            self.cards[self.current_index].set_selected(False)
            self.current_index = (self.current_index + 1) % len(self.cards)
            self.cards[self.current_index].set_selected(True)
            self.update_background()

        elif key in (Qt.Key_Return, Qt.Key_Enter):
            selected_card = self.cards[self.current_index]
            self.animate_zoom_and_exit(selected_card)

        elif key == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverviewWindow()
    window.show()
    sys.exit(app.exec())
