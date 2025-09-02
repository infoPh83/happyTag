@echo off
echo === HappyTag Build Test ===
echo Testing the newly built executable...
echo.

if exist "dist\HappyTag.exe" (
    echo Found HappyTag.exe, launching...
    echo.
    start "HappyTag Test" /wait "dist\HappyTag.exe"
    echo.
    echo Executable finished running.
) else (
    echo ERROR: HappyTag.exe not found in dist folder!
)

echo.
echo Press any key to close...
pause >nul
