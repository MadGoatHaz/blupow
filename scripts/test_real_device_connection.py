#!/usr/bin/env python3
"""
Test script to verify real BluPow device connection
This script tests the updated client without any fake data
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the custom_components directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "blupow"))

from blupow_client import BluPowClient

async def test_real_device_connection():
    """Test real device connection and data retrieval"""
    print("🔍 Testing Real BluPow Device Connection")
    print("=" * 50)
    
    # Test with both known device MAC addresses
    test_devices = [
        "D8:B6:73:BF:4F:75",  # Primary device
        "C4:D3:6A:66:7E:D4",  # Secondary device
    ]
    
    for mac_address in test_devices:
        print(f"\n📱 Testing device: {mac_address}")
        print("-" * 30)
        
        client = BluPowClient(mac_address)
        
        try:
            # Test connection
            print("1. Testing connection...")
            connected = await client.connect()
            
            if connected:
                print("✅ Device connected successfully")
                
                # Test data reading
                print("2. Reading device data...")
                device_data = await client.read_device_info()
                
                if device_data:
                    print(f"✅ Device data retrieved: {len(device_data)} fields")
                    print("📊 Device data:")
                    for key, value in device_data.items():
                        print(f"   {key}: {value}")
                else:
                    print("❌ No data retrieved from device")
                
                # Test cached data
                print("3. Testing cached data...")
                cached_data = client.get_data()
                if cached_data:
                    print(f"✅ Cached data available: {len(cached_data)} fields")
                else:
                    print("❌ No cached data available")
                
                # Disconnect
                print("4. Disconnecting...")
                await client.disconnect()
                print("✅ Disconnected successfully")
                
            else:
                print("❌ Failed to connect to device")
                
                # Test get_data when not connected (should return empty)
                print("5. Testing get_data when disconnected...")
                data = client.get_data()
                if data:
                    print(f"⚠️ WARNING: get_data returned data when disconnected: {data}")
                    print("   This suggests fake data is still present!")
                else:
                    print("✅ get_data correctly returns empty dict when disconnected")
                
        except Exception as e:
            print(f"❌ Error testing device {mac_address}: {e}")
        
        print()

async def test_integration_flow():
    """Test the integration flow that coordinator would use"""
    print("\n🔄 Testing Integration Flow")
    print("=" * 50)
    
    mac_address = "D8:B6:73:BF:4F:75"  # Primary device
    client = BluPowClient(mac_address)
    
    try:
        # Simulate coordinator update cycle
        print("1. Simulating coordinator update cycle...")
        
        # Try to connect and read data
        connected = await client.connect()
        
        if connected:
            device_data = await client.read_device_info()
            await client.disconnect()
            
            if device_data:
                print(f"✅ Update cycle successful: {len(device_data)} fields")
                return device_data
            else:
                print("❌ Update cycle failed - no data")
                return {}
        else:
            print("❌ Update cycle failed - connection failed")
            
            # Test what happens when connection fails
            cached_data = client.get_data()
            if cached_data:
                print(f"⚠️ WARNING: Client returned data despite connection failure: {cached_data}")
                print("   This suggests fake data is still present!")
            else:
                print("✅ Client correctly returns empty data when connection fails")
            
            return {}
            
    except Exception as e:
        print(f"❌ Integration flow error: {e}")
        return {}

async def main():
    """Main test function"""
    print("🚀 BluPow Real Device Connection Test")
    print("This test verifies that fake data has been removed")
    print("=" * 60)
    
    # Test individual device connections
    await test_real_device_connection()
    
    # Test integration flow
    await test_integration_flow()
    
    print("\n✅ Test completed!")
    print("If you see warnings about fake data, the removal was incomplete.")
    print("If all tests pass, fake data has been successfully removed.")

if __name__ == "__main__":
    asyncio.run(main()) 