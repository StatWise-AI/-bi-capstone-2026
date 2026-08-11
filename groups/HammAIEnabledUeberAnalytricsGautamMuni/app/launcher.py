"""
launcher.py
================================================================================
Silent Bootstrap Launcher for the
AI-Enabled Uber India Operations Analytics Dashboard.

This is a NEW, STANDALONE file. It does not modify app.py, config.py, the
backend, Gemini AI integration, charts, KPIs, or any template/HTML/CSS.

--------------------------------------------------------------------------
BEHAVIOUR (by design -- no window, no console, no popups, ever)
--------------------------------------------------------------------------
  1. No launcher GUI. This script has zero UI code -- no Tkinter, no
     CustomTkinter, no message boxes. It is a pure background bootstrapper.
  2. No CMD/console window -- built with PyInstaller's console=False, and
     the Flask child process is started with CREATE_NO_WINDOW + a hidden
     STARTUPINFO.
  3. Checks http://127.0.0.1:<port> first. If something is already
     listening there, it assumes the dashboard is already running, opens
     the browser itself (nothing else is going to), and exits -- it never
     starts a second Flask instance.
  4. Otherwise it starts app.py completely hidden and waits (polling the
     port) until Flask actually responds. IMPORTANT: app.py itself opens
     the browser exactly once, ~1 second after its own startup (see the
     Timer(1.0, _open_browser, ...) call at the bottom of app.py). This
     launcher deliberately does NOT open the browser a second time in this
     path -- it only waits so it can log success/failure. Browser-opening
     therefore happens in exactly one place for any given run: app.py when
     a fresh instance is started, or this launcher when it finds Flask
     already running. The two paths are mutually exclusive, so the browser
     is opened once and only once per double-click, never twice.
  5. As soon as start-up has been confirmed (or the browser has been
     opened, in the "already running" case), THIS launcher process exits.
     Flask keeps running in the background as an independent process --
     closing the launcher does not stop it. It stays up until the user
     ends the python.exe process manually (Task Manager) or shuts down
     Windows.
  6. A single-instance lock (a local TCP port used purely as a mutex)
     guarantees only one launcher can ever be doing this start-up sequence
     at a time, so a double/triple-click never races into two Flask
     servers.
  7. All lifecycle events and any errors are appended to launcher.log next
     to the executable -- there is nothing to see on screen, ever, even on
     failure. There are no popups.

--------------------------------------------------------------------------
WHY THIS IS FROZEN-SAFE (important, this bit caused a bug previously)
--------------------------------------------------------------------------
When compiled with PyInstaller, `__file__` does NOT point at the folder the
.exe actually sits in -- it points inside a temporary extraction directory.
So this script resolves its real folder from `sys.executable` (which IS the
.exe's real path) whenever `sys.frozen` is set, and only uses `__file__`
when running as a plain .py script. It also NEVER falls back to using its
own executable as "the python interpreter to run app.py with" -- that
mistake is what caused a launcher-relaunching-itself loop in an earlier
version of this file.
================================================================================
"""

import logging
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# --------------------------------------------------------------------------
# Paths / constants
# --------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Frozen build: __file__ points into a temp extraction dir, NOT the
    # folder the .exe actually sits in. sys.executable is the real path.
    BASE_DIR = Path(sys.executable).resolve().parent
    THIS_EXE = Path(sys.executable).resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent
    THIS_EXE = Path(sys.executable).resolve()  # the python.exe running this script

VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
APP_ENTRY = BASE_DIR / "app.py"
PID_FILE = BASE_DIR / ".dashboard.pid"
LAUNCHER_LOG = BASE_DIR / "launcher.log"
FLASK_LOG = BASE_DIR / "flask_server.log"

# Try to read the REAL host/port straight from the project's own config.py
# so the launcher can never drift out of sync with the Flask app.
HOST, PORT = "127.0.0.1", 5000
try:
    sys.path.insert(0, str(BASE_DIR))
    from config import Config  # noqa: E402  (import after sys.path tweak, by design)
    HOST = getattr(Config, "HOST", HOST)
    PORT = getattr(Config, "PORT", PORT)
except Exception:
    pass  # fall back to the defaults above -- config.py is untouched either way

DASHBOARD_URL = f"http://{HOST}:{PORT}/"

CREATE_NO_WINDOW = 0x08000000  # Windows-only flag to fully hide the console

STARTUP_TIMEOUT_SECONDS = 45.0
POLL_INTERVAL_SECONDS = 0.4

# Fixed local port used ONLY as a single-instance mutex for THIS launcher
# process (deliberately different from the Flask port). While one launcher
# is running its start-up sequence, any second launch exits immediately.
SINGLE_INSTANCE_PORT = 51920
_instance_lock_socket = None  # kept alive for the whole process lifetime


