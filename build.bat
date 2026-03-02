@echo off
echo Installing requirements...
py -m pip install customtkinter pyinstaller matplotlib

echo.
echo Building executable...
py -m PyInstaller --noconsole --onefile --windowed --name "EPFSelfContributionCalc" app.py

echo.
echo Build complete. The Executable can be found in the "dist" folder.
pause
