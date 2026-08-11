@echo off
setlocal

REM ============================================================================
REM run.bat - AI-Enabled Uber India Operations Analytics Dashboard
REM Creates a virtual environment if needed, installs dependencies, starts the
REM Flask app, and opens it in your default browser.
REM ============================================================================

cd /d "%~dp0"

echo ================================================================
echo  Uber India Operations Analytics Dashboard
echo ================================================================
echo.

REM --- Check Python is available ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.10 or later from https://www.python.org/downloads/
    echo and make sure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

REM --- Create virtual environment if it doesn't already exist ---
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists - skipping creation.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/updating dependencies from requirements.txt...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Check your internet connection.
    pause
    exit /b 1
)

REM --- Check dataset presence and give an early, clear hint (the app itself
REM     also handles this gracefully with a setup page - this is just a
REM     helpful console message before the browser even opens) ---
if not exist "data\raw\uber.xlsx" (
    echo.
    echo ----------------------------------------------------------------
    echo  NOTE: data\raw\uber.xlsx was not found.
    echo  The app will still start and show setup instructions in your
    echo  browser. Place your dataset at data\raw\uber.xlsx and restart
    echo  this script once it's there.
    echo ----------------------------------------------------------------
)

echo.
echo Starting the application...
echo (Your browser will open automatically in a moment.)
echo.
echo Press CTRL+C in this window to stop the server.
echo ================================================================
echo.

python app.py

pause
