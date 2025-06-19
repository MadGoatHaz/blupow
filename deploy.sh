#!/bin/bash

# BluPow Integration Deployment Script
# This script automatically detects your Home Assistant installation type and deploys accordingly

set -e  # Exit on any error

echo "🚀 BluPow Integration Deployment Script"
echo "========================================"

# Function to detect Home Assistant installation type and set paths
detect_ha_environment() {
    echo "🔍 Detecting Home Assistant environment..."
    
    # Check for Home Assistant OS/Supervised (hassio)
    if [ -d "/usr/share/hassio" ]; then
        echo "📦 Detected: Home Assistant OS/Supervised"
        HA_CONFIG_DIR="/usr/share/hassio/homeassistant"
        HA_TYPE="hassio"
        RESTART_CMD="ha core restart"
        LOG_CMD="ha core logs"
        return 0
    fi
    
    # Check for Docker installation (common paths)
    DOCKER_PATHS=(
        "/home/madgoat/opt/homeassistant/config"
        "/home/homeassistant/.homeassistant"
        "/config"
        "/usr/share/homeassistant"
        "/opt/homeassistant/config"
    )
    
    for path in "${DOCKER_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo "🐳 Detected: Docker Home Assistant at $path"
            HA_CONFIG_DIR="$path"
            HA_TYPE="docker"
            RESTART_CMD="docker restart homeassistant"
            LOG_CMD="docker exec -it homeassistant ha core logs"
            return 0
        fi
    done
    
    # Check for Home Assistant Core (pip installation)
    CORE_PATHS=(
        "$HOME/.homeassistant"
        "/home/homeassistant/.homeassistant"
        "/srv/homeassistant"
    )
    
    for path in "${CORE_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo "🏠 Detected: Home Assistant Core at $path"
            HA_CONFIG_DIR="$path"
            HA_TYPE="core"
            RESTART_CMD="systemctl restart home-assistant"
            LOG_CMD="journalctl -u home-assistant -f"
            return 0
        fi
    done
    
    # If we get here, we couldn't detect the installation
    echo "❌ Could not automatically detect Home Assistant installation"
    echo "📋 Please manually specify your Home Assistant config directory:"
    echo "   Common locations:"
    echo "   - Docker: /home/user/homeassistant/config"
    echo "   - Home Assistant OS: /usr/share/hassio/homeassistant"
    echo "   - Core: ~/.homeassistant"
    echo ""
    read -p "Enter your Home Assistant config directory path: " HA_CONFIG_DIR
    
    if [ ! -d "$HA_CONFIG_DIR" ]; then
        echo "❌ Directory $HA_CONFIG_DIR does not exist"
        exit 1
    fi
    
    echo "📁 Using manually specified path: $HA_CONFIG_DIR"
    HA_TYPE="manual"
    RESTART_CMD="# Please restart Home Assistant manually"
    LOG_CMD="# Please check logs manually"
}

# Function to detect Docker environment specifically
detect_docker_details() {
    if [ "$HA_TYPE" = "docker" ]; then
        echo "🐳 Detecting Docker container details..."
        
        # Try to find the container name
        CONTAINER_NAMES=("homeassistant" "home-assistant" "hass" "ha")
        
        for name in "${CONTAINER_NAMES[@]}"; do
            if docker ps --format "table {{.Names}}" | grep -q "^$name$" 2>/dev/null; then
                DOCKER_CONTAINER="$name"
                echo "✅ Found Docker container: $DOCKER_CONTAINER"
                RESTART_CMD="docker restart $DOCKER_CONTAINER"
                LOG_CMD="docker exec -it $DOCKER_CONTAINER ha core logs"
                break
            fi
        done
        
        if [ -z "$DOCKER_CONTAINER" ]; then
            echo "⚠️  Could not detect Docker container name automatically"
            echo "📋 Available containers:"
            docker ps --format "table {{.Names}}\t{{.Image}}" | grep -i home || echo "   No Home Assistant containers found"
            echo ""
            read -p "Enter your Home Assistant Docker container name [homeassistant]: " DOCKER_CONTAINER
            DOCKER_CONTAINER=${DOCKER_CONTAINER:-homeassistant}
            RESTART_CMD="docker restart $DOCKER_CONTAINER"
            LOG_CMD="docker exec -it $DOCKER_CONTAINER ha core logs"
        fi
    fi
}

# Function to set ownership based on environment
set_proper_ownership() {
    case "$HA_TYPE" in
        "hassio")
            echo "🔐 Setting ownership for Home Assistant OS/Supervised..."
            chown -R root:root "$BLUPOW_DIR"
            ;;
        "docker")
            echo "🔐 Setting ownership for Docker installation..."
            # Try to detect the user running the container
            if [ -n "$DOCKER_CONTAINER" ]; then
                CONTAINER_USER=$(docker exec "$DOCKER_CONTAINER" whoami 2>/dev/null || echo "root")
                echo "📋 Container user: $CONTAINER_USER"
            fi
            chown -R $(whoami):$(whoami) "$BLUPOW_DIR"
            ;;
        "core")
            echo "🔐 Setting ownership for Home Assistant Core..."
            chown -R homeassistant:homeassistant "$BLUPOW_DIR" 2>/dev/null || chown -R $(whoami):$(whoami) "$BLUPOW_DIR"
            ;;
        *)
            echo "🔐 Setting default ownership..."
            chown -R $(whoami):$(whoami) "$BLUPOW_DIR"
            ;;
    esac
}

# Main deployment logic
main() {
    SOURCE_DIR="$(pwd)"
    
    # Detect environment
    detect_ha_environment
    detect_docker_details
    
    CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
    BLUPOW_DIR="$CUSTOM_COMPONENTS_DIR/blupow"
    
    echo ""
    echo "📋 Deployment Summary:"
    echo "   Installation Type: $HA_TYPE"
    echo "   Source directory: $SOURCE_DIR"
    echo "   Target directory: $BLUPOW_DIR"
    echo "   Restart command: $RESTART_CMD"
    echo ""
    
    # Check if we're running as root or with sudo (when needed)
    if [ "$HA_TYPE" = "hassio" ] && [ "$EUID" -ne 0 ]; then
        echo "❌ This script needs to be run with sudo for Home Assistant OS/Supervised"
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
    
    # Set proper permissions and ownership
    echo "🔐 Setting proper permissions..."
    set_proper_ownership
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
        echo "   1. Restart Home Assistant:"
        echo "      $RESTART_CMD"
        echo ""
        echo "   2. Check logs for any issues:"
        echo "      $LOG_CMD | grep blupow"
        echo ""
        echo "   3. Go to Settings > Devices & Services to configure BluPow"
        echo ""
        echo "🐛 For debugging, enable debug logging by adding to configuration.yaml:"
        echo "   logger:"
        echo "     logs:"
        echo "       custom_components.blupow: debug"
        echo ""
        
        # Offer to restart automatically for Docker
        if [ "$HA_TYPE" = "docker" ] && [ -n "$DOCKER_CONTAINER" ]; then
            echo "🔄 Would you like to restart Home Assistant now? (y/N)"
            read -p "Restart? " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "🔄 Restarting Home Assistant..."
                $RESTART_CMD
                echo "✅ Home Assistant restarted!"
            fi
        fi
    else
        echo "❌ Installation verification failed"
        exit 1
    fi
    
    echo "🎉 Deployment complete!"
}

# Run main function
main "$@" 