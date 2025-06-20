#!/usr/bin/env python3
"""Simple Bluetooth test to diagnose container access issues"""

import asyncio
from bleak import BleakScanner

async def test_scan():
    try:
        print('🔍 Testing Bluetooth scan...')
        devices = await BleakScanner.discover(timeout=5.0)
        print(f'✅ Found {len(devices)} devices')
        for device in devices[:5]:
            print(f'  - {device.address}: {device.name or "Unknown"}')
        return True
    except Exception as e:
        print(f'❌ Scan failed: {e}')
        return False

if __name__ == "__main__":
    result = asyncio.run(test_scan())
    exit(0 if result else 1) 