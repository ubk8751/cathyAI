#!/bin/bash
# Development environment setup script for cathyAI

echo "Setting up cathyAI development environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create static directory if it doesn't exist
if [ ! -d "static" ]; then
    echo "Creating static directory..."
    mkdir -p static
    echo "✓ Static directory created"
else
    echo "✓ Static directory exists"
fi

# Check if avatar exists
if [ ! -f "public/avatars/catherine_pfp.jpg" ]; then
    echo "⚠️  Warning: Avatar file static/catherine_pfp.jpg not found"
    echo "   Please add your avatar image to the static directory"
fi

# Make watchdog script executable
if [ -f "watchdog.sh" ]; then
    chmod +x watchdog.sh
    echo "✓ Watchdog script made executable"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the app locally:"
echo "  chainlit run app.py"
echo ""
echo "To run tests:"
echo "  pytest tests/test_app.py"
