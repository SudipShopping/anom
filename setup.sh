#!/bin/bash

pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium --with-deps || python -m playwright install chromium
echo "Setup complete!"
