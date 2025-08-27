#!/bin/bash

# Get the absolute path of the directory containing this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory.
cd "$SCRIPT_DIR"

# Activate the virtual environment.
source "venv/bin/activate"

# Run the GUI application.
python gui.py
