#!/usr/bin/env python3
"""
Simple test for BluPow cyrils approach without HA dependencies
"""
import asyncio
import logging
import sys
import os

# Direct import of just the client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'blupow'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_discovery():
    """Simple discovery test"""
    try:
        from bleak import BleakScanner
        print("🔍 Scanning for Bluetooth devices...")
        devices = await BleakScanner.discover(timeout=10)
        print(f"Found {len(devices)} devices:")
        
        for dev in devices:
            print(f"  - {dev.name or 'Unknown'} ({dev.address})")
            
        # Look for our specific devices
        target_devices = ["D8:B6:73:BF:4F:75", "C4:D3:6A:66:7E:D4"]
        found_devices = []
        
        for dev in devices:
            if dev.address.upper() in [addr.upper() for addr in target_devices]:
                found_devices.append(dev)
                print(f"🎯 Found target device: {dev.name} ({dev.address})")
        
        if found_devices:
            print("✅ Your BluPow devices are discoverable!")
            print("   The integration should work once Home Assistant restarts.")
        else:
            print("❌ BluPow devices not found. Please check:")
            print("   1. Devices are powered on")
            print("   2. Devices are within range")
            print("   3. Devices are not connected to another app")
            
    except Exception as e:
        print(f"Error during discovery: {e}")

if __name__ == "__main__":
    asyncio.run(test_discovery()) 