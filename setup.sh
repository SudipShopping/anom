#!/bin/bash

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing system dependencies for Chromium..."
apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 || true

echo "Installing Playwright browsers..."
python -m playwright install chromium

echo "Installing Playwright system dependencies..."
python -m playwright install-deps chromium

echo "Setup complete! Chromium installed at:"
ls -la ~/.cache/ms-playwright/ || ls -la /opt/render/.cache/ms-playwright/ || echo "Checking paths..."
