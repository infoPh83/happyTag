@echo off
echo === Testing HappyTag_Debug_Win.exe ===
echo Clean build with only essential files
echo Time started: %time%
echo.

.\dist\HappyTag_Debug_Win.exe

echo.
echo === Debug executable finished ===
echo Time finished: %time%
echo.
echo Press any key to close this debug console...
pause >nul
