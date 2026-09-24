#!/usr/bin/env python3
# ~/.config/qtile/scripts/clutch.py
"""
clutch.py - Cambia entre sesiones KDE Plasma <-> Qtile (Wayland) automaticamente (SDDM).

Uso:
    clutch.py --install      # una sola vez: helper root + sudoers + lanzadores KDE + autostart KDE
    clutch.py qtile          # cierra la sesion actual y entra a Qtile
    clutch.py kde            # cierra la sesion actual y entra a KDE
    clutch.py toggle         # alterna segun la sesion actual
    clutch.py --clear        # borra el autologin temporal (lo llama la sesion nueva al iniciar)
    clutch.py qtile --dry-run

Todo queda registrado en ~/.local/share/qtile/clutch.log y los errores se muestran como
notificacion (asi un atajo que falla nunca lo hace en silencio).

Como funciona: escribe /etc/sddm.conf.d/zz-clutch.conf ([Autologin] + Relogin=true) apuntando
a la sesion destino, cierra la sesion actual y SDDM entra solo a la otra. La sesion nueva
ejecuta --clear para que el siguiente logout vuelva al login normal.
"""
import argparse
import datetime
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

HELPER = "/usr/local/libexec/clutch-set-session"
SUDOERS = "/etc/sudoers.d/clutch"
SESSIONS_DIRS = [Path("/usr/local/share/wayland-sessions"), Path("/usr/share/wayland-sessions")]
CANDIDATES = {
    "kde": ["plasma.desktop"],
    # qtile.desktop solo se acepta si su Exec arranca qtile directo (ver session_usable)
    "qtile": ["qtile-wayland.desktop", "qtile.desktop"],
}
LOG_FILE = Path.home() / ".local" / "share" / "qtile" / "clutch.log"
APPS_DIR = Path.home() / ".local" / "share" / "applications"
KDE_AUTOSTART = Path.home() / ".config" / "autostart" / "clutch-clear.desktop"
SELF = Path(__file__).resolve()

# Helper que corre como root (solo escribe/borra UN archivo y valida la sesion).
HELPER_SRC = r'''#!/usr/bin/env python3
import os, re, sys
from pathlib import Path

CONF = Path("/etc/sddm.conf.d/zz-clutch.conf")
SESSIONS = [Path("/usr/local/share/wayland-sessions"), Path("/usr/share/wayland-sessions")]

user = os.environ.get("SUDO_USER")
if not user or user == "root":
    sys.exit("Este helper solo se usa via sudo desde un usuario normal.")

cmd = sys.argv[1] if len(sys.argv) > 1 else ""

if cmd == "clear" and len(sys.argv) == 2:
    CONF.unlink(missing_ok=True)
    sys.exit(0)

if cmd == "set" and len(sys.argv) == 3:
    session = sys.argv[2]
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.desktop", session) or not any((d / session).is_file() for d in SESSIONS):
        sys.exit("Sesion invalida: " + session)
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text("[Autologin]\nUser=%s\nSession=%s\nRelogin=true\n" % (user, session))
    sys.exit(0)

sys.exit("uso: clutch-set-session set <sesion.desktop> | clear")
'''


# -----------------------------------------------------------------------------
# Log y notificaciones
# -----------------------------------------------------------------------------
def log(msg: str):
    line = f"{datetime.datetime.now():%F %T} {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def notify(title: str, body: str = ""):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", "-a", "clutch", title, body], check=False)


def die(msg: str):
    log("ERROR: " + msg)
    notify("Clutch: no se pudo cambiar de sesion", msg)
    sys.exit(1)


def run(cmd, check=True, **kw):
    return subprocess.run(cmd, check=check, **kw)


# -----------------------------------------------------------------------------
# Instalacion
# -----------------------------------------------------------------------------
def desktop_entry(name: str, comment: str, exec_line: str, icon: str) -> str:
    return (
        "[Desktop Entry]\nType=Application\n"
        f"Name={name}\nComment={comment}\nExec={exec_line}\nIcon={icon}\n"
        "Terminal=false\nCategories=System;\n"
    )


