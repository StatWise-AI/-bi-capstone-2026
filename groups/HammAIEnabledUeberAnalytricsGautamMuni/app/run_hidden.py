"""
run_hidden.py
================================================================================
OPTIONAL fallback script. Not required if you use launcher.py / the built
UberDashboardLauncher.exe -- those already start Flask hidden on their own.

This is a minimal, GUI-less alternative for anyone who just wants a single
double-clickable file that starts the dashboard completely silently (no CMD
window, no launcher window either) without needing CustomTkinter installed.

USAGE
--------------------------------------------------------------------------
Double-click this file after renaming/copying it to "run_hidden.pyw" and
Windows will run it with pythonw.exe, which has no console at all.

Alternatively, from the project folder:
    pythonw run_hidden.py

WHAT IT DOES
--------------------------------------------------------------------------
  1. Checks if the dashboard is already running on the configured port.
     If it is, THIS SCRIPT opens the browser itself (nothing else will)
     and exits.
  2. If not, starts app.py completely hidden (CREATE_NO_WINDOW). app.py
     opens the browser itself ~1 second after it starts serving (see the
     Timer(1.0, _open_browser, ...) call at the bottom of app.py), so this
     script does NOT open the browser a second time in this path -- it
     just waits so it can log success/failure. This keeps browser-opening
     to exactly one call per run: app.py on a fresh start, or this script
     when Flask was already running.
  3. Waits until the server responds (fresh-start path only).
  4. Exits immediately (Flask keeps running in the background; use Task
     Manager, or launcher.py's "Stop Dashboard" button, to stop it later).

Same safety fix as launcher.py: this script resolves its own real folder
correctly even if it is ever frozen with PyInstaller, and it will NEVER
use its own executable as the "python interpreter" to start app.py.
================================================================================
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    THIS_EXE = Path(sys.executable).resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent
    THIS_EXE = Path(sys.executable).resolve()

VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
APP_ENTRY = BASE_DIR / "app.py"
PID_FILE = BASE_DIR / ".dashboard.pid"
LOG_FILE = BASE_DIR / "dashboard_launcher.log"

HOST, PORT = "127.0.0.1", 5000
try:
    sys.path.insert(0, str(BASE_DIR))
    from config import Config
    HOST = getattr(Config, "HOST", HOST)
    PORT = getattr(Config, "PORT", PORT)
except Exception:
    pass

DASHBOARD_URL = f"http://{HOST}:{PORT}/"
CREATE_NO_WINDOW = 0x08000000


def is_server_up(timeout: float = 0.6) -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_server(timeout: float = 45.0, interval: float = 0.4) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_server_up():
            return True
        time.sleep(interval)
    return False


def resolve_python_exe():
    """Never returns this script's/executable's own path -- see launcher.py."""
    if VENV_PYTHON.exists():
        candidate = VENV_PYTHON.resolve()
        if candidate != THIS_EXE:
            return str(candidate)

    system_python = shutil.which("python")
    if system_python:
        candidate = Path(system_python).resolve()
        if candidate != THIS_EXE and candidate.name.lower() != "uberdashboardlauncher.exe":
            return str(candidate)

    return None


def main():
    # Already running -> we are the only thing that will ever open a tab
    # for this launch, so do it here, exactly once.
    if is_server_up():
        webbrowser.open(DASHBOARD_URL)
        return

    python_exe = resolve_python_exe()
    if python_exe is None:
        # No GUI here to show an error in -- write it to the log so it's
        # discoverable, and exit quietly rather than risk relaunching self.
        with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as log_handle:
            log_handle.write(
                f"\n--- run_hidden FAILED at {time.strftime('%Y-%m-%d %H:%M:%S')}: "
                "no safe python interpreter found ---\n"
            )
        return

    if not APP_ENTRY.exists():
        with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as log_handle:
            log_handle.write(
                f"\n--- run_hidden FAILED at {time.strftime('%Y-%m-%d %H:%M:%S')}: "
                f"app.py not found at {APP_ENTRY} ---\n"
            )
        return

    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        creationflags = CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as log_handle:
        log_handle.write(f"\n--- run_hidden start at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        log_handle.write(f"Interpreter: {python_exe}\n")
        proc = subprocess.Popen(
            [python_exe, str(APP_ENTRY)],
            cwd=str(BASE_DIR),
            stdout=log_handle,
            stderr=log_handle,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )

    try:
        PID_FILE.write_text(str(proc.pid))
    except Exception:
        pass

    # NOTE: we deliberately do NOT call webbrowser.open() here even if the
    # server comes up. app.py opens the browser itself (Timer(1.0,
    # _open_browser, ...) at the bottom of app.py) ~1 second after it
    # starts serving. Calling webbrowser.open() again here would open a
    # second tab pointing at the same URL every time this script has to
    # start Flask from cold. We only wait so we can log success/failure.
    wait_for_server()
    # If it never came up, dashboard_launcher.log has the details -- there's
    # no GUI here to report an error into.


if __name__ == "__main__":
    if os.name == "nt":
        main()
