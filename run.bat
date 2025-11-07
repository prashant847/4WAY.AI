@echo off
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║     🚦 ADVANCED TRAFFIC MANAGEMENT SYSTEM 🚦                   ║
echo ║                                                                ║
echo ║     AI-Powered Smart Traffic Signal Controller                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo.

:MENU
echo ┌────────────────────────────────────────────────────────────────┐
echo │                      MAIN MENU                                 │
echo ├────────────────────────────────────────────────────────────────┤
echo │                                                                │
echo │  [1] 🚀 Run Complete System Test                               │
echo │      (Process videos and generate full analysis)              │
echo │                                                                │
echo │  [2] 🌐 Start API Server                                       │
echo │      (Launch Flask REST API on port 5000)                     │
echo │                                                                │
echo │  [3] 🧪 Test API with Example Client                           │
echo │      (Test all API endpoints)                                 │
echo │                                                                │
echo │  [4] 📁 Organize Videos                                        │
echo │      (Move videos to correct folders)                         │
echo │                                                                │
echo │  [5] 📦 Install/Update Dependencies                            │
echo │      (Install required Python packages)                       │
echo │                                                                │
echo │  [6] 📊 View System Status                                     │
echo │      (Check installation and files)                           │
echo │                                                                │
echo │  [0] ❌ Exit                                                    │
echo │                                                                │
echo └────────────────────────────────────────────────────────────────┘
echo.

set /p choice="Enter your choice (0-6): "

if "%choice%"=="1" goto TEST_SYSTEM
if "%choice%"=="2" goto START_API
if "%choice%"=="3" goto TEST_API
if "%choice%"=="4" goto ORGANIZE
if "%choice%"=="5" goto INSTALL
if "%choice%"=="6" goto STATUS
if "%choice%"=="0" goto EXIT
goto MENU

:TEST_SYSTEM
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Running Complete System Test...
echo ════════════════════════════════════════════════════════════════
echo.
echo This will:
echo  ✓ Process all 4 traffic videos
echo  ✓ Detect vehicles using YOLOv8
echo  ✓ Analyze congestion levels
echo  ✓ Assign traffic signals
echo  ✓ Generate reports and charts
echo.
pause
echo.
python test_system.py
echo.
echo ════════════════════════════════════════════════════════════════
echo  Test Complete! Check the output folder for results.
echo ════════════════════════════════════════════════════════════════
echo.
pause
goto MENU

:START_API
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Starting Flask API Server...
echo ════════════════════════════════════════════════════════════════
echo.
echo Server will start at: http://localhost:5000
echo.
echo Available endpoints:
echo  • GET  /api/health      - Health check
echo  • POST /api/process-videos - Process videos
echo  • GET  /api/signals     - Get signal states
echo  • GET  /api/analysis    - Get analysis results
echo.
echo Press Ctrl+C to stop the server
echo.
pause
echo.
python app.py
goto MENU

:TEST_API
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Testing API Client...
echo ════════════════════════════════════════════════════════════════
echo.
echo Make sure the API server is running first!
echo (Start it from option 2 in another terminal)
echo.
pause
echo.
python api_client_example.py
echo.
pause
goto MENU

:ORGANIZE
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Organizing Videos...
echo ════════════════════════════════════════════════════════════════
echo.
call organize_videos.bat
goto MENU

:INSTALL
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Installing/Updating Dependencies...
echo ════════════════════════════════════════════════════════════════
echo.
call install.bat
pause
goto MENU

:STATUS
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  System Status Check
echo ════════════════════════════════════════════════════════════════
echo.

echo [Python Version]
python --version
echo.

echo [Required Directories]
if exist "videos" (echo ✓ videos/) else (echo ✗ videos/ - missing)
if exist "output" (echo ✓ output/) else (echo ✗ output/ - missing)
if exist "models" (echo ✓ models/) else (echo ✗ models/ - missing)
if exist "logs" (echo ✓ logs/) else (echo ✗ logs/ - missing)
echo.

echo [Video Files]
if exist "videos\lane_0.mp4" (echo ✓ lane_0.mp4 (North)) else (echo ✗ lane_0.mp4 - missing)
if exist "videos\lane_1.mp4" (echo ✓ lane_1.mp4 (South)) else (echo ✗ lane_1.mp4 - missing)
if exist "videos\lane_2.mp4" (echo ✓ lane_2.mp4 (East)) else (echo ✗ lane_2.mp4 - missing)
if exist "videos\lane_3.mp4" (echo ✓ lane_3.mp4 (West)) else (echo ✗ lane_3.mp4 - missing)
echo.

echo [Core Files]
if exist "app.py" (echo ✓ app.py) else (echo ✗ app.py - missing)
if exist "vehicle_detector.py" (echo ✓ vehicle_detector.py) else (echo ✗ vehicle_detector.py - missing)
if exist "traffic_analyzer.py" (echo ✓ traffic_analyzer.py) else (echo ✗ traffic_analyzer.py - missing)
if exist "signal_controller.py" (echo ✓ signal_controller.py) else (echo ✗ signal_controller.py - missing)
echo.

echo [Virtual Environment]
if exist "venv" (echo ✓ Virtual environment exists) else (echo ✗ Virtual environment not created - run option 5)
echo.

echo ════════════════════════════════════════════════════════════════
pause
goto MENU

:EXIT
cls
echo.
echo ════════════════════════════════════════════════════════════════
echo  Thank you for using Traffic Management System!
echo ════════════════════════════════════════════════════════════════
echo.
echo  For documentation, see:
echo   • README.md - Complete guide
echo   • QUICKSTART.md - Quick tutorial
echo   • ARCHITECTURE.md - Technical details
echo.
timeout /t 3
exit

