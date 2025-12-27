#!/bin/bash
set -e

echo "=== Setting up environment ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright

echo "=== Installing system dependencies ==="
apt-get update || true
apt-get install -y tesseract-ocr || true

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
python -m playwright install chromium

echo "=== Verifying Tesseract ==="
tesseract --version || echo "Tesseract not installed, OCR may fail"

echo "=== Setup complete! ==="
