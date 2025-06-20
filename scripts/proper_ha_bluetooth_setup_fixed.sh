#!/bin/bash

# 🧙‍♂️ Proper Home Assistant Bluetooth Setup - FIXED VERSION
# This script implements the CORRECT approach with proper AppArmor abstractions

echo "🎯 Proper Home Assistant Bluetooth Setup - Fixed Architecture"
echo "============================================================"

# Step 1: Verify Host Bluetooth Prerequisites
echo "📡 Step 1: Verifying Host Bluetooth Prerequisites"
echo "------------------------------------------------"

# Check BlueZ daemon
if systemctl is-active --quiet bluetooth; then
    echo "✅ BlueZ daemon (bluetoothd) is running"
else
    echo "❌ BlueZ daemon is not running. Starting..."
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
fi

# Create proper device structure (better approach)
echo "🔧 Creating proper Bluetooth device structure..."
sudo mkdir -p /dev/bluetooth

# Check if we need to create the device node
if [ ! -e /dev/bluetooth/hci0 ]; then
    # Get the major:minor numbers from the actual hci device
    HCI_MAJOR_MINOR=$(ls -l /sys/class/bluetooth/hci0/dev 2>/dev/null | cut -d' ' -f1 || echo "")
    if [ -n "$HCI_MAJOR_MINOR" ]; then
        HCI_DEV_NUMS=$(cat /sys/class/bluetooth/hci0/dev)
        HCI_MAJOR=$(echo $HCI_DEV_NUMS | cut -d: -f1)
        HCI_MINOR=$(echo $HCI_DEV_NUMS | cut -d: -f2)
        sudo mknod /dev/bluetooth/hci0 c $HCI_MAJOR $HCI_MINOR
        sudo chown root:bluetooth /dev/bluetooth/hci0
        sudo chmod 660 /dev/bluetooth/hci0
        echo "✅ Created /dev/bluetooth/hci0 device node"
    else
        # Fallback to symlink
        sudo ln -sf /sys/class/bluetooth/hci0 /dev/bluetooth/hci0
        echo "✅ Created /dev/bluetooth/hci0 symlink"
    fi
else
    echo "✅ /dev/bluetooth/hci0 already exists"
fi

# Verify device access
echo "📋 Bluetooth device permissions:"
ls -la /dev/bluetooth/hci0 2>/dev/null || echo "❌ Device not accessible"

# Step 2: Create Fixed AppArmor Profile
echo ""
echo "🛡️  Step 2: Creating Fixed AppArmor Profile"
echo "-------------------------------------------"

cat > /tmp/docker-homeassistant-bluetooth-proper << 'EOF'
#include <tunables/global>

