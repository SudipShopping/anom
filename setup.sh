#!/bin/bash

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium

echo "Installing Playwright dependencies..."
playwright install-deps chromium

echo "Setup complete!"
