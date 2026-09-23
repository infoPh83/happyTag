@echo off
REM ============================================================================
REM Build HappyTag exe (PyInstaller) and wrap it in an Inno Setup installer.
REM Usage:  build_installer.bat
REM ============================================================================
setlocal

cd /d "%~dp0\.."

echo.
echo === Step 1/2: Building HappyTag.exe with PyInstaller ===
call ".venv_win\Scripts\activate.bat"
pyinstaller HappyTag_Win.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo !!! PyInstaller build FAILED - fix errors above and re-run.
    exit /b 1
)

echo.
echo === Step 2/2: Compiling installer with Inno Setup ===
REM Check the per-user install location first, then the machine-wide default
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto :no_inno
goto :compile

:no_inno
echo !!! Inno Setup compiler not found.
echo     Looked in: %LOCALAPPDATA%\Programs\Inno Setup 6
echo     and:       C:\Program Files ^(x86^)\Inno Setup 6
echo     Install Inno Setup 6 from https://jrsoftware.org/isdl.php
exit /b 1

:compile
echo Using Inno compiler: %ISCC%
"%ISCC%" installer\HappyTag_Setup.iss
if errorlevel 1 (
    echo.
    echo !!! Inno Setup compilation FAILED - fix errors above and re-run.
    exit /b 1
)

echo.
echo === DONE ===
echo Installer created at: installer\installer_output\HappyTag_Setup_*.exe
endlocal
