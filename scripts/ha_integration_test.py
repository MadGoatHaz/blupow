#!/usr/bin/env python3
"""
Home Assistant BluPow Integration Test

This script runs inside the Home Assistant container to test
the corrected BluPow integration with the inverter.
"""

import sys
import json
import asyncio
from datetime import datetime

# Add custom components to path
sys.path.insert(0, '/config/custom_components')

async def test_blupow_integration():
    """Test the BluPow integration inside Home Assistant"""
    print("🔬 Home Assistant BluPow Integration Test")
    print("=" * 45)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'import_test': False,
        'sensor_count': 0,
        'client_test': False,
        'errors': []
    }
    
    # Test 1: Import BluPow components
    print("🧪 TEST 1: Import BluPow Components")
    try:
        import blupow
        print("✅ Main blupow module imported")
        
        from blupow.const import DOMAIN, DEVICE_SENSORS
        print(f"✅ Constants imported - Domain: {DOMAIN}")
        print(f"✅ Sensors imported - Count: {len(DEVICE_SENSORS)}")
        test_results['sensor_count'] = len(DEVICE_SENSORS)
        
        from blupow.blupow_client import BluPowClient
        print("✅ BluPowClient imported")
        
        from blupow.coordinator import BluPowDataUpdateCoordinator
        print("✅ Coordinator imported")
        
        from blupow.sensor import BluPowSensor
        print("✅ Sensor imported")
        
        test_results['import_test'] = True
        print("✅ All imports successful!")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        test_results['errors'].append(f"Import failed: {e}")
        return test_results
    
    print()
    
    # Test 2: Show sensor definitions
    print("🧪 TEST 2: Sensor Definitions")
    print(f"Total sensors: {len(DEVICE_SENSORS)}")
    
    # Show first 10 sensors
    print("First 10 sensors:")
    for i, sensor in enumerate(DEVICE_SENSORS[:10]):
        print(f"  {i+1:2d}. {sensor.key}: {sensor.name}")
    
    if len(DEVICE_SENSORS) > 10:
        print(f"  ... and {len(DEVICE_SENSORS) - 10} more sensors")
    
    # Key inverter sensors
    sensor_keys = [sensor.key for sensor in DEVICE_SENSORS]
    key_inverter_sensors = [
        'model', 'input_voltage', 'output_voltage', 'input_frequency', 
        'battery_voltage', 'battery_soc', 'load_power', 'temperature'
    ]
    
    print("\nKey inverter sensors:")
    missing_sensors = []
    for sensor in key_inverter_sensors:
        if sensor in sensor_keys:
            print(f"  ✅ {sensor}")
        else:
            print(f"  ❌ {sensor} (missing)")
            missing_sensors.append(sensor)
    
    if missing_sensors:
        print(f"\n⚠️  Missing {len(missing_sensors)} key sensors: {missing_sensors}")
    else:
        print("\n✅ All key inverter sensors present!")
    
    print()
    
    # Test 3: Create client (without connecting)
    print("🧪 TEST 3: Client Creation")
    try:
        client = BluPowClient("D8:B6:73:BF:4F:75")
        print("✅ BluPowClient created successfully")
        print(f"✅ Device address: {client.address}")
        print(f"✅ Connection status: {client.is_connected}")
        test_results['client_test'] = True
        
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        test_results['errors'].append(f"Client creation failed: {e}")
    
    print()
    
    # Test 4: Check for config entries
    print("🧪 TEST 4: Config Entry Check")
    try:
        import os
        config_path = '/config/.storage/core.config_entries'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            entries = config_data.get('data', {}).get('entries', [])
            blupow_entries = [e for e in entries if e.get('domain') == 'blupow']
            
            print(f"Total config entries: {len(entries)}")
            print(f"BluPow entries: {len(blupow_entries)}")
            
            if blupow_entries:
                print("⚠️  Existing BluPow entries found:")
                for entry in blupow_entries:
                    print(f"  • {entry.get('title', 'Unknown')} ({entry.get('entry_id', 'Unknown')})")
                print("  These may need to be removed if causing issues")
            else:
                print("✅ No existing BluPow entries (clean state)")
                
        else:
            print("❌ Config entries file not found")
            
    except Exception as e:
        print(f"❌ Config entry check failed: {e}")
        test_results['errors'].append(f"Config entry check failed: {e}")
    
    # Final results
    print("\n" + "=" * 45)
    print("📋 TEST SUMMARY")
    print("=" * 45)
    
    print(f"Import Test: {'✅ PASS' if test_results['import_test'] else '❌ FAIL'}")
    print(f"Sensor Count: {test_results['sensor_count']} sensors")
    print(f"Client Test: {'✅ PASS' if test_results['client_test'] else '❌ FAIL'}")
    print(f"Errors: {len(test_results['errors'])}")
    
    if test_results['errors']:
        print("\nErrors encountered:")
        for error in test_results['errors']:
            print(f"  • {error}")
    
    # Overall status
    overall_success = (
        test_results['import_test'] and 
        test_results['client_test'] and 
        test_results['sensor_count'] == 22 and
        len(test_results['errors']) == 0
    )
    
    print(f"\nOverall Status: {'🎉 SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        print("\n📋 READY FOR INTEGRATION SETUP:")
        print("1. Go to Home Assistant Settings → Devices & Services")
        print("2. Click 'Add Integration'")
        print("3. Search for 'BluPow'")
        print("4. Configure with MAC: D8:B6:73:BF:4F:75")
        print("5. All 22 inverter sensors should appear")
    else:
        print("\n🔧 TROUBLESHOOTING NEEDED:")
        print("Check the errors above and resolve before proceeding")
    
    # Save results
    try:
        with open('/config/blupow_integration_test.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"\n💾 Test results saved: /config/blupow_integration_test.json")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return overall_success

async def main():
    """Main test execution"""
    success = await test_blupow_integration()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(result)
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        exit(1) 