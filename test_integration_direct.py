#!/usr/bin/env python3
"""
Direct Integration Test for BluPow
==================================

This script tests the corrected BluPow integration directly within
the Home Assistant environment to verify the data parsing fixes.
"""

import asyncio
import sys
import os

# Add the BluPow integration to path
sys.path.append('/config/custom_components/blupow')

from blupow_client import BluPowClient

async def test_integration():
    """Test the corrected integration directly"""
    print("🧪 Testing BluPow Integration with Corrected Parsing")
    print("=" * 55)
    
    # Test the client
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    try:
        print("🔗 Connecting to inverter...")
        if not await client.connect():
            print("❌ Connection failed")
            return False
        
        print("✅ Connected successfully!")
        
        print("📋 Reading all inverter data...")
        data = await client.read_device_info()
        
        if not data:
            print("❌ No data received")
            return False
        
        print(f"✅ Received {len(data)} data points")
        print("\n📊 PARSED DATA:")
        print("-" * 40)
        
        # Display key values
        key_fields = [
            'model', 'device_id', 'input_voltage', 'output_voltage',
            'input_frequency', 'output_frequency', 'battery_voltage',
            'battery_percentage', 'load_active_power', 'temperature',
            'solar_voltage', 'solar_current', 'charging_status'
        ]
        
        for field in key_fields:
            if field in data:
                value = data[field]
                print(f"{field+':':<20} {value}")
        
        print("-" * 40)
        
        # Validate data makes sense
        issues = []
        if 'input_voltage' in data and data['input_voltage'] > 200:
            issues.append(f"Input voltage too high: {data['input_voltage']}V")
        if 'battery_voltage' in data and data['battery_voltage'] > 20:
            issues.append(f"Battery voltage too high: {data['battery_voltage']}V")
        if 'battery_percentage' in data and data['battery_percentage'] > 100:
            issues.append(f"Battery SOC too high: {data['battery_percentage']}%")
        if 'temperature' in data and data['temperature'] > 100:
            issues.append(f"Temperature too high: {data['temperature']}°C")
        
        if issues:
            print("\n⚠️  DATA VALIDATION ISSUES:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ ALL DATA VALUES LOOK CORRECT!")
            print("🎉 Integration parsing is working perfectly!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client.is_connected:
            await client.disconnect()
            print("🔌 Disconnected")

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1) 