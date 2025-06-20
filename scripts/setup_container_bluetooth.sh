#!/bin/bash

# BluPow Container Bluetooth Setup Script
# Automatically configures Docker containers for Bluetooth access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="homeassistant"
CONFIG_PATH="/path/to/your/homeassistant/config"
TIMEZONE="America/New_York"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  BluPow Container Setup${NC}"
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

check_requirements() {
    print_info "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check if AppArmor is available
    if ! command -v apparmor_parser &> /dev/null; then
        print_warning "AppArmor tools not found. Installing..."
        apt-get update && apt-get install -y apparmor-utils
    fi
    
    # Check if bluetoothctl is available
    if ! command -v bluetoothctl &> /dev/null; then
        print_warning "Bluetooth tools not found. Installing..."
        apt-get update && apt-get install -y bluetooth bluez
    fi
    
    print_success "System requirements satisfied"
}

detect_container() {
    print_info "Detecting Home Assistant container..."
    
    # Try to find the container
    CONTAINER_CANDIDATES=("homeassistant" "home-assistant" "hass" "ha")
    
    for candidate in "${CONTAINER_CANDIDATES[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${candidate}$"; then
            CONTAINER_NAME="$candidate"
            print_success "Found container: $CONTAINER_NAME"
            return 0
        fi
    done
    
    # If not found, list available containers
    print_warning "Could not auto-detect Home Assistant container"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    echo
    read -p "Enter your Home Assistant container name: " CONTAINER_NAME
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Container '$CONTAINER_NAME' not found or not running"
        exit 1
    fi
}

