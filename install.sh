#!/bin/bash

echo "========================================"
echo "Advanced Traffic Management System"
echo "Installation Script for Linux/Mac"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/6] Python found!"
python3 --version
echo ""

# Create directories
echo "[2/6] Creating required directories..."
mkdir -p videos output models logs
echo "Done!"
echo ""

# Create virtual environment
echo "[3/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "Virtual environment created!"
fi
echo ""

# Activate virtual environment
echo "[4/6] Activating virtual environment..."
source venv/bin/activate
echo ""

# Install dependencies
echo "[5/6] Installing Python packages..."
echo "This may take a few minutes..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "All packages installed successfully!"
echo ""

# Create .env file
echo "[6/6] Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env file created from template"
else
    echo ".env file already exists"
fi
echo ""

echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Place your 4 traffic videos in the 'videos' folder"
echo "2. Run: python test_system.py"
echo "   OR"
echo "   Run: python app.py (to start API server)"
echo ""
echo "To activate the virtual environment in future:"
echo "   source venv/bin/activate"
echo ""
echo "For detailed instructions, see README.md or QUICKSTART.md"
echo "========================================"
