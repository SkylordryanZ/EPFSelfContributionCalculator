@echo off
setlocal

echo ============================================
echo  EPF Self-Contribution Calculator - Builder
echo ============================================
echo.

REM Check if Python 3.12 is available via the py launcher
py -V:3.12 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.12 was not found on this machine.
    echo.
    echo PyInstaller does not yet support Python 3.14+.
    echo Please install Python 3.12 by running:
    echo   py install 3.12
    echo.
    pause
    exit /b 1
)

echo [OK] Python 3.12 found.
echo.

echo Installing required packages with Python 3.12...
py -V:3.12 -m pip install --upgrade customtkinter pyinstaller matplotlib
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b 1
)

echo.
echo Building self-contained executable with Python 3.12...
py -V:3.12 build.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Build complete!
echo  The standalone .exe is in the "dist" folder.
echo  Clients do NOT need Python installed to run it.
echo ============================================
pause
endlocal
