#!/usr/bin/env python3
"""Test BluPow connection to the discovered Renogy device"""

import asyncio
import sys

# Add the BluPow directory to path
sys.path.append('/config/custom_components/blupow')

try:
    from bleak import BleakScanner, BleakClient
except ImportError as e:
    print(f"Error importing bleak: {e}")
    sys.exit(1)

async def test_renogy_device():
    """Test connection to the discovered Renogy device"""
    target_address = 'D8:B6:73:BF:4F:75'
    target_name = 'BTRIC134000035'
    
    try:
        print('🔍 Testing direct connection to Renogy device...')
        print(f'📍 Target: {target_address} ({target_name})')
        
        # First, verify device is still discoverable
        print('📡 Scanning for device...')
        devices = await BleakScanner.discover(timeout=10.0)
        
        target_device = None
        for device in devices:
            if device.address == target_address:
                target_device = device
                break
        
        if not target_device:
            print(f'❌ Device {target_address} not found in scan')
            return False
        
        print(f'✅ Device found: {target_device.name} (RSSI: {getattr(target_device, "rssi", "Unknown")})')
        
        # Test connection
        print('🔗 Attempting to connect...')
        async with BleakClient(target_device) as client:
            print(f'✅ Connected successfully!')
            
            # Get services
            services = client.services
            service_list = list(services)
            print(f'📋 Found {len(service_list)} services:')
            
            renogy_service_found = False
            for service in service_list:
                print(f'   🔹 Service: {service.uuid}')
                for char in service.characteristics:
                    print(f'      └─ Characteristic: {char.uuid} (Properties: {char.properties})')
                
                # Look for Renogy service UUID
                renogy_service_uuid = "0000ffd0-0000-1000-8000-00805f9b34fb"
                if str(service.uuid).lower() == renogy_service_uuid.lower():
                    print(f'✅ Found Renogy service UUID: {renogy_service_uuid}')
                    renogy_service_found = True
            
            if renogy_service_found:
                return True
            else:
                print(f'⚠️  Renogy service UUID not found')
                return False
                
    except Exception as e:
        print(f'❌ Connection test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_renogy_device())
    print(f'\n🎯 Connection test: {"SUCCESS" if result else "FAILED"}')
    exit(0 if result else 1) 