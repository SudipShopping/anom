#!/bin/bash
set -e

echo "=== Setting up environment ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
python -m playwright install chromium

echo "=== Verifying installation ==="
ls -la $PLAYWRIGHT_BROWSERS_PATH/chromium-*/ || echo "Chromium not found"

echo "=== Setup complete! ==="
