#!/usr/bin/env python3
"""
Simple BluPow Inverter Test Script

Quick test to verify the corrected inverter protocol works
with the Renogy RIV1230RCH-SPS inverter.
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from const import DEVICE_SENSORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_inverter_connection():
    """Test connection and data fetch from inverter"""
    device_address = "D8:B6:73:BF:4F:75"
    
    print("🔬 BluPow Inverter Connection Test")
    print("=" * 40)
    print(f"Device: {device_address}")
    print(f"Expected Type: Renogy RIV1230RCH-SPS Inverter")
    print(f"Protocol: Corrected Inverter Registers")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Check sensor definitions
    print("🧪 TEST 1: Sensor Definitions")
    print(f"Total sensors defined: {len(DEVICE_SENSORS)}")
    
    sensor_keys = [sensor.key for sensor in DEVICE_SENSORS]
    key_sensors = ['model', 'input_voltage', 'output_voltage', 'battery_voltage', 'battery_soc']
    
    print("Key sensor check:")
    for sensor in key_sensors:
        status = "✅" if sensor in sensor_keys else "❌"
        print(f"  {status} {sensor}")
    print()
    
    # Test 2: Connection and data fetch
    print("🧪 TEST 2: Connection & Data Fetch")
    
    try:
        # Create client
        client = BluPowClient(device_address)
        print(f"✅ Client created for {device_address}")
        
        # Connect to device
        print("🔄 Attempting connection...")
        if await client.connect():
            print("✅ Connection successful!")
            
            # Fetch data
            print("🔄 Fetching inverter data...")
            data = await client.read_device_info()
            
            if data:
                print("✅ Data fetch successful!")
                print("\n📊 INVERTER DATA SUMMARY:")
                print("-" * 30)
                
                # Display key data points
                key_data = {
                    'Model': data.get('model', 'Unknown'),
                    'Device ID': data.get('device_id', 'Unknown'),
                    'Input Voltage': f"{data.get('input_voltage', 'N/A')}V",
                    'Output Voltage': f"{data.get('output_voltage', 'N/A')}V",
                    'Input Frequency': f"{data.get('input_frequency', 'N/A')}Hz",
                    'Output Frequency': f"{data.get('output_frequency', 'N/A')}Hz",
                    'Battery Voltage': f"{data.get('battery_voltage', 'N/A')}V",
                    'Battery SOC': f"{data.get('battery_percentage', 'N/A')}%",
                    'Load Power': f"{data.get('load_active_power', 'N/A')}W",
                    'Temperature': f"{data.get('temperature', 'N/A')}°C",
                    'Solar Voltage': f"{data.get('solar_voltage', 'N/A')}V",
                    'Solar Current': f"{data.get('solar_current', 'N/A')}A"
                }
                
                for key, value in key_data.items():
                    print(f"{key}: {value}")
                
                # Verify inverter characteristics
                print("\n🔍 INVERTER VERIFICATION:")
                print("-" * 25)
                
                # Check model
                model = data.get('model', '')
                if 'RIV1230RCH' in str(model):
                    print("✅ Correct inverter model detected")
                else:
                    print(f"⚠️  Model: {model} (expected RIV1230RCH-SPS)")
                
                # Check AC voltages
                input_v = data.get('input_voltage')
                output_v = data.get('output_voltage')
                if input_v and isinstance(input_v, (int, float)) and 100 <= input_v <= 150:
                    print(f"✅ Input voltage reasonable: {input_v}V")
                else:
                    print(f"⚠️  Input voltage: {input_v}V")
                    
                if output_v and isinstance(output_v, (int, float)) and 100 <= output_v <= 150:
                    print(f"✅ Output voltage reasonable: {output_v}V")
                else:
                    print(f"⚠️  Output voltage: {output_v}V")
                
                # Check frequency
                input_freq = data.get('input_frequency')
                if input_freq and isinstance(input_freq, (int, float)) and 50 <= input_freq <= 65:
                    print(f"✅ Input frequency reasonable: {input_freq}Hz")
                else:
                    print(f"⚠️  Input frequency: {input_freq}Hz")
                
                # Check battery
                battery_v = data.get('battery_voltage')
                if battery_v and isinstance(battery_v, (int, float)) and 10 <= battery_v <= 16:
                    print(f"✅ Battery voltage reasonable: {battery_v}V")
                else:
                    print(f"⚠️  Battery voltage: {battery_v}V")
                
                # Save results
                results_file = Path("results/simple_inverter_test.json")
                results_file.parent.mkdir(exist_ok=True)
                
                test_results = {
                    'timestamp': datetime.now().isoformat(),
                    'device_address': device_address,
                    'test_status': 'success',
                    'data': data
                }
                
                with open(results_file, 'w') as f:
                    json.dump(test_results, f, indent=2, default=str)
                
                print(f"\n💾 Results saved: {results_file}")
                
                print("\n🎉 TEST SUCCESSFUL!")
                print("Integration ready for Home Assistant setup!")
                return True
                
            else:
                print("❌ No data received from inverter")
                return False
                
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test exception:")
        return False
    
    finally:
        # Cleanup
        try:
            if 'client' in locals() and client:
                await client.disconnect()
                print("🔌 Disconnected from device")
        except Exception as e:
            print(f"⚠️  Disconnect error: {e}")

def main():
    """Main execution"""
    print("Starting inverter test...")
    success = asyncio.run(test_inverter_connection())
    
    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Go to Home Assistant: Settings → Devices & Services")
        print("2. Click 'Add Integration'")
        print("3. Search for 'BluPow'")
        print("4. Configure with MAC: D8:B6:73:BF:4F:75")
        print("5. Verify all 22 sensors appear and populate with data")
        return 0
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check inverter is powered on")
        print("2. Verify Bluetooth is enabled")
        print("3. Ensure no other apps are connected to inverter")
        print("4. Check MAC address: D8:B6:73:BF:4F:75")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 