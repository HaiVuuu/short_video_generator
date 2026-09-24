@echo off
REM One-time setup: creates a virtual environment, installs dependencies, and prepares FFmpeg binaries.
REM Usage: setup.bat

cd /d "%~dp0"

echo [1/3] Creating virtual environment in .\venv ...
python -m venv venv

echo [2/3] Installing dependencies...
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt

echo [3/3] Fetching bundled static FFmpeg binaries...
.\venv\Scripts\python -c "import static_ffmpeg; static_ffmpeg.add_paths()"

echo.
echo ============================================================
echo Setup complete!
echo.
echo To run the pipeline:
echo    .\venv\Scripts\python scripts\run_pipeline.py
echo.
echo Or activate the virtual environment first:
echo    .\venv\Scripts\activate
echo    python scripts\run_pipeline.py
echo ============================================================
