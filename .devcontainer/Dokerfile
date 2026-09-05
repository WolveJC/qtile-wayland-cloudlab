# debian:testing corresponde al desarrollo de Debian 14 (Forky)
FROM debian:testing-slim

# Instalar dependencias mínimas de sistema y curl para Nix
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Configurar usuario no-root para Codespaces
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME

