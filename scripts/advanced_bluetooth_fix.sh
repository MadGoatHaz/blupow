#!/bin/bash

# Advanced BluPow Bluetooth Fix Script
# ====================================
# Based on comprehensive Docker+AppArmor+Bluetooth guide
# This script creates a proper AppArmor profile and Docker configuration

set -e

echo "🧙‍♂️ Advanced BluPow Bluetooth Fix - Now with REAL Magic!"
echo "========================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

CONTAINER_NAME="homeassistant"

echo "🔍 Step 1: Analyzing Current Bluetooth Setup"
echo "----------------------------------------"

# Check Bluetooth service
echo "📡 Bluetooth Service Status:"
systemctl is-active bluetooth && echo "✅ Bluetooth service is running" || echo "❌ Bluetooth service not running"

# Check HCI devices
echo ""
echo "🎯 HCI Device Analysis:"
if hciconfig -a | grep -q "hci0"; then
    echo "✅ HCI device hci0 found"
    HCI_DEVICE="hci0"
else
    echo "❌ No HCI device found"
    exit 1
fi

# Check device files
echo ""
echo "📁 Device Files Present:"
for device in /dev/vhci /dev/uhid /dev/hidraw*; do
    if [ -e "$device" ]; then
        echo "✅ $device exists"
        ls -la "$device"
    else
        echo "❌ $device not found"
    fi
done

echo ""
echo "🏗️  Step 2: Creating Custom AppArmor Profile"
echo "-------------------------------------------"

# Create the AppArmor profile
APPARMOR_PROFILE="/etc/apparmor.d/docker-homeassistant-bluetooth"

cat > "$APPARMOR_PROFILE" << 'EOF'
#include <tunables/global>

