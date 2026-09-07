{
  description = "Entorno de desarrollo y pruebas para Qtile Wayland";

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
          python3Packages.pyside6  # <- Vital para overview.py sin romper pip en el venv
          procps
          fontconfig

          # Componentes de Wayland, Display Headless y Compositor
          wlroots
          wayland
          wayland-utils
          xwayland
          swaybg

          # Utilidades de Entorno y Demonios (Declarados en autostart.sh)
          mako
          wl-clipboard
          cliphist

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
        ];

        shellHook = ''
          # Configuración del servidor headless y backend de renderizado
          export WLR_RENDERER=pixman
          export WLR_BACKENDS=headless
          export XDG_RUNTIME_DIR=/tmp/runtime-nix
          mkdir -p $XDG_RUNTIME_DIR
          chmod 0700 $XDG_RUNTIME_DIR
          export LANG=C.UTF-8
          export LC_ALL=C.UTF-8

          echo "Entorno Nix Flake activo para Qtile Wayland."
        '';

          # Variables críticas para que PySide6 (Qt6) reconozca Wayland en el entorno headless
          export QT_QPA_PLATFORM=wayland
          export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

          # Crear el venv automáticamente si no existe para mantener la estructura del proyecto
          if [ ! -d "venv" ]; then
              echo "Creando entorno virtual Python (venv)..."
              python3 -m venv venv
              source venv/bin/activate
              pip install --upgrade pip
              # Si necesitas aislar algo más por pip, se hará aquí, pero pyside6 ya viene de Nix
          else
              source venv/bin/activate
          fi

          echo "=========================================================="
          echo " Entorno Nix Flake activo para Qtile Wayland + PySide6."
          echo "=========================================================="
        '';
      };
    };
}