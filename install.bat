@echo off
echo ========================================
echo Advanced Traffic Management System
echo Installation Script for Windows
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/6] Python found!
python --version
echo.

REM Create directories
echo [2/6] Creating required directories...
if not exist "videos" mkdir videos
if not exist "output" mkdir output
if not exist "models" mkdir models
if not exist "logs" mkdir logs
echo Done!
echo.

REM Create virtual environment
echo [3/6] Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created!
)
echo.

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo [5/6] Installing Python packages...
echo This may take a few minutes...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo All packages installed successfully!
echo.

REM Create .env file
echo [6/6] Setting up environment...
if not exist ".env" (
    copy .env.example .env
    echo .env file created from template
) else (
    echo .env file already exists
)
echo.

echo ========================================
echo Installation Complete! 
echo ========================================
echo.
echo Next Steps:
echo 1. Place your 4 traffic videos in the 'videos' folder
echo 2. Run: python test_system.py
echo    OR
echo    Run: python app.py (to start API server)
echo.
echo To activate the virtual environment in future:
echo    venv\Scripts\activate
echo.
echo For detailed instructions, see README.md or QUICKSTART.md
echo ========================================
pause
