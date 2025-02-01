#!/usr/bin/env bash

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install -r requirements.txt

# Install system libraries
apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libdrm2 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libxkbcommon0 libasound2 \
    libatspi2.0-0

# Install Playwright dependencies
playwright install-deps

# Install Playwright browsers
playwright install