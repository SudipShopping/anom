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

echo "=== Verifying Gemini API Key ==="
python -c "import os; print('✅ GEMINI_API_KEY:', 'SET' if os.environ.get('GEMINI_API_KEY') else 'NOT SET')"

echo "=== Setup complete! ==="
