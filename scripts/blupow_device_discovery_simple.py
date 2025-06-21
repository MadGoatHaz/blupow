#!/usr/bin/env python3
"""
BluPow Simple Device Discovery Tool

A streamlined, reliable device discovery system for finding and testing Renogy devices.
"""

import asyncio
import logging
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from bleak import BleakScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blupow_discovery.log')
    ]
)
logger = logging.getLogger(__name__)

class RenogyDevicePatterns:
    """Known Renogy device patterns"""
    
    PATTERNS = {
        'BT-TH-': 'BT-1 Module (Inverter/MPPT)',
        'BT-2-': 'BT-2 Module (40A MPPT)',
        'RBT': 'Smart Battery',
        'RIV': 'Smart Inverter',
        'RENOGY': 'Renogy Device'
    }
    
    @classmethod
    def is_renogy_device(cls, name: str) -> bool:
        """Check if device name matches Renogy patterns"""
        name_upper = name.upper()
        return any(pattern in name_upper for pattern in cls.PATTERNS.keys())
    
    @classmethod
    def get_device_type(cls, name: str) -> str:
        """Get device type description"""
        name_upper = name.upper()
        for pattern, description in cls.PATTERNS.items():
            if pattern in name_upper:
                return description
        return 'Unknown Renogy Device'

async def discover_devices(scan_duration: float = 10.0):
    """Discover all Bluetooth devices"""
    print(f"🔍 Scanning for devices ({scan_duration}s)...")
    
    devices = await BleakScanner.discover(timeout=scan_duration)
    
    print(f"\n📡 Found {len(devices)} Bluetooth devices:")
    renogy_devices = []
    
    for device in devices:
        device_name = device.name or "Unknown"
        is_renogy = RenogyDevicePatterns.is_renogy_device(device_name)
        
        print(f"  {'🎯' if is_renogy else '📱'} {device_name} ({device.address}) RSSI: {device.rssi}")
        
        if is_renogy:
            device_type = RenogyDevicePatterns.get_device_type(device_name)
            renogy_devices.append({
                'mac_address': device.address,
                'name': device_name,
                'device_type': device_type,
                'rssi': device.rssi
            })
    
    return renogy_devices

async def test_device(device_info):
    """Test a single device for connectivity and data retrieval"""
    mac_address = device_info['mac_address']
    name = device_info['name']
    
    print(f"\n🔬 Testing {name} ({mac_address})...")
    
    test_results = {
        'mac_address': mac_address,
        'name': name,
        'device_type': device_info['device_type'],
        'rssi': device_info['rssi'],
        'working': False,
        'model': 'Unknown',
        'data_fields': 0,
        'connection_time': 0.0,
        'sample_data': {},
        'error': None
    }
    
    try:
        client = BluPowClient(mac_address)
        start_time = time.time()
        
        # Test connection
        connected = await client.connect()
        connection_time = time.time() - start_time
        
        if connected:
            print(f"  ✅ Connected in {connection_time:.1f}s")
            
            # Test data retrieval
            data = client.get_data()
            await client.disconnect()
            
            if data and len(data) > 5:
                print(f"  📊 Retrieved {len(data)} data fields")
                print(f"  📋 Model: {data.get('model', 'Unknown')}")
                
                # Sample some key data points
                sample_keys = ['model', 'battery_voltage', 'load_power', 'output_voltage', 'input_voltage']
                sample_data = {k: data.get(k) for k in sample_keys if k in data}
                
                test_results.update({
                    'working': True,
                    'model': data.get('model', 'Unknown'),
                    'data_fields': len(data),
                    'connection_time': connection_time,
                    'sample_data': sample_data
                })
                
                print(f"  ✅ Device is WORKING and ready for BluPow!")
                print(f"  📋 Sample data: {sample_data}")
                
            else:
                print(f"  ❌ No data retrieved")
                test_results['error'] = 'No data retrieved'
        else:
            print(f"  ❌ Connection failed")
            test_results['error'] = 'Connection failed'
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        test_results['error'] = str(e)
    
    return test_results

