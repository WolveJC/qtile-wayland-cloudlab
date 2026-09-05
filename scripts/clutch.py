#!/usr/bin/env python3
# ~/.config/qtile/scripts/clutch.py

import os
import subprocess
import time

def transition_to_qtile():
    print("⚡ Iniciando secuencia de embrague hacia Qtile (Wayland)...")
    
    # 1. Apagar Plasma Shell limpiamente (Compatibilidad con Plasma 5 y 6)
    for cmd in [["kquitapp6", "plasmashell"], ["kquitapp5", "plasmashell"]]:
        try:
            subprocess.run(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except FileNotFoundError:
            pass
            
    subprocess.run(["killall", "-9", "plasmashell"], stderr=subprocess.DEVNULL)
    
    # 2. Reemplazar KWin por Qtile especificando el backend Wayland
    print("🔄 Reemplazando KWin por Qtile Wayland...")
    subprocess.Popen(["qtile", "start", "-b", "wayland", "--replace"])
    
    # 3. Lanzar Swaybg y Mako tras la transición
    time.sleep(0.8)
    subprocess.Popen(["swaybg", "-i", os.path.expanduser("~/.config/qtile/wallpapers/default.jpg"), "-m", "fill"])
    subprocess.Popen(["mako"])
    
    print("🚀 Transición completada con éxito.")

if __name__ == "__main__":
    transition_to_qtile()