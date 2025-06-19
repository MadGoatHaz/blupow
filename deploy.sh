#!/bin/bash

# BluPow Integration Deployment Script
# This script copies the updated BluPow integration to Home Assistant

set -e  # Exit on any error

echo "🚀 BluPow Integration Deployment Script"
echo "========================================"

# Configuration
HA_CONFIG_DIR="/home/madgoat/opt/homeassistant/config"
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
BLUPOW_DIR="$CUSTOM_COMPONENTS_DIR/blupow"
SOURCE_DIR="$(pwd)"

echo "📍 Source directory: $SOURCE_DIR"
echo "📍 Target directory: $BLUPOW_DIR"

# Check if we're running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script needs to be run with sudo to access Home Assistant files"
    echo "   Usage: sudo ./deploy.sh"
    exit 1
fi

# Check if source directory looks correct
if [ ! -f "manifest.json" ] || [ ! -f "blupow_client.py" ]; then
    echo "❌ This doesn't appear to be the BluPow integration directory"
    echo "   Make sure you're running this script from the blupow project root"
    exit 1
fi

# Check if Home Assistant config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo "❌ Home Assistant config directory not found at $HA_CONFIG_DIR"
    echo "   Please update the HA_CONFIG_DIR variable in this script"
    exit 1
fi

# Create custom_components directory if it doesn't exist
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo "📁 Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Backup existing installation if it exists
if [ -d "$BLUPOW_DIR" ]; then
    BACKUP_DIR="$BLUPOW_DIR.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up existing installation to $BACKUP_DIR"
    mv "$BLUPOW_DIR" "$BACKUP_DIR"
fi

# Create new blupow directory
echo "📁 Creating new BluPow integration directory..."
mkdir -p "$BLUPOW_DIR"

# Copy all Python files and configuration
echo "📋 Copying integration files..."
cp -v *.py "$BLUPOW_DIR/"
cp -v *.json "$BLUPOW_DIR/"

# Copy translations directory if it exists
if [ -d "translations" ]; then
    echo "🌐 Copying translations..."
    cp -rv translations "$BLUPOW_DIR/"
fi

# Copy brand directory if it exists
if [ -d "brand" ]; then
    echo "🎨 Copying brand assets..."
    cp -rv brand "$BLUPOW_DIR/"
fi

# Set proper permissions
echo "🔐 Setting proper permissions..."
chown -R madgoat:madgoat "$BLUPOW_DIR"
chmod -R 644 "$BLUPOW_DIR"
find "$BLUPOW_DIR" -type d -exec chmod 755 {} \;

# Verify installation
echo "✅ Verifying installation..."
if [ -f "$BLUPOW_DIR/manifest.json" ] && [ -f "$BLUPOW_DIR/blupow_client.py" ]; then
    echo "✅ Installation successful!"
    echo ""
    echo "📝 Files copied:"
    ls -la "$BLUPOW_DIR"
    echo ""
    echo "🔄 Next steps:"
    echo "   1. Restart Home Assistant"
    echo "   2. Check logs for any issues:"
    echo "      docker exec -it homeassistant ha core logs | grep blupow"
    echo "   3. Go to Settings > Devices & Services to configure BluPow"
    echo ""
    echo "🐛 For debugging, enable debug logging by adding to configuration.yaml:"
    echo "   logger:"
    echo "     logs:"
    echo "       custom_components.blupow: debug"
else
    echo "❌ Installation verification failed"
    exit 1
fi

echo "🎉 Deployment complete!" 