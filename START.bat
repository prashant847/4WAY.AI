@echo off
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║     ✅ SYSTEM IS READY - QUICK START GUIDE                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Your Advanced Traffic Management System is now ready to use!
echo.
echo ══════════════════════════════════════════════════════════════════
echo  📁 VIDEOS ORGANIZED
echo ══════════════════════════════════════════════════════════════════
echo  ✓ videos\lane_0.mp4  (North)
echo  ✓ videos\lane_1.mp4  (South)
echo  ✓ videos\lane_2.mp4  (East)
echo  ✓ videos\lane_3.mp4  (West)
echo.
echo ══════════════════════════════════════════════════════════════════
echo  🚀 HOW TO RUN THE SYSTEM
echo ══════════════════════════════════════════════════════════════════
echo.
echo  OPTION 1: Run Test (Process all videos and analyze)
echo  ────────────────────────────────────────────────────
echo    Command: venv\Scripts\activate
echo             python test_system.py
echo.
echo  OPTION 2: Start API Server (for web/app integration)
echo  ────────────────────────────────────────────────────
echo    Command: venv\Scripts\activate
echo             python app.py
echo    Access at: http://localhost:5000
echo.
echo  OPTION 3: Use Interactive Menu
echo  ────────────────────────────────────────────────────
echo    Command: run.bat
echo.
echo ══════════════════════════════════════════════════════════════════
echo  🎯 CHOOSE YOUR OPTION
echo ══════════════════════════════════════════════════════════════════
echo.
echo  [1] Run Test System Now
echo  [2] Start API Server
echo  [3] Open Interactive Menu
echo  [0] Exit
echo.
set /p choice="Enter your choice (0-3): "

if "%choice%"=="1" goto RUN_TEST
if "%choice%"=="2" goto START_API
if "%choice%"=="3" goto MENU
if "%choice%"=="0" goto END
goto END

:RUN_TEST
echo.
echo Starting test system...
call venv\Scripts\activate
python test_system.py
pause
goto END

:START_API
echo.
echo Starting API server...
echo Server will be available at: http://localhost:5000
call venv\Scripts\activate
python app.py
goto END

:MENU
echo.
call run.bat
goto END

:END
echo.
echo Thank you for using Traffic Management System!
echo.
timeout /t 2
