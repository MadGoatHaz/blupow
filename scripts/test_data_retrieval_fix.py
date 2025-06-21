#!/usr/bin/env python3
"""
Test script to identify and fix the data retrieval issue in BluPow client
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_current_approach():
    """Test the current approach that the coordinator uses"""
    print("=" * 60)
    print("🔍 TESTING CURRENT COORDINATOR APPROACH")
    print("=" * 60)
    
    # Use the correct MAC address discovered earlier
    mac_address = "C4:D3:6A:66:7E:D4"
    client = BluPowClient(mac_address)
    
    try:
        print("1. Connecting to device...")
        connected = await client.connect()
        if not connected:
            print("❌ Connection failed")
            return {}
        
        print("2. Calling get_data() (current coordinator approach)...")
        data = client.get_data()
        print(f"📊 get_data() returned: {len(data)} fields")
        print(f"Data: {data}")
        
        print("3. Disconnecting...")
        await client.disconnect()
        
        return data
        
    except Exception as e:
        print(f"❌ Error in current approach: {e}")
        return {}

async def test_fixed_approach():
    """Test the fixed approach that actually reads device data"""
    print("\n" + "=" * 60)
    print("🔧 TESTING FIXED APPROACH")
    print("=" * 60)
    
    # Use the correct MAC address discovered earlier
    mac_address = "C4:D3:6A:66:7E:D4"
    client = BluPowClient(mac_address)
    
    try:
        print("1. Connecting to device...")
        connected = await client.connect()
        if not connected:
            print("❌ Connection failed")
            return {}
        
        print("2. Calling read_device_info() (fixed approach)...")
        data = await client.read_device_info()
        print(f"📊 read_device_info() returned: {len(data)} fields")
        print(f"Data: {data}")
        
        print("3. Now calling get_data() after read_device_info()...")
        cached_data = client.get_data()
        print(f"📊 get_data() now returns: {len(cached_data)} fields")
        print(f"Cached data: {cached_data}")
        
        print("4. Disconnecting...")
        await client.disconnect()
        
        return data
        
    except Exception as e:
        print(f"❌ Error in fixed approach: {e}")
        return {}

async def test_coordinator_simulation():
    """Simulate the exact coordinator subprocess approach with fix"""
    print("\n" + "=" * 60)
    print("🎯 TESTING COORDINATOR SIMULATION (FIXED)")
    print("=" * 60)
    
    mac_address = "C4:D3:6A:66:7E:D4"
    client = BluPowClient(mac_address)
    start_time = time.time()
    
    try:
        # Connect
        print("1. Connecting...")
        connected = await client.connect()
        if not connected:
            return {'error': 'Connection failed', 'timestamp': time.time()}
        
        # Read device info FIRST (this is the fix!)
        print("2. Reading device info...")
        data = await client.read_device_info()
        
        # Then get cached data (this is what coordinator expects)
        print("3. Getting cached data...")
        cached_data = client.get_data()
        
        # Disconnect
        print("4. Disconnecting...")
        await client.disconnect()
        
        # Add metadata (like coordinator does)
        if cached_data:
            cached_data['_coordinator_meta'] = {
                'cycle_time': time.time() - start_time,
                'timestamp': time.time(),
                'mac_address': mac_address,
                'connection_method': 'cycle'
            }
            print(f"✅ SUCCESS: {len(cached_data)} fields retrieved")
            return cached_data
        else:
            print("❌ No data retrieved")
            return {}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'error': str(e)}

async def main():
    """Run all tests to identify and validate the fix"""
    print("🚀 BluPow Data Retrieval Fix Test")
    print("This test will identify why get_data() returns empty and test the fix")
    
    # Test current broken approach
    current_data = await test_current_approach()
    
    # Test fixed approach
    fixed_data = await test_fixed_approach()
    
    # Test coordinator simulation
    coordinator_data = await test_coordinator_simulation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Current approach (get_data only): {len(current_data)} fields")
    print(f"Fixed approach (read_device_info first): {len(fixed_data)} fields")
    print(f"Coordinator simulation (fixed): {len(coordinator_data)} fields")
    
    if len(fixed_data) > len(current_data):
        print("\n✅ FIX CONFIRMED: read_device_info() must be called before get_data()")
        print("💡 SOLUTION: Coordinator subprocess must call read_device_info() first")
    else:
        print("\n❌ Issue not resolved - further investigation needed")

if __name__ == "__main__":
    asyncio.run(main()) 