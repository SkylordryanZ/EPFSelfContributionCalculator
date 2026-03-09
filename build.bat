@echo off
echo Installing requirements...
py -m pip install customtkinter pyinstaller matplotlib

echo.
echo Building executable...
py build.py

echo.
echo Build complete. The Executable can be found in the "dist" folder.
pause
