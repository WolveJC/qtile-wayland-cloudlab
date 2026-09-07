# ~/.config/qtile/overview/overview.py
import sys
import os
import io
import json
import subprocess
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, 
                             QVBoxLayout, QLabel, QGraphicsBlurEffect)
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QRect, QEasingCurve

# --- Resolución Dinámica de Directorios ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAM_DIR = "/dev/shm/qtile_overview"
PALETTE_FILE = os.path.join(RAM_DIR, "palette.json")
WP_DIR = os.path.join(BASE_DIR, "wallpapers")

os.makedirs(RAM_DIR, exist_ok=True)


# --- Carga de Paleta Dinámica desde RAM ---
def load_color_palette() -> dict:
    """Carga los colores dinámicos desde RAM (/dev/shm). Fallback a Catppuccin si no existe."""
    default_palette = {
        "border_active": "#89b4fa",
        "border_inactive": "rgba(255, 255, 255, 0.1)",
        "bg_card_active": "rgba(49, 50, 68, 0.8)",
        "bg_card_inactive": "rgba(0, 0, 0, 0.4)",
        "text_color": "#cdd6f4",
        "bg_overlay": "rgba(15, 15, 23, 0.5)"
    }
    
    if os.path.exists(PALETTE_FILE):
        try:
            with open(PALETTE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_palette.update(data)
        except Exception as e:
            print(f"Error leyendo paleta en RAM: {e}")
            
    return default_palette


class AppIconBar(QWidget):
    """Barra inferior con iconos planos para representar apps abiertas."""
    def __init__(self, app_classes, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignLeft)

        for wm_class in app_classes[:5]:
            icon_name = self.resolve_icon_name(str(wm_class).lower())
            icon = QIcon.fromTheme(icon_name)
            
            if not icon.isNull():
                lbl = QLabel(self)
                lbl.setPixmap(icon.pixmap(QSize(18, 18)))
                layout.addWidget(lbl)

    def resolve_icon_name(self, wm_class: str) -> str:
        mapping = {
            "kitty": "utilities-terminal",
            "alacritty": "utilities-terminal",
            "firefox": "firefox",
            "chromium": "chromium",
            "google-chrome": "google-chrome",
            "code": "visual-studio-code",
            "vscodium": "vscodium",
            "spotify": "spotify",
            "thunar": "system-file-manager",
            "dolphin": "system-file-manager",
            "steam": "steam",
            "discord": "discord",
        }
        return mapping.get(wm_class, "application-x-executable")


class WorkspaceCard(QWidget):
    def __init__(self, bg_path, name, palette, app_classes=None, is_active=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.bg_path = bg_path
        self.palette = palette
        self.is_selected = False
        self.setFixedSize(280, 160)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        self.lbl_title = QLabel(f"Workspace {name}", self)
        self.lbl_title.setStyleSheet(f"color: {self.palette['text_color']}; font-weight: bold; font-size: 12px;")
        self.main_layout.addWidget(self.lbl_title)

        self.lbl_bg = QLabel(self)
        self.lbl_bg.setScaledContents(True)
        
        if os.path.exists(bg_path):
            with open(bg_path, "rb") as f:
                ram_buffer = io.BytesIO(f.read())
                image = QImage.fromData(ram_buffer.getvalue())
                self.lbl_bg.setPixmap(QPixmap.fromImage(image))
        else:
            self.lbl_bg.setText(f"Workspace {name}")
            self.lbl_bg.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(self.lbl_bg, stretch=1)

        if app_classes:
            self.icon_bar = AppIconBar(app_classes, self)
            self.main_layout.addWidget(self.icon_bar)

        self.set_selected(is_active)

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
        self.showFullScreen()

        self.palette = load_color_palette()

        # Fondo Dinámico Desenfocado
        self.lbl_full_bg = QLabel(self)
        self.lbl_full_bg.setScaledContents(True)
        self.lbl_full_bg.resize(self.size())
        self.lbl_full_bg.lower()

        self.blur_effect = QGraphicsBlurEffect(self)
        self.blur_effect.setBlurRadius(35.0)
        self.blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
        self.lbl_full_bg.setGraphicsEffect(self.blur_effect)

        # Overlay dinámico
        self.overlay = QWidget(self)
        self.overlay.resize(self.size())
        self.overlay.setStyleSheet(f"background-color: {self.palette['bg_overlay']};")
        self.overlay.lower()

        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(20)
        self.cards = []
        self.current_index = 0
        self.is_animating = False

        qtile_state = self.get_qtile_state()
        current_group = qtile_state.get("current_group", "1")
        groups_apps = qtile_state.get("groups_apps", {})

        for i in range(1, 6):
            group_name = str(i)
            # Ruta absoluta corregida utilizando el repositorio
            bg_path = os.path.join(WP_DIR, f"wp_{i}.jpg")
            
            is_active = (group_name == current_group)
            if is_active:
                self.current_index = i - 1

            apps_in_group = groups_apps.get(group_name, [])

            card = WorkspaceCard(
                bg_path=bg_path, 
                name=group_name,
                palette=self.palette,
                app_classes=apps_in_group, 
                is_active=is_active, 
                parent=self
            )
            self.cards.append(card)
            self.layout.addWidget(card)

        self.update_background()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.lbl_full_bg.resize(self.size())
        self.overlay.resize(self.size())

    def update_background(self):
        if not self.cards:
            return
            
        current_card = self.cards[self.current_index]
        bg_path = current_card.bg_path

        if os.path.exists(bg_path):
            with open(bg_path, "rb") as f:
                ram_buffer = io.BytesIO(f.read())
                image = QImage.fromData(ram_buffer.getvalue())
                self.lbl_full_bg.setPixmap(QPixmap.fromImage(image))
        else:
            self.lbl_full_bg.clear()

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
            
            # 2. Ejecutar la Sincronización Camaleón Global (theme_sync.sh)
            sync_script = os.path.join(BASE_DIR, "scripts", "theme_sync.sh")
            if os.path.exists(sync_script) and os.path.exists(card.bg_path):
                subprocess.Popen(["bash", sync_script, card.bg_path])
                
            # 3. Cerrar la interfaz libera RAM de forma inmediata
            self.close()

        self.anim.finished.connect(on_finished)
        self.anim.start()

    def get_qtile_state(self) -> dict:
        state = {"current_group": "1", "groups_apps": {}}
        try:
            res_group = subprocess.check_output(["qtile", "cmd-obj", "-o", "group", "-f", "info"])
            group_data = json.loads(res_group.decode("utf-8"))
            state["current_group"] = str(group_data.get("name", "1"))

            res_groups = subprocess.check_output(["qtile", "cmd-obj", "-o", "cmd", "-f", "get_groups"])
            all_groups = json.loads(res_groups.decode("utf-8"))

            for g_name, g_info in all_groups.items():
                state["groups_apps"][g_name] = g_info.get("windows", [])

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