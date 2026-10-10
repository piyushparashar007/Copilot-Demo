#!/usr/bin/env bash

set -e

echo "Preparing security scanning environment..."

VENV_DIR=".security-scan-env"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python -m venv $VENV_DIR
fi

echo "Activating environment..."
source $VENV_DIR/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing security tools..."

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

echo "Security tool installation complete."