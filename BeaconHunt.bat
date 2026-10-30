@echo off
REM BeaconHunt launcher — double-click to open the GUI (needs Python 3.10+).
cd /d "%~dp0"

REM Ensure PyYAML is present (the only runtime dependency).
python -c "import yaml" 1>nul 2>nul || python -m pip install --quiet pyyaml

python beaconhunt_gui.py
if errorlevel 1 (
  echo.
  echo Could not start with 'python'. Trying the 'py' launcher...
  py beaconhunt_gui.py
)
if errorlevel 1 pause
