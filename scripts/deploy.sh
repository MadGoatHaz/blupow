#!/bin/bash

# BluPow Home Assistant Integration Deployer
#
# This script safely deploys the 'blupow' custom_component to a
# Home Assistant configuration directory.
#
# It performs the following steps:
#   1. Auto-detects the Home Assistant '/config' volume path from Docker.
#   2. Creates a timestamped backup of any existing 'blupow' integration.
#   3. Copies the new integration code from this repository.
#   4. Sets the correct file ownership to match the parent directory.

set -e

# --- Configuration ---
# The root of the blupow project git repository.
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
# The source directory of the integration we want to deploy.
SOURCE_DIR="$PROJECT_ROOT/custom_components/blupow"
# The name of the integration directory.
INTEGRATION_NAME="blupow"

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Functions ---
print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}  BluPow Home Assistant Integration Deployer ${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# --- Script Logic ---
print_header

# 1. Find the HA Config Directory
print_info "Attempting to detect Home Assistant config directory from Docker..."
HA_CONFIG_PATH=$(docker inspect homeassistant --format='{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo "")

if [[ -z "$HA_CONFIG_PATH" ]]; then
    print_warning "Could not auto-detect Home Assistant config path."
    read -p "Please enter the absolute path to your Home Assistant 'config' directory: " HA_CONFIG_PATH
    if [[ -z "$HA_CONFIG_PATH" ]]; then
        print_error "Config path cannot be empty."
    fi
fi
print_success "Using HA Config Directory: $HA_CONFIG_PATH"

# 2. Define target directory
TARGET_DIR="$HA_CONFIG_PATH/custom_components/$INTEGRATION_NAME"
print_info "Target deployment directory: $TARGET_DIR"

# 3. Backup existing deployment
if [ -d "$TARGET_DIR" ]; then
    print_warning "Existing integration found. Creating a backup..."
    BACKUP_NAME="$HA_CONFIG_PATH/custom_components/$INTEGRATION_NAME.bak.$(date +%Y%m%d-%H%M%S)"
    if sudo mv "$TARGET_DIR" "$BACKUP_NAME"; then
        print_success "Backup created at: $BACKUP_NAME"
    else
        print_error "Failed to create backup. You may need to enter your password for 'sudo'. Aborting."
    fi
fi

# 4. Deploy new code
print_info "Deploying new integration code from $SOURCE_DIR..."
if sudo cp -r "$SOURCE_DIR" "$TARGET_DIR"; then
    print_success "Successfully copied integration files."
else
    print_error "Failed to copy integration files. Aborting."
fi

# 5. Set Permissions
print_info "Setting ownership permissions to match parent directory..."
PARENT_UID=$(stat -c '%u' "$HA_CONFIG_PATH/custom_components")
PARENT_GID=$(stat -c '%g' "$HA_CONFIG_PATH/custom_components")
if sudo chown -R "$PARENT_UID":"$PARENT_GID" "$TARGET_DIR"; then
    print_success "Permissions set successfully."
else
    print_warning "Could not set permissions. This might be okay."
fi

echo
print_success "Deployment complete!"
print_warning "You must RESTART Home Assistant for the changes to take effect."
echo 