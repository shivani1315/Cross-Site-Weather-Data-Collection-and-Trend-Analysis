#!/bin/bash
set -e

echo " Updating system packages..."
apt-get update

echo " Installing dependencies..."
apt-get install -y chromium-browser chromium-chromedriver libglib2.0-0 libnss3 libfontconfig1 unzip wget

echo " Installing Python libraries..."
pip install --upgrade selenium pandas matplotlib

echo " Configuring Chrome & Chromedriver..."
# Copy chromedriver to PATH
if [ -f /usr/lib/chromium-browser/chromedriver ]; then
    cp /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver
fi

# Optional: Clean up broken Chromium installs
apt-get remove -y chromium-browser || true
rm -rf /usr/lib/chromium-browser/ || true

# Install compatible Chrome + Chromedriver manually (version 122)
wget -q https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.57/linux64/chrome-linux64.zip
wget -q https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.57/linux64/chromedriver-linux64.zip
unzip -o chrome-linux64.zip
unzip -o chromedriver-linux64.zip
mv chrome-linux64 /opt/chrome
mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver

echo " Setup complete!"
