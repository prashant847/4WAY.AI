@echo off
echo ========================================
echo   Traffic Management System - Launcher
echo ========================================
echo.
echo Starting Flask Backend API...
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Backend API starting on http://localhost:5000
echo.
echo IMPORTANT: 
echo 1. Backend will run on port 5000
echo 2. Open index.html in your browser to view dashboard
echo 3. Press Ctrl+C to stop the server
echo.

python app.py

pause
