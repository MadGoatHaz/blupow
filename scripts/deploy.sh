#!/bin/bash

# BluPow Integration Deployment Script
# Automatically deploys BluPow integration to Home Assistant with testing tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INTEGRATION_NAME="blupow"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  BluPow Integration Deployment${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

detect_environment() {
    print_info "Detecting Home Assistant environment..."
    
    # Check for Home Assistant OS/Supervised
    if [[ -d "/usr/share/hassio" ]]; then
        HA_TYPE="supervised"
        CONFIG_PATH="/config"
        print_success "Detected Home Assistant Supervised"
        return 0
    fi
    
    # Check for Docker container
    if [[ -f "/.dockerenv" ]]; then
        HA_TYPE="container"
        CONFIG_PATH="/config"
        print_success "Detected Home Assistant Container"
        return 0
    fi
    
    # Check for common container paths
    if [[ -d "/config" && -f "/config/configuration.yaml" ]]; then
        HA_TYPE="container"
        CONFIG_PATH="/config"
        print_success "Detected Home Assistant in container environment"
        return 0
    fi
    
    # Check for Docker from outside
    if command -v docker &> /dev/null; then
        if docker ps --format "table {{.Names}}" | grep -q "homeassistant"; then
            HA_TYPE="external_docker"
            print_success "Detected external Docker Home Assistant"
            
            # Try to find config path
            CONFIG_MOUNT=$(docker inspect homeassistant --format='{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo "")
            if [[ -n "$CONFIG_MOUNT" ]]; then
                CONFIG_PATH="$CONFIG_MOUNT"
                print_info "Found config path: $CONFIG_PATH"
            else
                print_warning "Could not detect config path automatically"
                read -p "Please enter your Home Assistant config path: " CONFIG_PATH
            fi
            return 0
        fi
    fi
    
    # Manual configuration
    print_warning "Could not auto-detect Home Assistant environment"
    echo "Please select your environment:"
    echo "1) Home Assistant OS/Supervised"
    echo "2) Home Assistant Container"
    echo "3) Home Assistant Core (venv)"
    echo "4) Custom path"
    
    read -p "Enter choice [1-4]: " choice
    
    case $choice in
        1)
            HA_TYPE="supervised"
            CONFIG_PATH="/config"
            ;;
        2)
            HA_TYPE="container"
            CONFIG_PATH="/config"
            ;;
        3)
            HA_TYPE="core"
            read -p "Enter your Home Assistant config directory: " CONFIG_PATH
            ;;
        4)
            HA_TYPE="custom"
            read -p "Enter your Home Assistant config directory: " CONFIG_PATH
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

validate_config_path() {
    print_info "Validating config path: $CONFIG_PATH"
    
    if [[ ! -d "$CONFIG_PATH" ]]; then
        print_error "Config directory does not exist: $CONFIG_PATH"
        return 1
    fi
    
    if [[ ! -f "$CONFIG_PATH/configuration.yaml" ]]; then
        print_error "configuration.yaml not found in: $CONFIG_PATH"
        return 1
    fi
    
    print_success "Config path validated"
    return 0
}

deploy_integration() {
    print_info "Deploying BluPow integration..."
    
    CUSTOM_COMPONENTS_DIR="$CONFIG_PATH/custom_components"
    INTEGRATION_DIR="$CUSTOM_COMPONENTS_DIR/$INTEGRATION_NAME"
    BACKUP_DIR="$CONFIG_PATH/backups"
    
    # Create custom_components directory if it doesn't exist
    if [[ ! -d "$CUSTOM_COMPONENTS_DIR" ]]; then
        print_info "Creating custom_components directory..."
        mkdir -p "$CUSTOM_COMPONENTS_DIR"
    fi
    
    # Create backups directory if it doesn't exist
    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_info "Creating backups directory..."
        mkdir -p "$BACKUP_DIR"
    fi
    
    # Create integration directory
    if [[ -d "$INTEGRATION_DIR" ]]; then
        print_warning "Existing integration found. Backing up..."
        mv "$INTEGRATION_DIR" "$BACKUP_DIR/$INTEGRATION_NAME.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$INTEGRATION_DIR"
    
    # Copy core integration files
    print_info "Copying core integration files..."
    
    CORE_FILES=(
        "__init__.py"
        "blupow_client.py"
        "config_flow.py"
        "const.py"
        "coordinator.py"
        "diagnostics.py"
        "manifest.json"
        "sensor.py"
        "strings.json"
    )
    
    for file in "${CORE_FILES[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            cp "$PROJECT_ROOT/$file" "$INTEGRATION_DIR/"
            print_success "Copied $file"
        else
            print_warning "File not found: $file"
        fi
    done
    
    # Copy translations
    if [[ -d "$PROJECT_ROOT/translations" ]]; then
        cp -r "$PROJECT_ROOT/translations" "$INTEGRATION_DIR/"
        print_success "Copied translations"
    fi
    
    # Copy branding
    if [[ -d "$PROJECT_ROOT/brand" ]]; then
        cp -r "$PROJECT_ROOT/brand" "$INTEGRATION_DIR/"
        print_success "Copied branding assets"
    fi
}

