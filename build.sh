
#!/usr/bin/env bash

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromiumg