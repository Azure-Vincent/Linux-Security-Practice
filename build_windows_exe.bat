@echo off
REM Build a standalone BeaconHunt.exe (run this ON Windows).
REM Produces dist\BeaconHunt.exe — a single file you can double-click.
cd /d "%~dp0"

python -m pip install --upgrade pyinstaller pyyaml || goto :err

pyinstaller --noconfirm --onefile --windowed --name BeaconHunt ^
  --collect-submodules beaconhunt ^
  --add-data "catalog;catalog" ^
  --add-data "services;services" ^
  --add-data "docker-compose.yml;." ^
  beaconhunt_gui.py || goto :err

echo.
echo ============================================================
echo  Built: dist\BeaconHunt.exe
echo  Keep it with Docker Desktop installed and running.
echo ============================================================
pause
exit /b 0

:err
echo.
echo Build failed. Make sure Python 3.10+ and pip are installed.
pause
exit /b 1