# --------------------------------------------------------------------------
# Logging -- the ONLY output surface this launcher has. No console, no UI.
# --------------------------------------------------------------------------
def _setup_logging() -> None:
    logging.basicConfig(
        filename=str(LAUNCHER_LOG),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# --------------------------------------------------------------------------
# Single-instance guard
# --------------------------------------------------------------------------
def acquire_single_instance_lock() -> bool:
    """
    Returns True if this is the only running instance (and holds the lock
    for the lifetime of the process). Returns False if another instance is
    already mid-startup.
    """
    global _instance_lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        s.listen(1)
        _instance_lock_socket = s  # keep alive so the OS doesn't release the port
        return True
    except OSError:
        s.close()
        return False


# --------------------------------------------------------------------------
# Server helpers
# --------------------------------------------------------------------------
def is_server_up(timeout: float = 0.6) -> bool:
    """Best-effort TCP check: is something already listening on HOST:PORT?"""
    try:
        with socket.create_connection((HOST, PORT), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_server(timeout: float, interval: float) -> bool:
    """Poll until the server accepts connections, or give up after `timeout`s."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_server_up(timeout=0.5):
            return True
        time.sleep(interval)
    return False


def write_pid(pid: int) -> None:
    try:
        PID_FILE.write_text(str(pid))
    except Exception:
        pass


def resolve_python_exe():
    """
    Find a REAL python.exe to run app.py with. Returns the path as a string,
    or None if no safe interpreter could be found.

    Deliberately NEVER returns this launcher's own executable -- that was
    the root cause of a self-relaunch loop in an earlier version.
    """
    if VENV_PYTHON.exists():
        candidate = VENV_PYTHON.resolve()
        if candidate != THIS_EXE:
            return str(candidate)

    system_python = shutil.which("python")
    if system_python:
        candidate = Path(system_python).resolve()
        if candidate != THIS_EXE and candidate.name.lower() not in ("uberai.exe",):
            return str(candidate)

    return None


def start_flask_hidden(python_exe: str) -> subprocess.Popen:
    creationflags = CREATE_NO_WINDOW if os.name == "nt" else 0
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    log_handle = open(FLASK_LOG, "a", encoding="utf-8", errors="ignore")
    log_handle.write(f"\n--- Flask start at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    log_handle.flush()

    proc = subprocess.Popen(
        [python_exe, str(APP_ENTRY)],
        cwd=str(BASE_DIR),
        stdout=log_handle,
        stderr=log_handle,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )
    return proc


# --------------------------------------------------------------------------
# Main bootstrap sequence
# --------------------------------------------------------------------------
def main() -> int:
    _setup_logging()
    logging.info("Launcher started. BASE_DIR=%s", BASE_DIR)

    if os.name != "nt":
        logging.error("This launcher only supports Windows. Exiting.")
        return 1

    if not acquire_single_instance_lock():
        logging.info("Another launcher instance is already starting up. Exiting silently.")
        return 0

    # --- Case 1: dashboard already running -> just open the browser ---
    # This is the ONLY place in this launcher that calls webbrowser.open().
    # It only runs when Flask was already up from a previous session, so
    # nothing else (no fresh app.py process, no Timer inside it) is going
    # to open a tab for us -- we have to do it here, exactly once.
    if is_server_up():
        logging.info("Flask already reachable at %s -- opening browser.", DASHBOARD_URL)
        webbrowser.open(DASHBOARD_URL)
        return 0

    # --- Case 2: not running -> start it hidden, then wait & open once ---
    python_exe = resolve_python_exe()
    if python_exe is None:
        logging.error(
            "No safe Python interpreter found (expected venv at %s, and no "
            "usable system python.exe on PATH). Cannot start the dashboard.",
            VENV_PYTHON,
        )
        return 1

    if Path(python_exe).resolve() == THIS_EXE:
        logging.error(
            "Safety check failed: resolved interpreter points at the "
            "launcher itself. Aborting to avoid a relaunch loop."
        )
        return 1

    if not APP_ENTRY.exists():
        logging.error("app.py not found next to the launcher at %s. Aborting.", APP_ENTRY)
        return 1

    try:
        proc = start_flask_hidden(python_exe)
    except Exception:
        logging.exception("Failed to start app.py.")
        return 1

    write_pid(proc.pid)
    logging.info("Flask process started (PID %s) using %s. Waiting for it to respond...",
                 proc.pid, python_exe)

    ready = wait_for_server(STARTUP_TIMEOUT_SECONDS, POLL_INTERVAL_SECONDS)

    if ready:
        # NOTE: we deliberately do NOT call webbrowser.open() here.
        # app.py opens the browser itself (Timer(1.0, _open_browser, ...)
        # at the bottom of app.py) ~1 second after it starts serving. If
        # this launcher also opened the browser at this point, every cold
        # start would show two tabs pointing at the same URL. Opening the
        # browser is the responsibility of whichever process actually
        # brings Flask up for the first time (app.py); this launcher only
        # opens the browser itself in the "already running" branch above,
        # where nothing else would open it.
        logging.info(
            "Flask is reachable at %s -- app.py will open the browser itself. "
            "Launcher will not open a second tab.", DASHBOARD_URL,
        )
    else:
        logging.error(
            "Flask did not respond within %.0f seconds. Browser was NOT opened. "
            "The server process (PID %s) is left running in case it is still "
            "starting up -- check %s for details.",
            STARTUP_TIMEOUT_SECONDS, proc.pid, FLASK_LOG,
        )
        return 1

    logging.info("Launcher exiting; dashboard continues running in the background.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
