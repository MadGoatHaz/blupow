#!/usr/bin/env python3
"""
BluPow Universal Device Discovery and Management System

This is the mega-tool that transforms BluPow into a smart, auto-discovering,
multi-device ecosystem manager for all Renogy and compatible devices.

Features:
- Auto-discovery of all Bluetooth devices in range
- Device identification and capability detection
- Optimal timing analysis for each device type
- User-friendly device selection interface
- Automatic configuration generation
- Multi-device polling strategy optimization
"""

import asyncio
import logging
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from bleak import BleakScanner, BleakClient

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

@dataclass
class DeviceCapabilities:
    """Device capability information"""
    device_type: str
    model: str
    data_fields: List[str]
    optimal_interval: float
    connection_time: float
    data_retrieval_time: float
    reliability_score: float
    special_features: List[str]

@dataclass
class DiscoveredDevice:
    """Discovered device information"""
    mac_address: str
    name: str
    rssi: int
    manufacturer_data: Dict[int, bytes]
    service_uuids: List[str]
    is_renogy: bool
    device_type: Optional[str] = None
    capabilities: Optional[DeviceCapabilities] = None
    test_results: Optional[Dict] = None

class RenogyDeviceDatabase:
    """Database of known Renogy device patterns and capabilities"""
    
    KNOWN_PATTERNS = {
        # BT-1 Devices (RS232)
        'BT-TH-': {
            'type': 'BT-1_Module',
            'description': 'Renogy BT-1 Bluetooth Module (RS232)',
            'likely_devices': ['Rover MPPT', 'Wanderer MPPT', 'Adventurer MPPT'],
            'services': ['0000ffd0-0000-1000-8000-00805f9b34fb'],
            'characteristics': {
                'tx': '0000ffd1-0000-1000-8000-00805f9b34fb',
                'rx': '0000fff1-0000-1000-8000-00805f9b34fb'
            }
        },
        
        # BT-2 Devices (RS485)
        'BT-2-': {
            'type': 'BT-2_Module', 
            'description': 'Renogy BT-2 Bluetooth Module (RS485)',
            'likely_devices': ['40A MPPT Controller', 'DC-DC Charger', 'Smart Battery'],
            'services': ['0000ffd0-0000-1000-8000-00805f9b34fb'],
            'characteristics': {
                'tx': '0000ffd1-0000-1000-8000-00805f9b34fb',
                'rx': '0000fff1-0000-1000-8000-00805f9b34fb'
            }
        },
        
        # Built-in Bluetooth Devices
        'RBT': {
            'type': 'Smart_Battery',
            'description': 'Renogy Smart Battery with Built-in Bluetooth',
            'likely_devices': ['RBT100LFP12-BT', 'RBT200LFP12-BT'],
            'services': ['0000ffd0-0000-1000-8000-00805f9b34fb'],
            'data_fields': ['voltage', 'current', 'capacity', 'temperature', 'cell_voltages']
        },
        
        'RIV': {
            'type': 'Smart_Inverter',
            'description': 'Renogy Smart Inverter with Built-in Bluetooth', 
            'likely_devices': ['RIV1230RCH-SPS', 'RIV4835CSH1S'],
            'services': ['0000ffd0-0000-1000-8000-00805f9b34fb'],
            'data_fields': ['input_voltage', 'output_voltage', 'load_power', 'battery_voltage', 'temperature']
        },
        
        # Third-party compatible devices
        'DRIVE168': {
            'type': 'Compatible_Controller',
            'description': 'Drive168.com compatible MPPT controller',
            'likely_devices': ['Generic MPPT with BT-2'],
            'services': ['0000ffd0-0000-1000-8000-00805f9b34fb'],
            'notes': 'Often found in BT-2 modules on third-party controllers'
        }
    }
    
    @classmethod
    def identify_device(cls, device_name: str, service_uuids: List[str]) -> Dict[str, Any]:
        """Identify device type based on name and services"""
        device_info = {
            'identified': False,
            'confidence': 0.0,
            'type': 'Unknown',
            'description': 'Unknown device',
            'likely_devices': [],
            'notes': []
        }
        
        # Check for Renogy service UUID
        renogy_service = '0000ffd0-0000-1000-8000-00805f9b34fb'
        has_renogy_service = renogy_service in service_uuids
        
        if has_renogy_service:
            device_info['notes'].append('Has Renogy BLE service UUID')
            device_info['confidence'] += 0.5
        
        # Pattern matching on device name
        for pattern, info in cls.KNOWN_PATTERNS.items():
            if pattern in device_name.upper():
                device_info.update({
                    'identified': True,
                    'confidence': min(1.0, device_info['confidence'] + 0.6),
                    'type': info['type'],
                    'description': info['description'],
                    'likely_devices': info['likely_devices']
                })
                
                if 'notes' in info:
                    device_info['notes'].append(info['notes'])
                
                break
        
        return device_info

