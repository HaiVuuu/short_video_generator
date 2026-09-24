@echo off
REM One-time setup: creates a virtual environment and installs dependencies.
REM Usage: setup.bat

cd /d "%~dp0"

echo Creating virtual environment in .\venv ...
python -m venv venv

echo Installing dependencies...
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt

echo.
echo Done. From now on, run pipeline scripts with:
echo   venv\Scripts\python scripts\run_pipeline.py
echo.
echo Or activate the environment first so you can just use 'python':
echo   venv\Scripts\activate
echo   python scripts\run_pipeline.py