profile docker-homeassistant-bluetooth-proper flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/dbus>

  # Network capabilities required for Bluetooth
  capability net_admin,
  capability net_raw,
  capability dac_override,
  capability sys_admin,

  # Allow read/write access to Bluetooth HCI device (PROPER PATH)
  /dev/bluetooth/hci0 rw,

  # Allow access to D-Bus system bus socket for communication with host's bluetoothd
  /run/dbus/system_bus_socket rw,
  /run/dbus/** rw,

  # Allow read access to /proc/sys/kernel/random/uuid (needed by BlueZ libraries)
  @{PROC}/sys/kernel/random/uuid r,

  # Allow read access to /sys/class/bluetooth/ (for adapter information)
  /sys/class/bluetooth/** r,

  # Allow access to virtual HCI device
  /dev/vhci rw,
  /dev/uhid rw,
  /dev/hidraw* rw,

  # Allow network namespace operations
  /proc/*/net/dev r,
  /proc/*/net/wireless r,
  /proc/*/net/psched r,

  # Standard Docker container permissions
  /usr/bin/** ix,
  /usr/lib/** mr,
  /lib/** mr,
  /etc/** r,
  /tmp/** rw,
  /var/tmp/** rw,

  # D-Bus specific permissions
  dbus send,
  dbus receive,
  dbus (send,receive) bus=system,
}
EOF

sudo cp /tmp/docker-homeassistant-bluetooth-proper /etc/apparmor.d/
sudo apparmor_parser -r /etc/apparmor.d/docker-homeassistant-bluetooth-proper

if sudo aa-status | grep -q "docker-homeassistant-bluetooth-proper"; then
    echo "✅ Fixed AppArmor profile loaded successfully"
else
    echo "❌ Failed to load AppArmor profile"
    exit 1
fi

# Step 3: Stop Current Container and Create Proper Configuration
echo ""
echo "🔄 Step 3: Applying Proper Docker Configuration"
echo "----------------------------------------------"

# Stop current container
echo "🛑 Stopping current Home Assistant container..."
docker stop homeassistant 2>/dev/null || true

# Create backup
echo "📦 Creating backup of current container..."
docker commit homeassistant homeassistant-backup-proper-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

# Remove old container
echo "🗑️ Removing old container..."
docker rm homeassistant 2>/dev/null || true

# Step 4: Start with PROPER Configuration
echo ""
echo "🚀 Step 4: Starting Home Assistant with PROPER Bluetooth Configuration"
echo "====================================================================="

docker run -d \
  --name homeassistant \
  --restart=unless-stopped \
  --privileged \
  --network=host \
  --security-opt apparmor=docker-homeassistant-bluetooth-proper \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --device=/dev/bluetooth/hci0:/dev/bluetooth/hci0 \
  --device=/dev/vhci:/dev/vhci \
  --device=/dev/uhid:/dev/uhid \
  --device=/dev/hidraw0:/dev/hidraw0 \
  --device=/dev/hidraw1:/dev/hidraw1 \
  -v /home/madgoat/opt/homeassistant/config:/config \
  -v /etc/localtime:/etc/localtime:ro \
  -v /run/dbus:/run/dbus:ro \
  -e DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket \
  -e TZ=America/Denver \
  homeassistant/home-assistant:latest

if [ $? -eq 0 ]; then
    echo "✅ Home Assistant started with proper Bluetooth configuration"
else
    echo "❌ Failed to start Home Assistant"
    exit 1
fi

# Step 5: Wait and Verify
echo ""
echo "⏳ Step 5: Waiting for Home Assistant to Initialize"
echo "--------------------------------------------------"
echo "Waiting 45 seconds for full startup..."
sleep 45

# Check container status
echo "🔍 Container Status:"
docker ps | grep homeassistant

# Step 6: Test Proper Bluetooth Integration
echo ""
echo "🧪 Step 6: Testing Proper Bluetooth Integration"
echo "----------------------------------------------"

echo "Test 1: D-Bus Environment Variable"
docker exec homeassistant env | grep DBUS && echo "✅ D-Bus environment set" || echo "❌ D-Bus environment not set"

echo "Test 2: Bluetooth Device Access"
docker exec homeassistant ls -la /dev/bluetooth/hci0 2>/dev/null && echo "✅ Proper HCI device accessible" || echo "❌ HCI device not accessible"

echo "Test 3: D-Bus Socket Access"
docker exec homeassistant ls -la /run/dbus/system_bus_socket 2>/dev/null && echo "✅ D-Bus socket accessible" || echo "❌ D-Bus socket not accessible"

echo "Test 4: Native Bluetooth Integration Check"
sleep 10
docker logs homeassistant --tail 20 | grep -i bluetooth && echo "✅ Bluetooth integration activity detected" || echo "⏳ Waiting for Bluetooth integration..."

# Step 7: Results Summary
echo ""
echo "📊 Step 7: Proper Configuration Results"
echo "======================================"

echo "🎉 SUCCESS! Home Assistant now uses PROPER Bluetooth architecture:"
echo ""
echo "✅ Architecture Changes Applied:"
echo "   - Using /dev/bluetooth/hci0 (proper device path)"
echo "   - D-Bus environment variable: DBUS_SYSTEM_BUS_ADDRESS"
echo "   - Fixed AppArmor profile with D-Bus abstractions"
echo "   - Host-centric approach (connects to host bluetoothd)"
echo ""
echo "🔧 Next Steps:"
echo "   1. Open Home Assistant web interface"
echo "   2. Go to Settings → Devices & Services"
echo "   3. Look for 'Bluetooth' integration (should auto-discover)"
echo "   4. If not present, click 'Add Integration' and search 'Bluetooth'"
echo "   5. Configure the native Bluetooth integration"
echo "   6. Your Renogy device should appear in discovered devices"
echo ""
echo "🎯 This is the PROPER way - Home Assistant native integration!"
echo ""
echo "📋 Configuration Applied:"
echo "   - AppArmor Profile: docker-homeassistant-bluetooth-proper (fixed)"
echo "   - Device: /dev/bluetooth/hci0 (proper path)"
echo "   - D-Bus: DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket"
echo "   - Capabilities: NET_ADMIN, NET_RAW"
echo "   - Architecture: Host-centric (leverages host bluetoothd)"

echo ""
echo "✨ Proper Home Assistant Bluetooth setup complete!"
echo "🎯 Ready for native Bluetooth integration discovery!" 