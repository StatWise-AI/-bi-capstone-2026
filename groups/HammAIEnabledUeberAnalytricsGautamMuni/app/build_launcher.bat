@echo off
setlocal

REM ============================================================================
REM build_launcher.bat
REM Builds UberAI.exe (the silent bootstrap launcher) from launcher.py using
REM PyInstaller.
REM
REM Run this ONCE (or whenever you edit launcher.py) from the project root,
REM i.e. the same folder that contains app.py, config.py, venv\, etc.
REM
REM IMPORTANT: the built .exe MUST stay in this project-root folder to find
REM app.py and venv\. This script copies it there automatically after a
REM successful build.
REM ============================================================================

cd /d "%~dp0"

echo ================================================================
echo  Building UberAI.exe (silent dashboard launcher)
echo ================================================================
echo.

REM --- Prefer the project's own venv so PyInstaller bundles the exact
REM     same Python version the project already uses ---
if exist "venv\Scripts\python.exe" (
    set "PYEXE=venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python was not found on your system PATH and no venv exists.
        echo Please install Python 3.10+ or run run.bat once first to create venv\.
        pause
        exit /b 1
    )
    set "PYEXE=python"
)

echo Using interpreter: %PYEXE%
echo.

echo Installing/updating PyInstaller...
"%PYEXE%" -m pip install --upgrade pip >nul
"%PYEXE%" -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "UberAI.exe" del /f /q "UberAI.exe"

echo.
echo Running PyInstaller...
"%PYEXE%" -m PyInstaller launcher.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed. See the output above for details.
    pause
    exit /b 1
)

if not exist "dist\UberAI.exe" (
    echo [ERROR] Build reported success but dist\UberAI.exe is missing.
    pause
    exit /b 1
)

echo.
echo Copying UberAI.exe into the project root (required so it can find
echo app.py and venv\ next to it)...
copy /Y "dist\UberAI.exe" "UberAI.exe" >nul
if errorlevel 1 (
    echo [ERROR] Could not copy the .exe into the project root.
    echo You can copy it manually from dist\UberAI.exe
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  Build complete.
echo  Ready to use: UberAI.exe  (in this folder)
echo  A copy also remains at: dist\UberAI.exe
echo.
echo  Double-click UberAI.exe any time. It runs completely silently:
echo  no window, no console. It checks if the dashboard is already
echo  running, starts it hidden if not, waits for it to respond, opens
echo  your browser once, then exits on its own. The dashboard itself
echo  keeps running in the background afterwards.
echo.
echo  Troubleshooting: if the browser never opens, check launcher.log
echo  and flask_server.log in this folder.
echo ================================================================
echo.
pause
