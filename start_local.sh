#!/bin/bash

# This script sets up the local development environment
# and runs the Flask application.

set -e

VENV_DIR="venv"
PYTHON_EXEC="python3"

# Find a valid Python 3 executable
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ ERROR: Python 3 is not found."
        echo "Please install Python 3 and ensure 'python3' or 'python' is in your PATH."
        exit 1
    else
        PYTHON_EXEC="python"
    fi
else
    PYTHON_EXEC="python3"
fi

echo "🐍 Found Python at: $($PYTHON_EXEC -c 'import sys; print(sys.executable)')"

# Check if LibreOffice is installed locally
if ! command -v soffice &> /dev/null; then
    echo "⚠️ WARNING: 'soffice' (LibreOffice) not found in your PATH."
    echo "PDF conversion will fail."
    echo "Please install it (e.g., 'sudo apt-get install libreoffice' or 'brew install libreoffice')"
    read -p "Press [Enter] to continue anyway..."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating new virtual environment in '$VENV_DIR'..."
    $PYTHON_EXEC -m venv $VENV_DIR
fi

# NOTE: We don't use 'source' anymore, as we call executables directly.
echo "Virtual environment is ready at '$VENV_DIR'"

echo "📦 Installing/updating dependencies from requirements.txt..."
# EXPLICITLY use the 'pip' from the virtual environment
"$VENV_DIR/bin/pip" install -r requirements.txt

echo "🚀 Starting Flask app in development mode..."
echo "Access the API at: http://localhost:5000"

# Use FLASK_ENV for older Flask versions, FLASK_DEBUG for newer
export FLASK_ENV=development
export FLASK_DEBUG=1

# EXPLICITLY use the 'python' from the virtual environment
"$VENV_DIR/bin/python" app.py

