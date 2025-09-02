@echo off
echo === Testing HappyTag_Debug.exe ===
echo Current time: %time%
echo Starting debug executable...
echo.

.\dist\HappyTag_Debug.exe

echo.
echo === Debug executable finished ===
echo End time: %time%
echo.
echo Press any key to close this window...
pause >nul