profile docker-homeassistant-bluetooth flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/dbus>
  
  # Network capabilities for Bluetooth
  capability net_admin,
  capability net_raw,
  capability dac_override,
  capability sys_admin,

  # Bluetooth device access
  /dev/vhci rw,
  /dev/uhid rw,
  /dev/hidraw* rw,
  /sys/class/bluetooth/ r,
  /sys/class/bluetooth/** r,
  /sys/devices/pci*/*/usb*/*/bluetooth/hci*/** r,

  # D-Bus system bus access
  /run/dbus/system_bus_socket rw,
  dbus bus=system,

  # Proc filesystem access
  @{PROC}/sys/kernel/random/uuid r,
  @{PROC}/sys/net/core/somaxconn r,
  
  # Home Assistant specific paths
  /config/** rw,
  /usr/local/lib/python*/site-packages/** r,
  /usr/local/lib/python*/site-packages/**/*.so mr,
  /usr/local/bin/python* ix,
  
  # Bluetooth utilities
  /usr/bin/bluetoothctl ix,
  /usr/bin/hciconfig ix,
  /usr/bin/hcitool ix,
  /usr/bin/gdbus ix,
  
  # Python and libraries
  /usr/bin/python* ix,
  /usr/lib/python*/** r,
  /usr/lib/python*/**/*.so mr,
  
  # Temporary files
  /tmp/** rw,
  /var/tmp/** rw,
  
  # Network access
  network,
  network inet,
  network inet6,
  network packet,
  network bluetooth,
  
  # Allow signals
  signal,
  
  # File operations
  file,
  
  # Allow most operations in /usr/local (where HA is installed)
  /usr/local/** r,
  /usr/local/lib/python*/site-packages/**/*.so mr,
  
  # Allow access to shared libraries
  /lib/x86_64-linux-gnu/** r,
  /lib64/** r,
  /usr/lib/x86_64-linux-gnu/** r,
  
  # Allow Python execution
  /usr/bin/python* ix,
  /usr/local/bin/python* ix,
}
EOF

echo "✅ AppArmor profile created: $APPARMOR_PROFILE"

# Load the AppArmor profile
echo "🔄 Loading AppArmor profile..."
apparmor_parser -r "$APPARMOR_PROFILE"

# Check if profile loaded
if aa-status | grep -q "docker-homeassistant-bluetooth"; then
    echo "✅ AppArmor profile loaded successfully"
else
    echo "❌ Failed to load AppArmor profile"
    exit 1
fi

echo ""
echo "🛑 Step 3: Stopping and Backing Up Current Container"
echo "------------------------------------------------"

# Stop current container
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Stopping $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME"
else
    echo "Container $CONTAINER_NAME not running"
fi

# Backup current container
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo "📦 Creating backup..."
    docker commit "$CONTAINER_NAME" "homeassistant-backup-advanced-$(date +%Y%m%d-%H%M%S)"
    
    echo "🗑️ Removing old container..."
    docker rm "$CONTAINER_NAME"
else
    echo "No existing container to backup"
fi

echo ""
echo "🚀 Step 4: Starting Home Assistant with Advanced Bluetooth Config"
echo "---------------------------------------------------------------"

# Start container with proper configuration
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart=unless-stopped \
  --privileged \
  --network=host \
  --security-opt apparmor=docker-homeassistant-bluetooth \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --cap-add=DAC_OVERRIDE \
  --cap-add=SYS_ADMIN \
  --device=/dev/vhci:/dev/vhci \
  --device=/dev/uhid:/dev/uhid \
  $(find /dev -name "hidraw*" -exec echo "--device={}:{}" \;) \
  -e TZ=America/Denver \
  -e DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket \
  -v /home/madgoat/opt/homeassistant/config:/config \
  -v /etc/localtime:/etc/localtime:ro \
  -v /run/dbus:/run/dbus:rw \
  -v /sys/class/bluetooth:/sys/class/bluetooth:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  homeassistant/home-assistant:latest

echo ""
echo "⏳ Step 5: Waiting for Home Assistant to Initialize"
echo "-----------------------------------------------"
echo "Waiting 30 seconds for full startup..."
sleep 30

# Check container status
echo ""
echo "🔍 Container Status:"
docker ps | grep "$CONTAINER_NAME" || echo "❌ Container not running"

echo ""
echo "🧪 Step 6: Advanced Bluetooth Testing"
echo "------------------------------------"

# Test 1: Check device access
echo "Test 1: Device Access"
docker exec "$CONTAINER_NAME" ls -la /dev/vhci /dev/uhid /dev/hidraw* 2>/dev/null || echo "❌ Device access failed"

# Test 2: Check D-Bus access
echo ""
echo "Test 2: D-Bus Access"
docker exec "$CONTAINER_NAME" python3 -c "
import dbus
try:
    bus = dbus.SystemBus()
    print('✅ D-Bus system bus accessible')
except Exception as e:
    print(f'❌ D-Bus access failed: {e}')
" 2>/dev/null || echo "❌ D-Bus test failed"

# Test 3: Check Bluetooth scanning capability
echo ""
echo "Test 3: Bluetooth Scanning"
docker exec "$CONTAINER_NAME" python3 -c "
import asyncio
from bleak import BleakScanner

async def test_scan():
    try:
        print('🔍 Testing Bluetooth scanning...')
        devices = await BleakScanner.discover(timeout=5.0)
        print(f'✅ Bluetooth scan successful - found {len(devices)} devices')
        
        # Look for our target device
        for device in devices:
            if device.address.upper() == 'D8:B6:73:BF:4F:75':
                print(f'🎯 Found target device: {device.name} ({device.address})')
                return True
        
        print('⚠️  Target device not found in scan, but scanning works')
        return True
    except Exception as e:
        print(f'❌ Bluetooth scan failed: {e}')
        return False

try:
    result = asyncio.run(test_scan())
    exit(0 if result else 1)
except Exception as e:
    print(f'❌ Scan test failed: {e}')
    exit(1)
" 

SCAN_RESULT=$?

# Test 4: Direct connection test
echo ""
echo "Test 4: Direct Connection Test"
docker exec "$CONTAINER_NAME" python3 -c "
import asyncio
from bleak import BleakClient

async def test_connection():
    try:
        print('🔗 Testing direct connection to D8:B6:73:BF:4F:75...')
        async with BleakClient('D8:B6:73:BF:4F:75', timeout=10.0) as client:
            print('✅ Connection successful!')
            print(f'   Connected: {client.is_connected}')
            print('   🎉 BluPow integration should now work!')
            return True
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

try:
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
except Exception as e:
    print(f'❌ Connection test failed: {e}')
    exit(1)
"

CONNECTION_RESULT=$?

echo ""
echo "📊 Step 7: Results Summary"
echo "========================"

if [ $CONNECTION_RESULT -eq 0 ]; then
    echo "🎉 SUCCESS! Home Assistant can now connect to Bluetooth devices!"
    echo ""
    echo "✅ What's Working:"
    echo "   - Custom AppArmor profile: docker-homeassistant-bluetooth"
    echo "   - Proper device access: /dev/vhci, /dev/uhid, /dev/hidraw*"  
    echo "   - D-Bus communication enabled"
    echo "   - Bluetooth scanning and connection working"
    echo ""
    echo "🔧 Your BluPow Integration Status:"
    echo "   - All 22 sensors should now show real data"
    echo "   - Connection status should show 'Connected'"
    echo "   - Data updates every 30 seconds"
    echo ""
    echo "🏠 Next Steps:"
    echo "   1. Check Home Assistant web interface"
    echo "   2. Go to Settings → Devices & Services → BluPow"
    echo "   3. Verify all sensors show real values"
    echo "   4. Set up Energy Dashboard with AC power data"
    
elif [ $SCAN_RESULT -eq 0 ]; then
    echo "🟡 PARTIAL SUCCESS: Bluetooth scanning works but connection failed"
    echo ""
    echo "✅ What's Working:"
    echo "   - Bluetooth adapter access"
    echo "   - Device scanning capability"
    echo "   - AppArmor profile loaded"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Ensure Renogy device is powered on and nearby"
    echo "   - Disconnect from any mobile apps"
    echo "   - Try restarting the Renogy device"
    echo "   - Check for Bluetooth interference"
    
else
    echo "⚠️  BLUETOOTH ACCESS CONFIGURED: Tests failed but container has better permissions"
    echo ""
    echo "🔧 What Was Done:"
    echo "   - Created custom AppArmor profile"
    echo "   - Added all required device access"
    echo "   - Configured proper capabilities"
    echo "   - Enabled D-Bus communication"
    echo ""
    echo "🔄 Next Steps:"
    echo "   1. Restart Home Assistant: docker restart $CONTAINER_NAME"
    echo "   2. Check AppArmor denials: sudo dmesg | grep DENIED"
    echo "   3. Monitor Home Assistant logs for BluPow connection attempts"
fi

echo ""
echo "🔧 Configuration Applied:"
echo "   - AppArmor Profile: docker-homeassistant-bluetooth"
echo "   - Privileged: true"
echo "   - Network: host"
echo "   - Devices: /dev/vhci, /dev/uhid, /dev/hidraw*"
echo "   - Capabilities: NET_ADMIN, NET_RAW, DAC_OVERRIDE, SYS_ADMIN"
echo "   - D-Bus: Read-write access"
echo ""
echo "🐛 Debugging Commands:"
echo "   - Check denials: sudo dmesg | grep DENIED"
echo "   - Check logs: docker logs $CONTAINER_NAME"
echo "   - Test manual: docker exec -it $CONTAINER_NAME /bin/bash"
echo ""
echo "✨ Advanced Bluetooth fix complete!" 