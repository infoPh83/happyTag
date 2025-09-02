@echo off
title HappyTag Debug Console
color 0F
echo.
echo ===============================================
echo              HappyTag Debug Mode
echo ===============================================
echo.
echo Starting application with console output...
echo If no output appears, the app may be running in background.
echo Check your taskbar for the HappyTag window.
echo.
echo Time started: %time%
echo.

REM Run the executable and wait for it to finish
.\dist\HappyTag.exe

echo.
echo ===============================================
echo Time finished: %time%
echo.
echo The application has closed.
echo Check above for any error messages.
echo.
echo Press any key to close this debug console...
pause >nul