deploy_testing_tools() {
    print_info "Deploying testing and diagnostic tools..."
    
    INTEGRATION_DIR="$CONFIG_PATH/custom_components/$INTEGRATION_NAME"
    
    # Copy tests directory
    if [[ -d "$PROJECT_ROOT/tests" ]]; then
        cp -r "$PROJECT_ROOT/tests" "$INTEGRATION_DIR/"
        print_success "Copied testing framework"
    fi
    
    # Copy scripts
    if [[ -d "$PROJECT_ROOT/scripts" ]]; then
        cp -r "$PROJECT_ROOT/scripts" "$INTEGRATION_DIR/"
        print_success "Copied utility scripts"
    fi
    
    # Copy documentation
    if [[ -d "$PROJECT_ROOT/docs" ]]; then
        cp -r "$PROJECT_ROOT/docs" "$INTEGRATION_DIR/"
        print_success "Copied documentation"
    fi
    
    # Copy info directory
    if [[ -d "$PROJECT_ROOT/info" ]]; then
        cp -r "$PROJECT_ROOT/info" "$INTEGRATION_DIR/"
        print_success "Copied reference information"
    fi
    
    # Copy project structure documentation
    if [[ -f "$PROJECT_ROOT/PROJECT_STRUCTURE.md" ]]; then
        cp "$PROJECT_ROOT/PROJECT_STRUCTURE.md" "$INTEGRATION_DIR/"
        print_success "Copied project structure documentation"
    fi
}

set_permissions() {
    print_info "Setting appropriate permissions..."
    
    INTEGRATION_DIR="$CONFIG_PATH/custom_components/$INTEGRATION_NAME"
    
    # Make scripts executable
    if [[ -d "$INTEGRATION_DIR/scripts" ]]; then
        chmod +x "$INTEGRATION_DIR/scripts"/*.sh 2>/dev/null || true
        print_success "Set script permissions"
    fi
    
    # Make test files executable
    if [[ -d "$INTEGRATION_DIR/tests" ]]; then
        find "$INTEGRATION_DIR/tests" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
        print_success "Set test file permissions"
    fi
}

show_next_steps() {
    echo
    print_success "Deployment completed successfully!"
    echo
    print_info "Next steps:"
    echo
    echo "1. 🔄 Restart Home Assistant to load the integration"
    echo
    echo "2. 🧪 Test your setup:"
    if [[ "$HA_TYPE" == "external_docker" ]]; then
        echo "   docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/tests/diagnostics/blupow_testing_suite.py"
    else
        echo "   python3 /config/custom_components/blupow/tests/diagnostics/blupow_testing_suite.py"
    fi
    echo
    echo "3. ⚙️  Configure the integration:"
    echo "   - Go to Settings → Devices & Services"
    echo "   - Click '+ Add Integration'"
    echo "   - Search for 'BluPow'"
    echo "   - Follow the configuration wizard"
    echo
    echo "4. 🔧 If you have Bluetooth issues:"
    echo "   - Check docs/troubleshooting/TROUBLESHOOTING.md"
    echo "   - Run scripts/setup_container_bluetooth.sh"
    echo
    print_info "Integration deployed to: $CONFIG_PATH/custom_components/$INTEGRATION_NAME"
}

restart_homeassistant() {
    print_info "Attempting to restart Home Assistant..."
    
    case $HA_TYPE in
        "supervised")
            if command -v ha &> /dev/null; then
                ha core restart
                print_success "Home Assistant restart initiated"
            else
                print_warning "Could not restart automatically. Please restart manually."
            fi
            ;;
        "external_docker")
            if docker restart homeassistant &> /dev/null; then
                print_success "Home Assistant container restarted"
            else
                print_warning "Could not restart container. Please restart manually."
            fi
            ;;
        *)
            print_warning "Please restart Home Assistant manually"
            ;;
    esac
}

main() {
    print_header
    
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    detect_environment
    
    if ! validate_config_path; then
        exit 1
    fi
    
    deploy_integration
    deploy_testing_tools
    set_permissions
    
    echo
    read -p "Would you like to restart Home Assistant now? (y/N): " restart_choice
    if [[ "$restart_choice" =~ ^[Yy]$ ]]; then
        restart_homeassistant
    fi
    
    show_next_steps
}

# Run main function
main "$@" 