async def test_connection_timing(device_info):
    """Test optimal connection timing for a device"""
    mac_address = device_info['mac_address']
    name = device_info['name']
    
    print(f"\n⏱️ Testing connection timing for {name}...")
    
    # Test multiple quick connections to find optimal timing
    intervals = [2.0, 5.0, 10.0]
    timing_results = []
    
    for interval in intervals:
        print(f"  Testing {interval}s interval...")
        success_count = 0
        total_time = 0.0
        
        for i in range(3):  # 3 test cycles
            try:
                start_time = time.time()
                
                client = BluPowClient(mac_address)
                connected = await client.connect()
                
                if connected:
                    data = client.get_data()
                    await client.disconnect()
                    
                    if data and len(data) > 5:
                        success_count += 1
                        total_time += time.time() - start_time
                
                if i < 2:  # Wait between tests
                    await asyncio.sleep(interval)
                    
            except Exception:
                pass  # Count as failure
        
        success_rate = success_count / 3.0
        avg_time = total_time / success_count if success_count > 0 else 0.0
        
        timing_results.append({
            'interval': interval,
            'success_rate': success_rate,
            'avg_time': avg_time
        })
        
        print(f"    {interval}s: {success_rate*100:.0f}% success, {avg_time:.1f}s avg")
    
    # Find optimal interval
    best_interval = 30.0  # Default
    for result in timing_results:
        if result['success_rate'] >= 0.8:  # 80% success threshold
            best_interval = max(result['interval'] * 2, 10.0)  # Add safety margin
            break
    
    print(f"  🎯 Recommended interval: {best_interval}s")
    return best_interval

async def main():
    """Main discovery workflow"""
    print("🚀 BluPow Simple Device Discovery")
    print("=" * 50)
    
    try:
        # Step 1: Discover devices
        renogy_devices = await discover_devices(scan_duration=10.0)
        
        if not renogy_devices:
            print("\n❌ No Renogy devices found!")
            print("   • Make sure devices are powered on")
            print("   • Check Bluetooth range (~10m)")
            print("   • Ensure no other apps are connected")
            return
        
        print(f"\n🎯 Found {len(renogy_devices)} Renogy devices")
        
        # Step 2: Test each device
        print("\n🧪 Testing devices...")
        working_devices = []
        
        for device_info in renogy_devices:
            test_result = await test_device(device_info)
            
            if test_result['working']:
                # Test timing for working devices
                optimal_interval = await test_connection_timing(device_info)
                test_result['optimal_interval'] = optimal_interval
                working_devices.append(test_result)
            
            # Wait between device tests
            await asyncio.sleep(3.0)
        
        # Step 3: Generate report
        if working_devices:
            print(f"\n🚀 DISCOVERY COMPLETE!")
            print(f"Found {len(working_devices)} working devices:")
            
            for i, device in enumerate(working_devices, 1):
                print(f"\n{i}. {device['name']}")
                print(f"   MAC: {device['mac_address']}")
                print(f"   Type: {device['device_type']}")
                print(f"   Model: {device['model']}")
                print(f"   Data Fields: {device['data_fields']}")
                print(f"   Connection Time: {device['connection_time']:.1f}s")
                print(f"   Optimal Interval: {device['optimal_interval']}s")
                print(f"   Sample Data: {device['sample_data']}")
            
            # Save report
            report = {
                'discovery_timestamp': datetime.now().isoformat(),
                'working_devices': working_devices,
                'total_devices_found': len(renogy_devices)
            }
            
            report_file = f"blupow_discovery_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📄 Report saved to: {report_file}")
            
            # Generate basic Home Assistant config
            print(f"\n⚙️ Home Assistant Configuration:")
            print("Add this to your configuration.yaml:")
            print()
            print("blupow:")
            for device in working_devices:
                print(f"  - mac_address: \"{device['mac_address']}\"")
                print(f"    name: \"{device['name']}\"")
                print(f"    update_interval: {int(device['optimal_interval'])}")
                print()
            
            print("🎯 These devices are ready for BluPow!")
            
        else:
            print("\n❌ No working devices found")
            print("Check device power, Bluetooth connectivity, and range")
    
    except KeyboardInterrupt:
        print("\n🛑 Discovery interrupted")
    except Exception as e:
        print(f"\n❌ Discovery error: {e}")
        logger.error(f"Discovery error: {e}")
    
    print("\n✨ Discovery complete!")

if __name__ == "__main__":
    asyncio.run(main()) 