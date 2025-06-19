#!/usr/bin/env python3
"""
Simple BluPow Bluetooth Test Script
"""

import asyncio
from bleak import BleakScanner, BleakClient

async def main():
    print("=" * 50)
    print("BluPow Bluetooth Connection Test")
    print("=" * 50)
    
    # First, scan for devices
    print("Scanning for Bluetooth devices...")
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f"Found {len(devices)} devices:")
        
        target_device = None
        for device in devices:
            name = device.name or "Unknown"
            address = device.address
            print(f"  {name} ({address})")
            
            # Look for our target device
            if address.upper() == "C4:D3:6A:66:7E:D4":
                target_device = device
                print(f"  *** Found target device: {name} ***")
        
        if not target_device:
            print("\n❌ Target device C4:D3:6A:66:7E:D4 not found!")
            print("Make sure your solar charger is:")
            print("  1. Powered on")
            print("  2. Within 10 meters")
            print("  3. Not connected to another device")
            return
        
        # Try to connect to the target device
        print(f"\n🔌 Attempting to connect to {target_device.name}...")
        try:
            async with BleakClient(target_device, timeout=15.0) as client:
                print("✅ Successfully connected!")
                
                # List services
                try:
                    services = client.services
                    if services:
                        print(f"Found services:")
                        for service in services:
                            print(f"  Service: {service.uuid}")
                            for char in service.characteristics:
                                print(f"    Char: {char.uuid} ({char.properties})")
                    else:
                        print("No services found")
                except Exception as e:
                    print(f"Error reading services: {e}")
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            
            if "No backend with an available connection slot" in str(e):
                print("\n🚨 This is the same error Home Assistant is experiencing!")
                print("\nTroubleshooting steps:")
                print("1. sudo systemctl restart bluetooth")
                print("2. sudo hciconfig hci0 reset")
                print("3. killall -9 bluetoothd && sudo systemctl start bluetooth")
                print("4. Check if another app is using the device")
                print("5. Try rebooting the system")
            
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        print("This indicates a serious Bluetooth issue")

if __name__ == "__main__":
    asyncio.run(main()) 