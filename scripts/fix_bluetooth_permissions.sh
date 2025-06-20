#!/bin/bash

# BluPow Bluetooth Permission Fix Script
# ======================================
# This script reconfigures Home Assistant Docker to allow Bluetooth access

set -e

echo "🔧 BluPow Bluetooth Permission Fix"
echo "================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Container name
CONTAINER_NAME="homeassistant"

echo "🔍 Current Home Assistant Container Status:"
docker ps | grep $CONTAINER_NAME || echo "   Container not running"

echo ""
echo "📋 Current Configuration Issues:"
echo "   - AppArmor Profile: docker-default (restricts D-Bus access)"
echo "   - Privileged: false (limits hardware access)"
echo "   - Devices: null (no Bluetooth device access)"
echo ""

echo "💡 Recommended Solution:"
echo "   We need to restart Home Assistant with proper Bluetooth permissions"
echo ""

# Confirm with user
read -p "Do you want to proceed with fixing the Bluetooth configuration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 1
fi

echo ""
echo "🛑 Stopping Home Assistant..."
docker stop $CONTAINER_NAME || echo "   Container already stopped"

echo ""
echo "🔄 Backing up current container..."
docker commit $CONTAINER_NAME homeassistant-backup-$(date +%Y%m%d-%H%M%S)

echo ""
echo "🗑️ Removing old container..."
docker rm $CONTAINER_NAME || echo "   Container already removed"

echo ""
echo "🚀 Starting Home Assistant with Bluetooth permissions..."

# Start container with proper Bluetooth configuration
docker run -d \
  --name $CONTAINER_NAME \
  --restart=unless-stopped \
  --privileged \
  --net=host \
  --security-opt apparmor:unconfined \
  --device /dev/hci0:/dev/hci0 \
  -e TZ=America/Denver \
  -v /home/madgoat/opt/homeassistant/config:/config \
  -v /etc/localtime:/etc/localtime:ro \
  -v /run/dbus:/run/dbus:rw \
  -v /var/run/docker.sock:/var/run/docker.sock \
  homeassistant/home-assistant:latest

echo ""
echo "⏳ Waiting for Home Assistant to start..."
sleep 10

echo ""
echo "🔍 Checking container status..."
docker ps | grep $CONTAINER_NAME

echo ""
echo "🧪 Testing Bluetooth access from container..."
docker exec $CONTAINER_NAME python3 -c "
import asyncio
from bleak import BleakClient
import sys

async def test_connection():
    try:
        print('Testing Bluetooth connection from container...')
        async with BleakClient('D8:B6:73:BF:4F:75', timeout=5.0) as client:
            print('✅ Bluetooth connection successful!')
            if client.is_connected:
                print(f'   Device connected: {client.is_connected}')
                print('   BluPow integration should now work!')
            return True
    except Exception as e:
        print(f'❌ Connection still failed: {e}')
        print('   May need additional troubleshooting')
        return False

try:
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f'❌ Test failed: {e}')
    sys.exit(1)
"

TEST_RESULT=$?

echo ""
echo "📊 Results:"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ SUCCESS: Home Assistant can now connect to Bluetooth devices!"
    echo ""
    echo "🎉 Your BluPow integration should now work properly:"
    echo "   1. All 22 sensors should show real data instead of 'Unavailable'"
    echo "   2. Check Home Assistant logs for successful connection messages"
    echo "   3. Visit the BluPow device page to see live data"
    echo ""
    echo "🔄 If sensors still show 'Unavailable', restart Home Assistant:"
    echo "   docker restart $CONTAINER_NAME"
else
    echo "⚠️  Bluetooth test failed, but container is running with better permissions"
    echo "   The BluPow integration may work after a restart or some time"
    echo ""
    echo "🔄 Try restarting Home Assistant:"
    echo "   docker restart $CONTAINER_NAME"
    echo ""
    echo "📋 Additional troubleshooting steps:"
    echo "   1. Check if the Renogy device is powered on and nearby"
    echo "   2. Ensure no other app is connected to the device"
    echo "   3. Check Home Assistant logs for connection attempts"
fi

echo ""
echo "🔧 Configuration Changes Made:"
echo "   - Added --privileged flag for hardware access"
echo "   - Added --device /dev/hci0 for Bluetooth device access"
echo "   - Changed AppArmor to unconfined for D-Bus access"
echo "   - Changed /run/dbus mount to read-write"
echo ""
echo "✅ Bluetooth permission fix complete!" 