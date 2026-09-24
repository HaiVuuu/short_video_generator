#!/usr/bin/env bash
# One-time setup: creates a virtual environment and installs dependencies.
# Usage: bash setup.sh
set -e

cd "$(dirname "$0")"

echo "Creating virtual environment in ./venv ..."
python3 -m venv venv

echo "Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "Done. From now on, run pipeline scripts with:"
echo "  ./venv/bin/python scripts/run_pipeline.py"
echo ""
echo "Or activate the environment first so you can just use 'python':"
echo "  source venv/bin/activate"
echo "  python scripts/run_pipeline.py"
