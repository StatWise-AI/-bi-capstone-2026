# Dashboard Launcher — Setup & Usage

This adds a professional Windows launcher for the **AI-Enabled Uber India
Operations Analytics Dashboard**, replacing the old "double-click `run.bat`
and watch a black CMD window" workflow.

**Nothing about the dashboard itself changed.** No Flask route, template,
chart, KPI, or Gemini AI code was touched. These files sit alongside the
existing project and only control *how the app starts*.

## Files added

| File                 | Purpose                                                              |
|----------------------|-----------------------------------------------------------------------|
| `launcher.py`         | The GUI launcher (CustomTkinter, falls back to plain Tkinter).       |
| `launcher.spec`       | PyInstaller spec to compile `launcher.py` into a single `.exe`.      |
| `build_launcher.bat`  | One-click script that installs build deps and runs PyInstaller.      |
| `run_hidden.py`       | Optional no-GUI fallback: silently starts Flask + opens the browser. |
| `README_LAUNCHER.md`  | This file.                                                            |

## Where to put these files

Copy all of the files above into the **project root** — the same folder
that already contains `app.py`, `config.py`, `requirements.txt`, `venv\`,
and `run.bat`. The launcher automatically:

- finds `venv\Scripts\python.exe` and uses it to run `app.py`,
- reads the real `HOST`/`PORT` straight from `config.py`, so it can never
  drift out of sync with the actual Flask app,
- keeps `run.bat` in place untouched, in case you ever want it back.

## Option A — Run it directly with Python (no build step)

1. Make sure `customtkinter` is installed in your venv:
   ```
   venv\Scripts\python.exe -m pip install customtkinter pillow
   ```
2. Double-click `launcher.py`, or run:
   ```
   venv\Scripts\pythonw.exe launcher.py
   ```
   (using `pythonw.exe` instead of `python.exe` avoids a console window for
   the launcher itself; Flask is already started hidden either way.)

## Option B — Build a standalone `.exe` (recommended for end users)

1. Double-click **`build_launcher.bat`**.
   - It installs `customtkinter`, `pillow`, and `pyinstaller` into your
     project's venv, then runs PyInstaller with `launcher.spec`.
2. When it finishes, you'll have:
   ```
   dist\UberDashboardLauncher.exe
   ```
3. Move/copy that single `.exe` back into the project root (next to
   `app.py`), and double-click it any time you want to open the dashboard.
   You can also pin it to the Start Menu or Taskbar.

### Optional extras for the build
- Drop a `app_icon.ico` file next to `launcher.spec` to give the `.exe` a
  custom icon.
- Drop a real logo at `assets\uber_logo.png` to replace the placeholder "U"
  badge shown in the launcher window.

## How it behaves

| Button              | Behaviour |
|----------------------|-----------|
| **Launch Dashboard** | Starts `app.py` completely hidden (no CMD window) using the project's venv. If the server is already running, it does **not** start a second instance — it just opens the browser. Waits for the server to actually respond before opening the browser. |
| **Open Dashboard**   | Opens `http://127.0.0.1:5000/` (or whatever `config.py` says) in your default browser. Does not start anything. |
| **Stop Dashboard**   | Gracefully terminates the Flask process (and any child processes) that this launcher started. |
| **Exit**              | Closes the launcher window only. The dashboard keeps running in the background if it was started — use **Stop Dashboard** first if you want to shut everything down. |

The status dot updates automatically every 2 seconds (green = running,
red = stopped), even if the server was started or stopped from outside the
launcher.

## Notes on the existing auto-open in `app.py`

`app.py` already opens the browser itself, about one second after Flask
starts (`Timer(1.0, _open_browser, ...)`). That code was **not modified**,
per your instructions. The launcher does its own, more reliable
"wait-until-ready-then-open" on top of that. In practice this means the
very first launch may occasionally open two browser tabs a moment apart —
harmless, just close the extra one. If you'd rather it never happens,
you can (optionally, later) remove that `Timer(...)` line from `app.py`
yourself, since the launcher already guarantees the browser opens once the
server is actually ready.

## Logs & process tracking

- `dashboard_launcher.log` — stdout/stderr from the hidden Flask process
  (useful if "Launch Dashboard" reports a timeout).
- `.dashboard.pid` — the process ID of the Flask instance the launcher
  started, used by "Stop Dashboard". Safe to delete when the app isn't
  running.

Both files are created next to `launcher.py` and are launcher-only
artifacts — they're not read or written by the Flask app itself.