def install():
    tmp_helper = Path("/tmp/clutch-set-session")
    tmp_sudoers = Path("/tmp/clutch-sudoers")
    tmp_helper.write_text(HELPER_SRC)
    tmp_sudoers.write_text(f"{getpass.getuser()} ALL=(root) NOPASSWD: {HELPER} *\n")

    run(["sudo", "install", "-D", "-m", "0755", "-o", "root", "-g", "root", str(tmp_helper), HELPER])
    # Validar sudoers ANTES de instalarlo (un sudoers roto puede bloquearte sudo)
    run(["sudo", "visudo", "-cf", str(tmp_sudoers)])
    run(["sudo", "install", "-m", "0440", "-o", "root", "-g", "root", str(tmp_sudoers), SUDOERS])
    tmp_helper.unlink(missing_ok=True)
    tmp_sudoers.unlink(missing_ok=True)

    py = sys.executable
    # Lanzadores: aparecen en el menu de KDE y se les puede asignar un atajo global
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    (APPS_DIR / "clutch-qtile.desktop").write_text(
        desktop_entry("Cambiar a Qtile", "Cierra la sesion y entra a Qtile (Wayland)",
                      f"{py} {SELF} qtile", "preferences-system-windows"))
    (APPS_DIR / "clutch-kde.desktop").write_text(
        desktop_entry("Cambiar a KDE", "Cierra la sesion y entra a KDE Plasma",
                      f"{py} {SELF} kde", "plasma"))

    # Autostart en KDE para limpiar el autologin al entrar
    KDE_AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
    KDE_AUTOSTART.write_text(
        "[Desktop Entry]\nType=Application\nName=Clutch clear\n"
        f"Exec={py} {SELF} --clear\nX-KDE-autostart-phase=2\n")

    if shutil.which("kbuildsycoca6"):
        run(["kbuildsycoca6"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Instalado.")
    print("Atajo desde KDE -> Qtile:")
    print("  Configuracion del sistema > Atajos > Agregar nuevo > Aplicacion")
    print("  elige 'Cambiar a Qtile' y asignale, por ejemplo, Meta+Ctrl+Q.")
    print("Atajo desde Qtile -> KDE: ya viene en keys.py (Super+Shift+E).")


# -----------------------------------------------------------------------------
# Cambio de sesion
# -----------------------------------------------------------------------------
def session_usable(path: Path) -> bool:
    """El qtile.desktop del paquete arranca via qtile.service (units que no existen): no sirve."""
    try:
        exec_line = next((l for l in path.read_text().splitlines() if l.startswith("Exec=")), "")
    except OSError:
        return False
    return "systemctl --user start" not in exec_line


def find_session(target: str) -> str:
    for name in CANDIDATES[target]:
        for d in SESSIONS_DIRS:
            p = d / name
            if p.is_file() and session_usable(p):
                return name
    available = sorted({p.name for d in SESSIONS_DIRS if d.is_dir() for p in d.glob("*.desktop")})
    hint = " (ejecuta install-qtile-session.sh)" if target == "qtile" else ""
    die(f"No encontre una sesion usable para '{target}'{hint}. Disponibles: {available}")


def current_session() -> str:
    """Sesion REAL en la que estamos. XDG_CURRENT_DESKTOP manda (una ventana de qtile
    anidada dentro de KDE hereda KDE); pgrep es solo el ultimo recurso."""
    desk = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "kde" in desk:
        return "kde"
    if "qtile" in desk:
        return "qtile"
    if subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "qtile"],
                      capture_output=True).returncode == 0:
        return "qtile"
    return "kde"


def clear():
    if Path(HELPER).exists():
        run(["sudo", "-n", HELPER, "clear"], check=False)
        log("autologin temporal limpiado")


def logout(cur: str) -> bool:
    """Cierra la sesion actual. Devuelve True si algun metodo funciono."""
    methods = []
    if cur == "kde":
        if shutil.which("busctl"):
            methods.append(["busctl", "--user", "call", "org.kde.Shutdown", "/Shutdown",
                            "org.kde.Shutdown", "logout"])
        for q in ("qdbus6", "qdbus"):
            if shutil.which(q):
                methods.append([q, "org.kde.Shutdown", "/Shutdown", "logout"])
    else:
        if shutil.which("qtile"):
            methods.append(["qtile", "cmd-obj", "-o", "cmd", "-f", "shutdown"])
    sid = os.environ.get("XDG_SESSION_ID")
    methods.append(["loginctl", "terminate-session", sid] if sid
                   else ["loginctl", "terminate-user", getpass.getuser()])

    for cmd in methods:
        r = run(cmd, check=False, capture_output=True, text=True)
        log(f"logout via {cmd[0]}: rc={r.returncode} {r.stderr.strip()[:120]}")
        if r.returncode == 0:
            return True
    return False


def switch(target: str, dry: bool):
    cur = current_session()
    if target == "toggle":
        target = "kde" if cur == "qtile" else "qtile"
    if target == cur:
        die(f"Ya estas en {cur}. (Si hay una ventana de Qtile anidada abierta en KDE, cierrala primero.)")
    if not Path(HELPER).exists():
        die("Falta instalar el helper. Ejecuta: python3 clutch.py --install")

    session = find_session(target)
    log(f"Clutch: {cur} -> {target} (sesion SDDM: {session})")
    if dry:
        log("[dry-run] no se ejecuta nada.")
        return
    r = run(["sudo", "-n", HELPER, "set", session], check=False, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"sudo/helper fallo: {r.stderr.strip() or r.stdout.strip()} (rc={r.returncode})")
    notify(f"Cambiando a {target}...", "Cerrando la sesion actual")
    if not logout(cur):
        clear()
        die("No pude cerrar la sesion actual; revierto el autologin.")


def main():
    ap = argparse.ArgumentParser(description="Cambio automatico de sesion KDE <-> Qtile (SDDM)")
    ap.add_argument("target", nargs="?", choices=["kde", "qtile", "toggle"])
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.install:
        install()
    elif args.clear:
        clear()
    elif args.target:
        switch(args.target, args.dry_run)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
