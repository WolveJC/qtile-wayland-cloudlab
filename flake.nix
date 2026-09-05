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
          # Python y Qtile con Soporte Wayland
          python3
          python3Packages.qtile
          python3Packages.pywayland
          python3Packages.cffi
          python3Packages.cairocffi

          # Componentes de Wayland y Display Headless
          wlroots
          wayland
          wayland-utils
          xwayland

          # Lanzador de aplicaciones (Lanzador Wayland nativo)
          rofi-wayland
          papirus-icon-theme
          nerd-fonts.jetbrains-mono

          # Transmisión y VNC
          wayvnc
          novnc
          websockify
          seatd

          # Utilerías de prueba
          foot
          alacritty
          mesa
        ];

        shellHook = ''
          export WLR_RENDERER=pixman
          export WLR_BACKENDS=headless
          export XDG_RUNTIME_DIR=/tmp/runtime-nix
          mkdir -p $XDG_RUNTIME_DIR
          chmod 0700 $XDG_RUNTIME_DIR

          echo "Entorno Nix Flake activo para Qtile Wayland."
        '';
      };
    };
}

