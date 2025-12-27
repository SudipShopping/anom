#!/bin/bash
set -e

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
python -m playwright install chromium

echo "=== Installing Playwright system dependencies ==="
python -m playwright install-deps chromium

echo "=== Verifying Playwright installation ==="
python -m playwright --version

echo "=== Checking Chromium path ==="
ls -la ~/.cache/ms-playwright/ 2>/dev/null || ls -la /opt/render/.cache/ms-playwright/ 2>/dev/null || echo "Chromium path check..."

echo "=== Setup complete! ==="