class DeviceTestSuite:
    """Comprehensive testing suite for discovered devices"""
    
    def __init__(self, mac_address: str, device_info: Dict):
        self.mac_address = mac_address
        self.device_info = device_info
        self.test_results = {}
        
    async def run_comprehensive_tests(self) -> DeviceCapabilities:
        """Run all tests and return device capabilities"""
        logger.info(f"🧪 Starting comprehensive tests for {self.mac_address}")
        
        # Test 1: Basic connectivity
        connectivity = await self._test_connectivity()
        
        # Test 2: Data retrieval capabilities  
        data_caps = await self._test_data_capabilities()
        
        # Test 3: Optimal timing analysis
        timing = await self._test_optimal_timing()
        
        # Test 4: Reliability assessment
        reliability = await self._test_reliability()
        
        # Compile results into capabilities
        capabilities = DeviceCapabilities(
            device_type=self.device_info.get('type', 'Unknown'),
            model=data_caps.get('model', 'Unknown'),
            data_fields=data_caps.get('fields', []),
            optimal_interval=timing.get('optimal_interval', 30.0),
            connection_time=timing.get('avg_connection_time', 0.0),
            data_retrieval_time=timing.get('avg_data_time', 0.0),
            reliability_score=reliability.get('score', 0.0),
            special_features=data_caps.get('special_features', [])
        )
        
        logger.info(f"✅ Tests complete for {self.mac_address}: {capabilities.device_type}")
        return capabilities
    
    async def _test_connectivity(self) -> Dict:
        """Test basic connection capabilities"""
        logger.info(f"🔌 Testing connectivity for {self.mac_address}")
        
        results = {
            'can_connect': False,
            'connection_time': 0.0,
            'connection_stable': False,
            'errors': []
        }
        
        try:
            client = BluPowClient(self.mac_address)
            start_time = time.time()
            
            connected = await client.connect()
            connection_time = time.time() - start_time
            
            results.update({
                'can_connect': connected,
                'connection_time': connection_time
            })
            
            if connected:
                # Test connection stability
                await asyncio.sleep(2.0)
                results['connection_stable'] = client.is_connected
                await client.disconnect()
                
            logger.info(f"🔌 Connectivity test: {'✅ PASS' if connected else '❌ FAIL'}")
            
        except Exception as e:
            results['errors'].append(str(e))
            logger.error(f"❌ Connectivity test error: {e}")
        
        self.test_results['connectivity'] = results
        return results
    
    async def _test_data_capabilities(self) -> Dict:
        """Test data retrieval capabilities and identify available fields"""
        logger.info(f"📊 Testing data capabilities for {self.mac_address}")
        
        results = {
            'can_retrieve_data': False,
            'fields': [],
            'model': 'Unknown',
            'special_features': [],
            'data_quality': 0.0
        }
        
        try:
            client = BluPowClient(self.mac_address)
            connected = await client.connect()
            
            if connected:
                data = client.get_data()
                await client.disconnect()
                
                if data and len(data) > 0:
                    results.update({
                        'can_retrieve_data': True,
                        'fields': list(data.keys()),
                        'model': data.get('model', 'Unknown'),
                        'data_quality': min(1.0, len(data) / 20.0)  # Quality based on field count
                    })
                    
                    # Identify special features
                    if 'charging_status' in data:
                        results['special_features'].append('Charging Control')
                    if 'temperature' in data:
                        results['special_features'].append('Temperature Monitoring')
                    if 'load_power' in data:
                        results['special_features'].append('Load Management')
                    if 'battery_percentage' in data:
                        results['special_features'].append('Battery Monitoring')
                
                logger.info(f"📊 Data test: {'✅ PASS' if results['can_retrieve_data'] else '❌ FAIL'} - {len(results['fields'])} fields")
                
        except Exception as e:
            logger.error(f"❌ Data capabilities test error: {e}")
        
        self.test_results['data_capabilities'] = results
        return results
    
    async def _test_optimal_timing(self) -> Dict:
        """Test optimal timing intervals for this device"""
        logger.info(f"⏱️ Testing optimal timing for {self.mac_address}")
        
        results = {
            'optimal_interval': 30.0,
            'min_safe_interval': 5.0,
            'avg_connection_time': 0.0,
            'avg_data_time': 0.0,
            'timing_tests': []
        }
        
        # Test different intervals
        test_intervals = [1.0, 2.0, 5.0, 10.0]
        
        for interval in test_intervals:
            try:
                # Test rapid cycles with this interval
                cycle_times = []
                success_count = 0
                
                for i in range(3):  # 3 test cycles
                    start_time = time.time()
                    
                    client = BluPowClient(self.mac_address)
                    connected = await client.connect()
                    
                    if connected:
                        data = client.get_data()
                        await client.disconnect()
                        
                        if data:
                            success_count += 1
                            cycle_times.append(time.time() - start_time)
                    
                    if i < 2:  # Don't wait after last cycle
                        await asyncio.sleep(interval)
                
                success_rate = success_count / 3.0
                avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0
                
                test_result = {
                    'interval': interval,
                    'success_rate': success_rate,
                    'avg_cycle_time': avg_cycle_time,
                    'recommended': success_rate >= 0.8  # 80% success rate threshold
                }
                
                results['timing_tests'].append(test_result)
                
                if test_result['recommended'] and interval < results['optimal_interval']:
                    results['optimal_interval'] = max(interval * 2, 5.0)  # Add safety margin
                
                logger.info(f"⏱️ {interval}s interval: {success_rate*100:.0f}% success")
                
            except Exception as e:
                logger.error(f"❌ Timing test error at {interval}s: {e}")
        
        # Calculate averages
        successful_tests = [t for t in results['timing_tests'] if t['success_rate'] > 0]
        if successful_tests:
            results['avg_connection_time'] = sum(t['avg_cycle_time'] for t in successful_tests) / len(successful_tests)
        
        logger.info(f"⏱️ Optimal interval determined: {results['optimal_interval']}s")
        
        self.test_results['timing'] = results
        return results
    
    async def _test_reliability(self) -> Dict:
        """Test device reliability over multiple cycles"""
        logger.info(f"🔄 Testing reliability for {self.mac_address}")
        
        results = {
            'score': 0.0,
            'total_attempts': 0,
            'successful_attempts': 0,
            'avg_response_time': 0.0,
            'stability_rating': 'Unknown'
        }
        
        try:
            response_times = []
            success_count = 0
            total_attempts = 5  # 5 reliability test cycles
            
            for i in range(total_attempts):
                start_time = time.time()
                
                try:
                    client = BluPowClient(self.mac_address)
                    connected = await client.connect()
                    
                    if connected:
                        data = client.get_data()
                        await client.disconnect()
                        
                        if data and len(data) > 5:  # Good data threshold
                            success_count += 1
                            response_times.append(time.time() - start_time)
                
                except Exception:
                    pass  # Count as failure
                
                # Wait between tests
                await asyncio.sleep(3.0)
            
            success_rate = success_count / total_attempts
            avg_response = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Calculate reliability score (0-1)
            reliability_score = success_rate * 0.7 + (0.3 if avg_response < 10.0 else 0.1)
            
            # Determine stability rating
            if reliability_score >= 0.9:
                stability = 'Excellent'
            elif reliability_score >= 0.7:
                stability = 'Good'
            elif reliability_score >= 0.5:
                stability = 'Fair'
            else:
                stability = 'Poor'
            
            results.update({
                'score': reliability_score,
                'total_attempts': total_attempts,
                'successful_attempts': success_count,
                'avg_response_time': avg_response,
                'stability_rating': stability
            })
            
            logger.info(f"🔄 Reliability test: {stability} ({reliability_score*100:.0f}%)")
            
        except Exception as e:
            logger.error(f"❌ Reliability test error: {e}")
        
        self.test_results['reliability'] = results
        return results

