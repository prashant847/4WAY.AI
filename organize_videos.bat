@echo off
echo ======================================
echo Moving videos to videos folder...
echo ======================================

if exist "north.mp4" (
    move /Y "north.mp4" "videos\lane_0.mp4"
    echo ✓ Moved north.mp4 to videos\lane_0.mp4
)

if exist "south.mp4" (
    move /Y "south.mp4" "videos\lane_1.mp4"
    echo ✓ Moved south.mp4 to videos\lane_1.mp4
)

if exist "east.mp4" (
    move /Y "east.mp4" "videos\lane_2.mp4"
    echo ✓ Moved east.mp4 to videos\lane_2.mp4
)

if exist "west.mp4" (
    move /Y "west.mp4" "videos\lane_3.mp4"
    echo ✓ Moved west.mp4 to videos\lane_3.mp4
)

echo.
echo ======================================
echo Videos organized successfully!
echo ======================================
echo.
echo Your videos are now ready in the videos folder:
echo - videos\lane_0.mp4 (North)
echo - videos\lane_1.mp4 (South)
echo - videos\lane_2.mp4 (East)
echo - videos\lane_3.mp4 (West)
echo.
pause
