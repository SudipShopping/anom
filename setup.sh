#!/bin/bash

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Checking Playwright installation..."
python -m playwright --version || echo "Playwright not found in path"

echo "Installing Playwright browsers..."
python -m playwright install chromium

echo "Installing Playwright dependencies..."
python -m playwright install-deps chromium

echo "Setup complete!"
