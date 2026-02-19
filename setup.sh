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

# Create state directory if it doesn't exist
if [ ! -d "state" ]; then
    echo "Creating state directory..."
    mkdir -p state
    echo "✓ State directory created"
else
    echo "✓ State directory exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the app locally:"
echo "  chainlit run app.py          # Chat UI on port 8000"
echo "  python auth_api.py           # Auth API on port 8001"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v --ignore=tests/test_auth.py"
echo ""
echo "To generate secrets:"
echo "  python generate_secrets.py"
echo ""
echo "To create admin user:"
echo "  python bootstrap_admin.py your_username"
