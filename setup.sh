#!/usr/bin/env bash
# One-time setup: creates a virtual environment, installs dependencies, and prepares FFmpeg binaries.
# Usage: bash setup.sh
set -e

cd "$(dirname "$0")"

echo "[1/3] Creating virtual environment in ./venv ..."
python3 -m venv venv

echo "[2/3] Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "[3/3] Fetching bundled static FFmpeg binaries..."
./venv/bin/python -c "import static_ffmpeg; static_ffmpeg.add_paths()"

echo ""
echo "============================================================"
echo "Setup complete!"
echo ""
echo "To run the pipeline:"
echo "  ./venv/bin/python scripts/run_pipeline.py"
echo ""
echo "Or activate the virtual environment first:"
echo "  source venv/bin/activate"
echo "  python scripts/run_pipeline.py"
echo "============================================================"
