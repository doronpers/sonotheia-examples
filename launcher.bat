@echo off
REM Sonotheia Examples - Windows Launch Script
REM Double-click to launch or run from Command Prompt

cd /d "%~dp0"
echo.
echo ========================================
echo   Sonotheia Examples Launcher (Windows)
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python detected
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install evaluation framework if it exists
if exist "evaluation" (
    echo [INFO] Installing evaluation framework...
    pip install -e "evaluation[dev]" --quiet
    if errorlevel 1 (
        echo [WARNING] Evaluation framework installation had issues
        echo Continuing anyway...
    )
)

REM Install examples dependencies if they exist
if exist "examples\python\requirements.txt" (
    echo [INFO] Installing Python examples dependencies...
    pip install -r examples\python\requirements.txt --quiet
    if errorlevel 1 (
        echo [WARNING] Examples dependencies installation had issues
        echo Continuing anyway...
    )
)

REM Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env file from .env.example...
        copy .env.example .env >nul
        echo [OK] .env file created. Please edit it with your API keys.
    ) else (
        echo [WARNING] No .env.example found. You may need to create .env manually.
    )
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file with your API keys (if needed)
echo   2. Run: launcher.bat dev (to set up development environment)
echo   3. Or run examples directly from examples\python\
echo.
echo For more information, see:
echo   documentation\LAUNCH_AND_ONBOARDING.md
echo.
pause