class BluPowDiscoveryManager:
    """Main discovery and management system"""
    
    def __init__(self):
        self.discovered_devices: List[DiscoveredDevice] = []
        self.tested_devices: List[DiscoveredDevice] = []
        self.device_database = RenogyDeviceDatabase()
        
    async def discover_all_devices(self, scan_duration: float = 10.0) -> List[DiscoveredDevice]:
        """Discover all Bluetooth devices in range"""
        logger.info(f"🔍 Starting device discovery (scanning for {scan_duration}s)...")
        
        devices = await BleakScanner.discover(timeout=scan_duration, return_adv=True)
        
        discovered = []
        for device, adv_data in devices.items():
            try:
                # Check if this looks like a Renogy device
                device_name = device.name or "Unknown"
                device_address = device.address
                service_uuids = list(adv_data.service_uuids) if adv_data.service_uuids else []
                is_renogy = self._is_likely_renogy_device(device_name, service_uuids)
                
                discovered_device = DiscoveredDevice(
                    mac_address=device_address,
                    name=device_name,
                    rssi=adv_data.rssi,
                    manufacturer_data=dict(adv_data.manufacturer_data) if adv_data.manufacturer_data else {},
                    service_uuids=service_uuids,
                    is_renogy=is_renogy
                )
                
                discovered.append(discovered_device)
                
                if is_renogy:
                    logger.info(f"🎯 Found potential Renogy device: {device_name} ({device_address})")
            except Exception as e:
                logger.warning(f"⚠️  Error processing device {device}: {e}")
                continue
        
        self.discovered_devices = discovered
        renogy_count = sum(1 for d in discovered if d.is_renogy)
        
        logger.info(f"🔍 Discovery complete: {len(discovered)} total devices, {renogy_count} potential Renogy devices")
        return discovered
    
    def _is_likely_renogy_device(self, name: str, service_uuids: List[str]) -> bool:
        """Determine if a device is likely a Renogy device"""
        # Check for Renogy service UUID
        renogy_service = '0000ffd0-0000-1000-8000-00805f9b34fb'
        has_renogy_service = renogy_service in service_uuids
        
        # Check for Renogy name patterns
        renogy_patterns = ['BT-TH-', 'BT-2-', 'RBT', 'RIV', 'RENOGY']
        has_renogy_name = any(pattern in name.upper() for pattern in renogy_patterns)
        
        return has_renogy_service or has_renogy_name
    
    async def test_all_renogy_devices(self) -> List[DiscoveredDevice]:
        """Test all discovered Renogy devices"""
        renogy_devices = [d for d in self.discovered_devices if d.is_renogy]
        
        logger.info(f"🧪 Starting comprehensive testing of {len(renogy_devices)} Renogy devices...")
        
        tested_devices = []
        for device in renogy_devices:
            logger.info(f"🔬 Testing device: {device.name} ({device.mac_address})")
            
            # Identify device type
            device_info = self.device_database.identify_device(device.name, device.service_uuids)
            device.device_type = device_info['type']
            
            # Run comprehensive tests
            test_suite = DeviceTestSuite(device.mac_address, device_info)
            try:
                capabilities = await test_suite.run_comprehensive_tests()
                device.capabilities = capabilities
                device.test_results = test_suite.test_results
                
                tested_devices.append(device)
                logger.info(f"✅ Testing complete for {device.name}")
                
            except Exception as e:
                logger.error(f"❌ Testing failed for {device.name}: {e}")
                device.test_results = {'error': str(e)}
                tested_devices.append(device)  # Include failed tests too
            
            # Wait between device tests to avoid interference
            await asyncio.sleep(2.0)
        
        self.tested_devices = tested_devices
        logger.info(f"🧪 Testing complete: {len(tested_devices)} devices tested")
        return tested_devices
    
    def generate_device_report(self) -> Dict[str, Any]:
        """Generate comprehensive device discovery report"""
        report = {
            'discovery_timestamp': datetime.now().isoformat(),
            'total_devices_found': len(self.discovered_devices),
            'renogy_devices_found': len([d for d in self.discovered_devices if d.is_renogy]),
            'devices_tested': len(self.tested_devices),
            'devices': []
        }
        
        for device in self.tested_devices:
            device_report = {
                'mac_address': device.mac_address,
                'name': device.name,
                'device_type': device.device_type,
                'rssi': device.rssi,
                'identification': self.device_database.identify_device(device.name, device.service_uuids),
                'capabilities': {
                    'model': device.capabilities.model if device.capabilities else 'Unknown',
                    'data_fields': device.capabilities.data_fields if device.capabilities else [],
                    'optimal_interval': device.capabilities.optimal_interval if device.capabilities else 30.0,
                    'reliability_score': device.capabilities.reliability_score if device.capabilities else 0.0,
                    'special_features': device.capabilities.special_features if device.capabilities else []
                } if device.capabilities else None,
                'test_results': device.test_results
            }
            
            report['devices'].append(device_report)
        
        return report
    
    def display_interactive_selection(self) -> List[str]:
        """Display interactive device selection interface"""
        if not self.tested_devices:
            print("❌ No tested devices available for selection")
            return []
        
        print("\n" + "="*80)
        print("🚀 BLUPOW DEVICE DISCOVERY AND SELECTION")
        print("="*80)
        
        print(f"\n📊 DISCOVERY SUMMARY:")
        print(f"   • Total devices found: {len(self.discovered_devices)}")
        print(f"   • Renogy devices identified: {len([d for d in self.discovered_devices if d.is_renogy])}")
        print(f"   • Devices successfully tested: {len([d for d in self.tested_devices if d.capabilities])}")
        
        print(f"\n🎯 AVAILABLE DEVICES:")
        print("-" * 80)
        
        for i, device in enumerate(self.tested_devices):
            status = "✅ READY" if device.capabilities and device.capabilities.reliability_score > 0.5 else "⚠️  ISSUES"
            reliability = f"{device.capabilities.reliability_score*100:.0f}%" if device.capabilities else "Unknown"
            
            print(f"{i+1:2d}. {device.name}")
            print(f"    MAC: {device.mac_address}")
            print(f"    Type: {device.device_type}")
            print(f"    Status: {status} (Reliability: {reliability})")
            
            if device.capabilities:
                print(f"    Model: {device.capabilities.model}")
                print(f"    Data Fields: {len(device.capabilities.data_fields)} available")
                print(f"    Optimal Interval: {device.capabilities.optimal_interval}s")
                if device.capabilities.special_features:
                    print(f"    Features: {', '.join(device.capabilities.special_features)}")
            
            print()
        
        print("📋 SELECTION OPTIONS:")
        print("   • Enter device numbers (comma-separated): 1,3,5")
        print("   • Enter 'all' to select all working devices")
        print("   • Enter 'none' or 'quit' to exit")
        
        while True:
            try:
                selection = input("\n🔧 Select devices to enable: ").strip().lower()
                
                if selection in ['none', 'quit', 'exit']:
                    return []
                
                if selection == 'all':
                    return [d.mac_address for d in self.tested_devices if d.capabilities and d.capabilities.reliability_score > 0.5]
                
                # Parse comma-separated numbers
                selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_macs = []
                
                for idx in selected_indices:
                    if 0 <= idx < len(self.tested_devices):
                        device = self.tested_devices[idx]
                        if device.capabilities and device.capabilities.reliability_score > 0.5:
                            selected_macs.append(device.mac_address)
                            print(f"✅ Selected: {device.name}")
                        else:
                            print(f"⚠️  Skipped {device.name} (reliability issues)")
                    else:
                        print(f"❌ Invalid device number: {idx + 1}")
                
                if selected_macs:
                    return selected_macs
                else:
                    print("❌ No valid devices selected. Please try again.")
                    
            except (ValueError, KeyboardInterrupt):
                print("❌ Invalid input. Please try again or enter 'quit' to exit.")
    
    def generate_home_assistant_config(self, selected_devices: List[str]) -> Dict[str, Any]:
        """Generate Home Assistant configuration for selected devices"""
        config = {
            'blupow': {
                'devices': []
            }
        }
        
        for mac_address in selected_devices:
            device = next((d for d in self.tested_devices if d.mac_address == mac_address), None)
            if device and device.capabilities:
                device_config = {
                    'mac_address': mac_address,
                    'name': device.name,
                    'device_type': device.device_type,
                    'model': device.capabilities.model,
                    'update_interval': int(device.capabilities.optimal_interval),
                    'enabled': True,
                    'special_features': device.capabilities.special_features
                }
                
                config['blupow']['devices'].append(device_config)
        
        return config

