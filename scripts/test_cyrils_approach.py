#!/usr/bin/env python3
"""
Test script for cyrils/renogy-bt approach
Tests: device discovery → connect → read → disconnect → parse
"""
import asyncio
import logging
import sys
import os

# Add the custom_components/blupow path directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'blupow'))

from blupow_client import BluPowClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_cyrils_approach():
    """Test the cyrils/renogy-bt polling approach"""
    print("🚀 Testing BluPow with cyrils/renogy-bt approach")
    print("=" * 60)
    
    # Test devices
    devices = [
        {"mac": "D8:B6:73:BF:4F:75", "name": "RIV1230RCH-SPS Inverter"},
        {"mac": "C4:D3:6A:66:7E:D4", "name": "RNG-CTRL-RVR40 Controller"}
    ]
    
    for device in devices:
        print(f"\n📱 Testing device: {device['name']} ({device['mac']})")
        print("-" * 50)
        
        client = BluPowClient(device['mac'], device['name'])
        
        try:
            # 1. Discovery & Connection
            print("1. Discovery & Connection...")
            connected = await client.connect()
            
            if connected:
                print("✅ Device connected successfully")
                
                # 2. Read Data
                print("2. Reading device data...")
                data = await client.get_data()
                
                # 3. Disconnect is handled by read_device_info
                print("3. Disconnecting...")
                await client.disconnect()
                
                # 4. Parse & Display Results
                print("4. Results:")
                if data:
                    print(f"✅ Data retrieved: {len(data)} fields")
                    print("\n📊 Key measurements:")
                    
                    # Display key fields based on device type
                    if 'battery_voltage' in data:
                        print(f"   Battery Voltage: {data['battery_voltage']} V")
                    if 'battery_percentage' in data:
                        print(f"   Battery SOC: {data['battery_percentage']} %")
                    if 'input_voltage' in data:
                        print(f"   AC Input Voltage: {data['input_voltage']} V")
                    if 'output_voltage' in data:
                        print(f"   AC Output Voltage: {data['output_voltage']} V")
                    if 'load_active_power' in data:
                        print(f"   Load Power: {data['load_active_power']} W")
                    if 'solar_power' in data:
                        print(f"   Solar Power: {data['solar_power']} W")
                    if 'pv_power' in data:
                        print(f"   PV Power: {data['pv_power']} W")
                    if 'charging_status' in data:
                        print(f"   Charging Status: {data['charging_status']}")
                    if 'model' in data:
                        print(f"   Model: {data['model']}")
                    
                    print(f"\n🔍 Full data: {data}")
                    
                else:
                    print("❌ No data retrieved")
                    
            else:
                print("❌ Connection failed - device not found or not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            # Ensure disconnection
            try:
                await client.disconnect()
            except:
                pass
        
        print("\n" + "="*60)

    print("\n🎯 Cyrils approach test complete!")
    print("\nIf devices were found and data retrieved:")
    print("✅ The integration should work properly!")
    print("\nIf devices were not found:")
    print("❌ Check that your devices are:")
    print("   1. Powered on")
    print("   2. Within Bluetooth range")
    print("   3. Not connected to another device")

if __name__ == "__main__":
    asyncio.run(test_cyrils_approach()) 