get_config_path() {
    print_info "Detecting Home Assistant config path..."
    
    # Try to get config path from container mounts
    CONFIG_MOUNT=$(docker inspect "$CONTAINER_NAME" --format='{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo "")
    
    if [[ -n "$CONFIG_MOUNT" && -d "$CONFIG_MOUNT" ]]; then
        CONFIG_PATH="$CONFIG_MOUNT"
        print_success "Detected config path: $CONFIG_PATH"
    else
        read -p "Enter your Home Assistant config directory path: " CONFIG_PATH
        if [[ ! -d "$CONFIG_PATH" ]]; then
            print_error "Config directory does not exist: $CONFIG_PATH"
            exit 1
        fi
    fi
}

diagnose_current_issue() {
    print_info "Diagnosing current Bluetooth access issues..."
    
    # Check if container is running
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Container is not running"
        return 1
    fi
    
    # Test Bluetooth access inside container
    print_info "Testing Bluetooth access inside container..."
    
    # Test 1: Check if BlueZ is accessible
    if docker exec -it "$CONTAINER_NAME" python3 -c "import bluetooth; print('BlueZ accessible')" 2>/dev/null; then
        print_success "BlueZ library is accessible"
    else
        print_warning "BlueZ library access failed"
    fi
    
    # Test 2: Check D-Bus access
    if docker exec -it "$CONTAINER_NAME" python3 -c "
import dbus
try:
    bus = dbus.SystemBus()
    print('D-Bus system bus accessible')
except Exception as e:
    print(f'D-Bus access failed: {e}')
" 2>/dev/null; then
        print_success "D-Bus system bus is accessible"
    else
        print_warning "D-Bus system bus access failed"
    fi
    
    # Test 3: Check AppArmor denials
    print_info "Checking for AppArmor denials..."
    if dmesg | grep -i apparmor | grep -i denied | tail -5; then
        print_warning "Found AppArmor denials (see above)"
    else
        print_info "No recent AppArmor denials found"
    fi
    
    # Test 4: Check container security options
    print_info "Checking container security configuration..."
    SECURITY_OPTS=$(docker inspect "$CONTAINER_NAME" --format='{{.HostConfig.SecurityOpt}}')
    if [[ "$SECURITY_OPTS" == "[]" || "$SECURITY_OPTS" == "<no value>" ]]; then
        print_warning "No custom security options configured"
    else
        print_info "Current security options: $SECURITY_OPTS"
    fi
}

create_apparmor_profile() {
    print_info "Creating custom AppArmor profile for Home Assistant..."
    
    PROFILE_PATH="/etc/apparmor.d/docker.homeassistant.bluetooth"
    
    cat > "$PROFILE_PATH" << 'EOF'
#include <tunables/global>

profile docker.homeassistant.bluetooth flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/python>
  
  # Allow network access
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,
  network netlink raw,
  network bluetooth,
  
  # Allow D-Bus access for Bluetooth
  dbus (send,receive) bus=system,
  
  # Allow Bluetooth device access
  /dev/rfkill rw,
  /sys/class/bluetooth/ r,
  /sys/class/bluetooth/** r,
  /sys/devices/virtual/bluetooth/ r,
  /sys/devices/virtual/bluetooth/** r,
  /sys/devices/pci*/**/bluetooth/ r,
  /sys/devices/pci*/**/bluetooth/** r,
  /sys/devices/platform/**/bluetooth/ r,
  /sys/devices/platform/**/bluetooth/** r,
  
  # Allow proc access for Bluetooth
  @{PROC}/sys/net/core/rmem_default r,
  @{PROC}/sys/net/core/rmem_max r,
  @{PROC}/sys/net/core/wmem_default r,
  @{PROC}/sys/net/core/wmem_max r,
  
  # Allow Home Assistant specific paths
  /config/ r,
  /config/** rw,
  /usr/src/homeassistant/ r,
  /usr/src/homeassistant/** r,
  /usr/local/lib/python*/** r,
  
  # Allow Python execution
  /usr/bin/python3 ix,
  /usr/bin/python3.* ix,
  
  # Allow shared libraries
  /lib/x86_64-linux-gnu/** mr,
  /usr/lib/x86_64-linux-gnu/** mr,
  /usr/local/lib/** mr,
  
  # Allow temporary files
  /tmp/** rw,
  /var/tmp/** rw,
  
  # Capabilities needed for Bluetooth
  capability net_admin,
  capability net_raw,
  capability sys_admin,
  capability dac_override,
  capability setgid,
  capability setuid,
  
  # Deny dangerous capabilities
  deny capability sys_module,
  deny capability sys_boot,
  deny capability sys_time,
}
EOF

    # Load the profile
    print_info "Loading AppArmor profile..."
    if apparmor_parser -r "$PROFILE_PATH"; then
        print_success "AppArmor profile loaded successfully"
    else
        print_error "Failed to load AppArmor profile"
        return 1
    fi
}

setup_solution_1_privileged() {
    print_info "Setting up Solution 1: Privileged Container (Least Secure)"
    
    print_warning "This solution runs the container in privileged mode"
    print_warning "This reduces security but provides full hardware access"
    
    read -p "Continue with privileged mode? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        return 1
    fi
    
    # Stop the container
    print_info "Stopping Home Assistant container..."
    docker stop "$CONTAINER_NAME"
    
    # Get current container configuration
    IMAGE=$(docker inspect "$CONTAINER_NAME" --format='{{.Config.Image}}')
    
    # Remove old container
    print_info "Removing old container..."
    docker rm "$CONTAINER_NAME"
    
    # Create new privileged container
    print_info "Creating new privileged container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --privileged \
        --restart=unless-stopped \
        -e TZ="$TIMEZONE" \
        -v "$CONFIG_PATH":/config \
        -v /run/dbus:/run/dbus:ro \
        --network=host \
        "$IMAGE"
    
    print_success "Privileged container created"
    print_warning "Security level: LOW (privileged mode)"
}

setup_solution_2_capabilities() {
    print_info "Setting up Solution 2: Specific Capabilities (Medium Security)"
    
    # Stop the container
    print_info "Stopping Home Assistant container..."
    docker stop "$CONTAINER_NAME"
    
    # Get current container configuration
    IMAGE=$(docker inspect "$CONTAINER_NAME" --format='{{.Config.Image}}')
    
    # Remove old container
    print_info "Removing old container..."
    docker rm "$CONTAINER_NAME"
    
    # Create new container with specific capabilities
    print_info "Creating container with Bluetooth capabilities..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart=unless-stopped \
        -e TZ="$TIMEZONE" \
        -v "$CONFIG_PATH":/config \
        -v /run/dbus:/run/dbus:ro \
        -v /dev/bus/usb:/dev/bus/usb \
        --device=/dev/ttyUSB0 \
        --device=/dev/ttyACM0 \
        --cap-add=NET_ADMIN \
        --cap-add=NET_RAW \
        --cap-add=SYS_ADMIN \
        --network=host \
        "$IMAGE"
    
    print_success "Container created with specific capabilities"
    print_info "Security level: MEDIUM (specific capabilities)"
}

setup_solution_3_apparmor() {
    print_info "Setting up Solution 3: Custom AppArmor Profile (High Security)"
    
    # Create the AppArmor profile
    create_apparmor_profile
    
    # Stop the container
    print_info "Stopping Home Assistant container..."
    docker stop "$CONTAINER_NAME"
    
    # Get current container configuration
    IMAGE=$(docker inspect "$CONTAINER_NAME" --format='{{.Config.Image}}')
    
    # Remove old container
    print_info "Removing old container..."
    docker rm "$CONTAINER_NAME"
    
    # Create new container with custom AppArmor profile
    print_info "Creating container with custom AppArmor profile..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart=unless-stopped \
        -e TZ="$TIMEZONE" \
        -v "$CONFIG_PATH":/config \
        -v /run/dbus:/run/dbus:ro \
        --device=/dev/ttyUSB0 \
        --device=/dev/ttyACM0 \
        --cap-add=NET_ADMIN \
        --cap-add=NET_RAW \
        --security-opt apparmor=docker.homeassistant.bluetooth \
        --network=host \
        "$IMAGE"
    
    print_success "Container created with custom AppArmor profile"
    print_info "Security level: HIGH (custom AppArmor profile)"
}

setup_solution_4_disable_apparmor() {
    print_info "Setting up Solution 4: Disable AppArmor (Development Only)"
    
    print_warning "This solution disables AppArmor for the container"
    print_warning "This should ONLY be used for development/testing"
    
    read -p "Continue with AppArmor disabled? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        return 1
    fi
    
    # Stop the container
    print_info "Stopping Home Assistant container..."
    docker stop "$CONTAINER_NAME"
    
    # Get current container configuration
    IMAGE=$(docker inspect "$CONTAINER_NAME" --format='{{.Config.Image}}')
    
    # Remove old container
    print_info "Removing old container..."
    docker rm "$CONTAINER_NAME"
    
    # Create new container with AppArmor disabled
    print_info "Creating container with AppArmor disabled..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart=unless-stopped \
        -e TZ="$TIMEZONE" \
        -v "$CONFIG_PATH":/config \
        -v /run/dbus:/run/dbus:ro \
        --device=/dev/ttyUSB0 \
        --device=/dev/ttyACM0 \
        --cap-add=NET_ADMIN \
        --cap-add=NET_RAW \
        --security-opt apparmor=unconfined \
        --network=host \
        "$IMAGE"
    
    print_success "Container created with AppArmor disabled"
    print_warning "Security level: VERY LOW (AppArmor disabled)"
}

test_bluetooth_access() {
    print_info "Testing Bluetooth access in new container..."
    
    # Wait for container to start
    sleep 5
    
    # Test Bluetooth scanning
    print_info "Testing Bluetooth device scanning..."
    
    TEST_SCRIPT='
import asyncio
import logging
from bleak import BleakScanner

async def test_scan():
    try:
        print("Starting Bluetooth scan test...")
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"Found {len(devices)} Bluetooth devices:")
        for device in devices[:5]:  # Show first 5 devices
            print(f"  - {device.address}: {device.name or \"Unknown\"}")
        return len(devices) > 0
    except Exception as e:
        print(f"Bluetooth scan failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_scan())
    exit(0 if result else 1)
'
    
    # Run the test inside the container
    if docker exec -it "$CONTAINER_NAME" python3 -c "$TEST_SCRIPT"; then
        print_success "Bluetooth access test PASSED"
        return 0
    else
        print_error "Bluetooth access test FAILED"
        return 1
    fi
}

show_menu() {
    echo
    print_info "Choose a setup solution:"
    echo
    echo "1) Privileged Container (Least Secure, Most Compatible)"
    echo "   - Runs container in privileged mode"
    echo "   - Full hardware access"
    echo "   - Security: LOW"
    echo
    echo "2) Specific Capabilities (Medium Security, Good Compatibility)"
    echo "   - Adds only necessary Linux capabilities"
    echo "   - Balanced security and functionality"
    echo "   - Security: MEDIUM"
    echo
    echo "3) Custom AppArmor Profile (High Security, May Need Tuning)"
    echo "   - Creates custom security profile"
    echo "   - Allows only necessary operations"
    echo "   - Security: HIGH"
    echo
    echo "4) Disable AppArmor (Development Only)"
    echo "   - Disables AppArmor for container"
    echo "   - For testing/development only"
    echo "   - Security: VERY LOW"
    echo
    echo "5) Diagnose Current Issues"
    echo "   - Analyze current container setup"
    echo "   - Identify specific problems"
    echo
    echo "0) Exit"
    echo
}

main() {
    print_header
    
    check_requirements
    detect_container
    get_config_path
    
    while true; do
        show_menu
        read -p "Enter your choice [0-5]: " choice
        
        case $choice in
            1)
                if setup_solution_1_privileged; then
                    test_bluetooth_access
                fi
                ;;
            2)
                if setup_solution_2_capabilities; then
                    test_bluetooth_access
                fi
                ;;
            3)
                if setup_solution_3_apparmor; then
                    test_bluetooth_access
                fi
                ;;
            4)
                if setup_solution_4_disable_apparmor; then
                    test_bluetooth_access
                fi
                ;;
            5)
                diagnose_current_issue
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 0-5."
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Run main function
main "$@" 