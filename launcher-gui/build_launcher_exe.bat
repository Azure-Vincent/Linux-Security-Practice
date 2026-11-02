@echo off
REM Build a standalone, windowless BeaconHunt Launcher.exe (run on Windows).
REM The .exe still needs Python + Docker available (the app itself requires them).
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller || goto :err
pyinstaller --noconfirm --onefile --windowed --name "BeaconHunt Launcher" ^
  --add-data "bh_backend.py;." ^
  beaconhunt_launcher.py || goto :err
echo.
echo ============================================================
echo  Built: dist\BeaconHunt Launcher.exe
echo  Put it in (or next to) the BeaconHunt app folder.
echo ============================================================
pause
exit /b 0
:err
echo Build failed. Ensure Python 3.10+ and pip are installed.
pause
exit /b 1
