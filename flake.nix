{
  description = "Entorno de desarrollo y pruebas para Qtile Wayland con Waybar, Eww y Hyprlock";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # Python y librerías base de Qtile / Wayland
          python3
          python3Packages.qtile
          python3Packages.pywayland
          python3Packages.cffi
          python3Packages.cairocffi
          python3Packages.websockify
          python3Packages.pywal
          python3Packages.pyside6  # Vital para overview.py
          procps
          fontconfig

          # Componentes de Wayland, Display Headless y Compositor
          wlroots
          wayland
          wayland-utils
          xwayland

          # Barras, Widgets, Fondos y Bloqueo
          waybar
          eww
          sass      # style/build.sh compila waybar.scss y swaync.scss
          awww      # Gestor de fondos en Wayland (core/theme.py llama a `awww img`)
          hyprlock  # Pantalla de bloqueo (hoy desactivada en autostart.sh)
          swayidle

          # Notificaciones y Portapapeles
          swaync
          libnotify  # notify-send (lo usa clutch.py)
          wl-clipboard
          cliphist

          # Utilidades que invocan los scripts de scripts/ y core/
          jq
          imagemagick  # `convert`/`magick`: fallback de wallpapers.py si falla pywal

          # Lanzadores y Estética
          rofi
          papirus-icon-theme
          nerd-fonts.jetbrains-mono

          # Transmisión, VNC y Utilidades de Red/Terminal
          wayvnc
          novnc
          seatd
          kitty
          fish
          mesa

          # OPCIONALES: solo para los widgets de eww (scripts/eww/*.sh). En un
          # contenedor sin audio/red/bluetooth reales no aportan nada.
          # pulseaudio      # pactl
          # pamixer
          # networkmanager  # nmcli
          # bluez           # bluetoothctl
        ];

        shellHook = ''
          # Perfil que leen config.py, core/keys.py y autostart.sh
          export QTILE_PROFILE=vnc

          # Servidor headless y backend de renderizado
          export WLR_RENDERER=pixman
          export WLR_BACKENDS=headless
          export XDG_RUNTIME_DIR=/tmp/runtime-nix
          mkdir -p $XDG_RUNTIME_DIR
          chmod 0700 $XDG_RUNTIME_DIR
          export LANG=C.UTF-8
          export LC_ALL=C.UTF-8

          # Para que PySide6 (Qt6) use Wayland en el entorno headless
          export QT_QPA_PLATFORM=wayland
          export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

          # venv del proyecto (core/keys.py lo usa para lanzar overview.py).
          # --system-site-packages: sin esto el venv NO ve el PySide6 de Nix
          # y overview.py falla con ModuleNotFoundError.
          if [ ! -d "venv" ]; then
              echo "Creando entorno virtual Python (venv)..."
              python3 -m venv --system-site-packages venv
          fi
          source venv/bin/activate

          echo "=========================================================="
          echo " Entorno Nix Flake activo para Qtile Wayland (Waybar + Eww)."
          echo "=========================================================="
        '';
      };
    };
}
