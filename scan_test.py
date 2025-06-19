#!/usr/bin/env python3
"""
Simple Bluetooth scan to find the Renogy device
"""

import asyncio
from bleak import BleakScanner

async def scan():
    print('🔍 Scanning for Bluetooth devices (10 seconds)...')
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        print(f'✅ Found {len(devices)} devices:')
        
        renogy_found = False
        for device in devices:
            name = device.name or 'Unknown'
            address = device.address
            rssi = getattr(device, 'rssi', 'Unknown')
            
            print(f'  📱 {name} ({address}) RSSI: {rssi}')
            
            # Check for our specific Renogy device
            if address.upper() == 'C4:D3:6A:66:7E:D4':
                print('    🎯 *** THIS IS OUR RENOGY DEVICE! ***')
                renogy_found = True
            elif 'BT-TH' in name:
                print('    🤔 Potential Renogy device (BT-TH prefix)')
        
        print()
        if renogy_found:
            print('✅ SUCCESS: Renogy device C4:D3:6A:66:7E:D4 is discoverable!')
        else:
            print('❌ WARNING: Renogy device C4:D3:6A:66:7E:D4 not found in scan')
            print('   Possible reasons:')
            print('   1. Device is not powered on')
            print('   2. Device is not in pairing/discoverable mode')
            print('   3. Device is already connected to another application')
            print('   4. Device is out of range')
            print('   5. Bluetooth interference')
            
    except Exception as e:
        print(f'❌ Scan failed: {e}')

if __name__ == "__main__":
    asyncio.run(scan()) 