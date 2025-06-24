#!/usr/bin/env python3
"""
Simple test for BluPow cyrils approach without HA dependencies
"""
import asyncio
import logging
import sys
import os
from bleak import BleakScanner

# Direct import of just the client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'blupow'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Use environment variables for target devices, or use a placeholder
TARGET_MACS_STR = os.environ.get("BLUPOW_TEST_MACS")

# --- Main Logic ---
async def main():
    if not TARGET_MACS_STR:
        print("❌ ERROR: Please set the BLUPOW_TEST_MACS environment variable.")
        print("   It should be a comma-separated list of MAC addresses.")
        print("   Example: export BLUPOW_TEST_MACS='AA:BB:CC:DD:EE:FF,11:22:33:44:55:66'")
        return

    target_devices = [mac.strip() for mac in TARGET_MACS_STR.split(',')]
    print("--- Cyril's Simple BLE Device Scanner ---")
    print(f"Looking for: {', '.join(target_devices)}")

    try:
        print("🔍 Scanning for Bluetooth devices...")
        devices = await BleakScanner.discover(timeout=10)
        print(f"Found {len(devices)} devices:")
        
        for dev in devices:
            print(f"  - {dev.name or 'Unknown'} ({dev.address})")
            
        # Look for our specific devices
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
    asyncio.run(main()) 