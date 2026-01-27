#!/bin/bash

set -e

echo "=== Fixed AI Neko Companion Setup Script ==="

cd ~/cathyAI

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing ollama client and transformers (from default PyPI)..."
pip install ollama transformers

echo "Installing CPU-only PyTorch (from special index)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Cache emotion model (safe to re-run)
echo "Caching emotion model..."
python - <<EOF
from transformers import pipeline
print("Loading/caching emotion model...")
emotion_pipeline = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
result = emotion_pipeline("Nyaa~ I'm happy! 🐾")
print("Test:", result)
print("Ready!")
EOF

echo "Setup complete! Run: python companion.py"