async def main():
    """Main discovery and configuration workflow"""
    print("🚀 BluPow Universal Device Discovery System")
    print("=" * 60)
    
    discovery_manager = BluPowDiscoveryManager()
    
    try:
        # Step 1: Discover all devices
        print("\n🔍 STEP 1: Device Discovery")
        await discovery_manager.discover_all_devices(scan_duration=15.0)
        
        renogy_devices = [d for d in discovery_manager.discovered_devices if d.is_renogy]
        if not renogy_devices:
            print("❌ No Renogy devices found. Make sure devices are powered on and in range.")
            return
        
        # Step 2: Test all Renogy devices
        print("\n🧪 STEP 2: Device Testing and Capability Analysis")
        await discovery_manager.test_all_renogy_devices()
        
        # Step 3: Generate report
        print("\n📊 STEP 3: Generating Device Report")
        report = discovery_manager.generate_device_report()
        
        # Save report to file
        report_file = f"blupow_discovery_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {report_file}")
        
        # Step 4: Interactive device selection
        print("\n🎯 STEP 4: Device Selection")
        selected_devices = discovery_manager.display_interactive_selection()
        
        if selected_devices:
            # Step 5: Generate configuration
            print("\n⚙️  STEP 5: Configuration Generation")
            config = discovery_manager.generate_home_assistant_config(selected_devices)
            
            # Save configuration
            config_file = f"blupow_config_{int(time.time())}.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"✅ Configuration saved to: {config_file}")
            print(f"🎯 Selected {len(selected_devices)} devices for BluPow integration")
            
            # Display next steps
            print("\n🚀 NEXT STEPS:")
            print("1. Copy the generated configuration to your Home Assistant config")
            print("2. Restart Home Assistant")
            print("3. Check the BluPow integration for your new devices")
            print("4. Monitor the logs for any issues")
            
        else:
            print("ℹ️  No devices selected. Discovery complete.")
    
    except KeyboardInterrupt:
        print("\n🛑 Discovery interrupted by user")
    except Exception as e:
        logger.error(f"❌ Discovery system error: {e}")
        print(f"❌ An error occurred: {e}")
    
    print("\n✨ BluPow Discovery System Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 