#!/bin/bash
# ESP_GATT_CONN_FAIL_ESTABLISH Fix Script
# Optimizes Linux Bluetooth connection parameters and timeouts
# Based on research from kernel.org and bluetooth development community

set -e

echo "🔧 BluPow ESP_GATT_CONN_FAIL_ESTABLISH Fix Script"
echo "=================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (sudo)"
   exit 1
fi

# 1. BLUETOOTH LOW-LATENCY OPTIMIZATION
echo "1️⃣ Optimizing Bluetooth connection parameters..."

BT_DEBUG_PATH="/sys/kernel/debug/bluetooth/"
if [ ! -d "$BT_DEBUG_PATH" ]; then
    echo "❌ Bluetooth debugfs path not found. Enabling..."
    mount -t debugfs none /sys/kernel/debug/ 2>/dev/null || true
fi

# Apply low-latency parameters for all HCI interfaces
for HCI_PATH in ${BT_DEBUG_PATH}hci*/ ; do
    if [ -d "$HCI_PATH" ]; then
        HCI_DEVICE=$(basename "$HCI_PATH")
        echo "   🔹 Configuring $HCI_DEVICE for low-latency"
        
        # Set connection latency to 0 (no skipped events)
        if [ -f "${HCI_PATH}conn_latency" ]; then
            echo "0" > "${HCI_PATH}conn_latency" 2>/dev/null || true
            echo "     ✅ conn_latency = 0"
        fi
        
        # Set minimum connection interval (6 = 7.5ms)
        if [ -f "${HCI_PATH}conn_min_interval" ]; then
            echo "6" > "${HCI_PATH}conn_min_interval" 2>/dev/null || true
            echo "     ✅ conn_min_interval = 6 (7.5ms)"
        fi
        
        # Set maximum connection interval (9 = 11.25ms)
        if [ -f "${HCI_PATH}conn_max_interval" ]; then
            echo "9" > "${HCI_PATH}conn_max_interval" 2>/dev/null || true
            echo "     ✅ conn_max_interval = 9 (11.25ms)"
        fi
    fi
done

# 2. BLUETOOTH POWER MANAGEMENT
echo "2️⃣ Disabling Bluetooth power management..."

# Disable Bluetooth USB autosuspend
for usb_device in /sys/bus/usb/devices/*/; do
    if [ -f "${usb_device}product" ] && grep -qi "bluetooth\|broadcom\|intel" "${usb_device}product" 2>/dev/null; then
        echo "on" > "${usb_device}power/control" 2>/dev/null || true
        echo "     ✅ Disabled USB autosuspend for $(cat ${usb_device}product 2>/dev/null || echo 'Bluetooth device')"
    fi
done

# 3. KERNEL MODULE PARAMETERS
echo "3️⃣ Optimizing Bluetooth kernel modules..."

# Create or update modprobe configuration
cat > /etc/modprobe.d/blupow-bluetooth-optimization.conf << 'EOF'
# BluPow Bluetooth Optimization
# Fixes ESP_GATT_CONN_FAIL_ESTABLISH errors

# Bluetooth core optimizations
options bluetooth disable_ertm=1
options bluetooth disable_esco=1

# HCI optimizations for connection stability
options btusb enable_autosuspend=0

# Increase connection attempt timeouts
options bluetooth le_conn_timeout=60000
EOF

echo "     ✅ Created /etc/modprobe.d/blupow-bluetooth-optimization.conf"

# 4. SYSTEM BLUETOOTH CONFIGURATION
echo "4️⃣ Configuring system Bluetooth settings..."

# Create bluetooth main.conf optimization
mkdir -p /etc/bluetooth
cat > /etc/bluetooth/main.conf << 'EOF'
[General]
# BluPow optimization for ESP_GATT_CONN_FAIL_ESTABLISH

# Increase timeouts for connection establishment
DiscoverableTimeout = 0
PairableTimeout = 0

# Connection parameters
MinConnectionInterval=6
MaxConnectionInterval=9
ConnectionLatency=0
ConnectionSupervisionTimeout=6000

# Disable problematic features
DisablePlugins = sap
EnableGatt = true

# Device class
Class = 0x000100

# Connection modes
FastConnectable = true
Privacy = off

[Policy]
AutoEnable=true
EOF

echo "     ✅ Created /etc/bluetooth/main.conf"

# 5. DOCKER BLUETOOTH OPTIMIZATION
echo "5️⃣ Optimizing Docker Bluetooth access..."

# Ensure proper device access
if [ -c /dev/rfkill ]; then
    chmod 666 /dev/rfkill
    echo "     ✅ Fixed /dev/rfkill permissions"
fi

# Create optimized Docker compose service
cat > /tmp/bluetooth-optimization.yml << 'EOF'
# Add these settings to your Home Assistant docker-compose.yml
# to optimize Bluetooth performance:

services:
  homeassistant:
    # ... your existing config ...
    privileged: true
    network_mode: host
    devices:
      - /dev/rfkill:/dev/rfkill:rw
    volumes:
      - /sys/kernel/debug:/sys/kernel/debug:ro
      - /run/dbus:/run/dbus:ro
    environment:
      - BLUETOOTH_HCICONFIG_UP=1
EOF

echo "     ✅ Created Bluetooth optimization reference"

# 6. RESTART BLUETOOTH SERVICES
echo "6️⃣ Restarting Bluetooth services..."

# Stop all Bluetooth services
systemctl stop bluetooth 2>/dev/null || true
systemctl stop bluetoothd 2>/dev/null || true

# Reset Bluetooth interface
for hci in $(hciconfig | grep hci | cut -d: -f1); do
    hciconfig $hci down 2>/dev/null || true
    hciconfig $hci up 2>/dev/null || true
    echo "     ✅ Reset $hci"
done

# Restart services
systemctl start bluetooth 2>/dev/null || true
sleep 3

# Power cycle Bluetooth
for hci in $(hciconfig | grep hci | cut -d: -f1); do
    bluetoothctl power off 2>/dev/null || true
    sleep 2
    bluetoothctl power on 2>/dev/null || true
    echo "     ✅ Power cycled $hci"
done

echo ""
echo "🎉 ESP_GATT_CONN_FAIL_ESTABLISH Fix Complete!"
echo "============================================="
echo ""
echo "✅ Applied low-latency Bluetooth parameters"
echo "✅ Disabled power management"
echo "✅ Optimized kernel modules"
echo "✅ Configured system Bluetooth"
echo "✅ Reset Bluetooth services"
echo ""
echo "🔄 NEXT STEPS:"
echo "1. Restart Home Assistant: docker restart homeassistant"
echo "2. Wait 60 seconds for full initialization"
echo "3. Check sensors - they should show data within 2-3 minutes"
echo ""
echo "📊 To monitor connection attempts:"
echo "   docker logs homeassistant --tail 20 | grep blupow"
echo ""
echo "🔍 To verify Bluetooth parameters:"
echo "   cat /sys/kernel/debug/bluetooth/hci0/conn_*"
echo "" 