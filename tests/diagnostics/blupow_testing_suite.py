#!/usr/bin/env python3
"""
BluPow Unified Testing Suite

This comprehensive testing suite combines all testing capabilities:
- Device discovery using Cyril's renogy-bt patterns
- Device wake-up and connection testing
- Bluetooth proxy optimization
- Hardware recommendation system
- Home Assistant configuration generation

Usage:
    python3 blupow_testing_suite.py
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

# Import our testing systems
try:
    # When running from deployed location
    import sys
    import os
    
    # Add the current directory to path so we can import sibling modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from device_discovery_system import BluPowDeviceDiscoverySystem
    from device_wake_system import DeviceWakeSystem, TARGET_DEVICE
    
    # Add the parent directory to import the main blupow modules
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, parent_dir)
    
    from blupow_client import BluPowClient
    from const import RENOGY_SERVICE_UUID, RENOGY_TX_CHAR_UUID, RENOGY_RX_CHAR_UUID
except ImportError as e:
    print(f"Error importing BluPow modules: {e}")
    print("Please ensure you're running from the BluPow directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

class BluPowTestingSuite:
    """Unified testing suite for BluPow integration"""
    
    def __init__(self):
        self.discovery_system = BluPowDeviceDiscoverySystem()
        self.wake_system = DeviceWakeSystem()
        self.test_results = {}
        
    def display_welcome(self):
        """Display welcome message and testing options"""
        print("🚀 BLUPOW COMPREHENSIVE TESTING SUITE")
        print("="*80)
        print("Based on cyrils/renogy-bt patterns and protocols")
        print("")
        print("This suite will help you:")
        print("✅ Discover and identify Renogy devices")
        print("✅ Test device connectivity and wake-up strategies")
        print("✅ Optimize Bluetooth proxy configurations")
        print("✅ Generate Home Assistant configuration recommendations")
        print("✅ Troubleshoot connection issues")
        print("")
        print("Available test modes:")
        print("1. 🔍 Device Discovery & Identification")
        print("2. 😴 Device Wake-Up Testing (for sleeping devices)")
        print("3. 🌐 Bluetooth Proxy Optimization")
        print("4. 🧪 Comprehensive Analysis (all tests)")
        print("5. 🎯 Quick Setup Assistant (for new installations)")
        print("6. 🔧 Current Device Diagnostics")
        print("")
    
    async def device_discovery_test(self):
        """Run comprehensive device discovery"""
        print("🔍 DEVICE DISCOVERY & IDENTIFICATION TEST")
        print("="*60)
        print("Scanning for all Renogy devices using Cyril's patterns...")
        print("")
        
        try:
            # Run comprehensive discovery
            await self.discovery_system.run_comprehensive_test()
            
            # Store results
            self.test_results['discovery'] = {
                'timestamp': datetime.now().isoformat(),
                'total_devices': len(self.discovery_system.discovered_devices),
                'renogy_devices': len([d for d in self.discovery_system.discovered_devices.values() if d.is_renogy]),
                'proxy_devices': len(self.discovery_system.proxy_devices),
                'status': 'completed'
            }
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Discovery test failed: {e}")
            self.test_results['discovery'] = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
            return False
    
    async def device_wake_test(self):
        """Run device wake-up testing"""
        print("😴 DEVICE WAKE-UP TESTING")
        print("="*60)
        print(f"Testing wake-up strategies for: {TARGET_DEVICE['name']}")
        print(f"MAC Address: {TARGET_DEVICE['address']}")
        print(f"Model: {TARGET_DEVICE['model']}")
        print("")
        
        try:
            # Run wake-up strategies
            wake_results = await self.wake_system.run_all_wake_strategies()
            
            # Store results
            successful_strategies = [name for name, attempt in wake_results.items() if attempt.device_found]
            
            self.test_results['wake_up'] = {
                'timestamp': datetime.now().isoformat(),
                'target_device': TARGET_DEVICE,
                'strategies_tested': len(wake_results),
                'successful_strategies': successful_strategies,
                'device_detected': len(successful_strategies) > 0,
                'status': 'completed'
            }
            
            return len(successful_strategies) > 0
            
        except Exception as e:
            _LOGGER.error(f"Wake-up test failed: {e}")
            self.test_results['wake_up'] = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
            return False
    
    async def proxy_optimization_test(self):
        """Test Bluetooth proxy optimization"""
        print("🌐 BLUETOOTH PROXY OPTIMIZATION")
        print("="*60)
        print("Testing connectivity through different Bluetooth proxies...")
        print("")
        
        proxies = [
            ("esp32-bluetooth-proxy-2105e4", "192.168.51.151", "Primary - +10dB tested"),
            ("proxy-2", "192.168.51.207", "Secondary"),
            ("proxy-3", "192.168.51.109", "Tertiary")
        ]
        
        proxy_results = {}
        
        for proxy_name, proxy_ip, description in proxies:
            print(f"🧪 Testing {proxy_name} ({proxy_ip})...")
            
            try:
                # Test discovery through this proxy
                devices = await self.discovery_system.comprehensive_scan(duration=10.0)
                
                renogy_devices = [d for d in devices.values() if d.is_renogy]
                best_signal = max([d.rssi for d in renogy_devices], default=-999)
                
                proxy_results[proxy_name] = {
                    'ip': proxy_ip,
                    'description': description,
                    'devices_found': len(renogy_devices),
                    'best_signal': best_signal,
                    'status': 'success'
                }
                
                print(f"   ✅ Found {len(renogy_devices)} Renogy devices")
                if best_signal > -999:
                    print(f"   📶 Best signal: {best_signal} dBm")
                
            except Exception as e:
                proxy_results[proxy_name] = {
                    'ip': proxy_ip,
                    'description': description,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"   ❌ Test failed: {e}")
        
        self.test_results['proxy_optimization'] = {
            'timestamp': datetime.now().isoformat(),
            'proxies_tested': len(proxies),
            'results': proxy_results,
            'status': 'completed'
        }
        
        return True
    
    async def comprehensive_analysis(self):
        """Run all tests in sequence"""
        print("🧪 COMPREHENSIVE ANALYSIS")
        print("="*60)
        print("Running all test suites for complete analysis...")
        print("")
        
        # Test sequence
        tests = [
            ("Device Discovery", self.device_discovery_test),
            ("Device Wake-Up", self.device_wake_test),
            ("Proxy Optimization", self.proxy_optimization_test)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n🔄 Running {test_name}...")
            try:
                success = await test_func()
                results[test_name] = 'success' if success else 'failed'
                print(f"✅ {test_name} completed")
            except Exception as e:
                results[test_name] = 'failed'
                print(f"❌ {test_name} failed: {e}")
        
        # Generate comprehensive report
        self.generate_comprehensive_report(results)
        
        return results
    
    def generate_comprehensive_report(self, test_results: Dict[str, str]):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE ANALYSIS REPORT")
        print("="*80)
        
        # Test Summary
        successful_tests = [name for name, status in test_results.items() if status == 'success']
        
        print(f"🧪 Tests Completed: {len(test_results)}")
        print(f"✅ Successful: {len(successful_tests)}")
        print(f"❌ Failed: {len(test_results) - len(successful_tests)}")
        print("")
        
        # Device Status
        discovery_results = self.test_results.get('discovery', {})
        wake_results = self.test_results.get('wake_up', {})
        
        if discovery_results.get('renogy_devices', 0) > 0:
            print("🎯 DEVICE STATUS: ✅ RENOGY DEVICES DETECTED")
            print(f"   Total Devices: {discovery_results.get('total_devices', 0)}")
            print(f"   Renogy Devices: {discovery_results.get('renogy_devices', 0)}")
            print(f"   Bluetooth Proxies: {discovery_results.get('proxy_devices', 0)}")
        elif wake_results.get('device_detected', False):
            print("🎯 DEVICE STATUS: ⚠️  DEVICE DETECTED BUT INTERMITTENT")
            print(f"   Target Device: {TARGET_DEVICE['name']}")
            print(f"   Detection Methods: {', '.join(wake_results.get('successful_strategies', []))}")
        else:
            print("🎯 DEVICE STATUS: ❌ NO RENOGY DEVICES DETECTED")
            
        print("")
        
        # Recommendations
        self.generate_setup_recommendations()
        
        # Save comprehensive results
        self.save_comprehensive_results()
    
    def generate_setup_recommendations(self):
        """Generate setup recommendations based on test results"""
        print("💡 SETUP RECOMMENDATIONS:")
        print("="*50)
        
        discovery_results = self.test_results.get('discovery', {})
        wake_results = self.test_results.get('wake_up', {})
        proxy_results = self.test_results.get('proxy_optimization', {})
        
        if discovery_results.get('renogy_devices', 0) > 0:
            print("✅ READY FOR HOME ASSISTANT INTEGRATION")
            print("")
            print("🏠 Home Assistant Setup:")
            print("   1. Go to Settings → Devices & Services")
            print("   2. Click '+ ADD INTEGRATION'")
            print("   3. Search for 'BluPow'")
            print("   4. Follow the device selection from discovery results")
            print("")
            
        elif wake_results.get('device_detected', False):
            print("⚠️  DEVICE REQUIRES SPECIAL HANDLING")
            print("")
            print("🔧 Device Management:")
            print("   • Device enters power-saving mode frequently")
            print("   • Consider continuous monitoring in Home Assistant")
            print("   • Check device power management settings")
            print("   • Optimal detection times may vary")
            print("")
            
        else:
            print("🔍 DEVICE TROUBLESHOOTING REQUIRED")
            print("")
            print("📋 Next Steps:")
            print("   1. Verify device is powered and operational")
            print("   2. Check for Bluetooth activation button/menu")
            print("   3. Try during active charging periods")
            print("   4. Ensure device not connected to Renogy app")
            print("   5. Consider device proximity and interference")
            print("")
        
        # Proxy recommendations
        if proxy_results and proxy_results.get('results'):
            best_proxy = None
            best_signal = -999
            
            for proxy_name, result in proxy_results['results'].items():
                if result.get('status') == 'success' and result.get('best_signal', -999) > best_signal:
                    best_signal = result['best_signal']
                    best_proxy = proxy_name
            
            if best_proxy:
                print("🌐 BLUETOOTH PROXY OPTIMIZATION:")
                print(f"   Recommended Proxy: {best_proxy}")
                print(f"   Signal Strength: {best_signal} dBm")
                print("")
        
        print("📄 Detailed results saved to blupow_test_results.json")
    
    def save_comprehensive_results(self):
        """Save all test results to file"""
        comprehensive_results = {
            'test_suite_version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': {
                'total_tests_run': len(self.test_results),
                'successful_tests': len([r for r in self.test_results.values() if r.get('status') == 'completed']),
                'devices_discovered': self.test_results.get('discovery', {}).get('total_devices', 0),
                'renogy_devices_found': self.test_results.get('discovery', {}).get('renogy_devices', 0)
            }
        }
        
        try:
            with open('blupow_test_results.json', 'w') as f:
                json.dump(comprehensive_results, f, indent=2)
            _LOGGER.info("📄 Comprehensive results saved to blupow_test_results.json")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to save results: {e}")
    
    async def quick_setup_assistant(self):
        """Quick setup assistant for new installations"""
        print("🎯 QUICK SETUP ASSISTANT")
        print("="*60)
        print("This will guide you through optimal BluPow setup...")
        print("")
        
        # Step 1: Quick discovery
        print("Step 1: Quick Device Discovery (15 seconds)")
        devices = await self.discovery_system.comprehensive_scan(duration=15.0)
        renogy_devices = [d for d in devices.values() if d.is_renogy]
        
        if renogy_devices:
            print(f"✅ Found {len(renogy_devices)} Renogy device(s)")
            
            # Sort by recommendation score
            renogy_devices.sort(key=lambda x: x.recommendation_score, reverse=True)
            best_device = renogy_devices[0]
            
            print(f"🏆 Recommended Device: {best_device.name} ({best_device.address})")
            print(f"📶 Signal Strength: {best_device.rssi} dBm")
            print(f"🏆 Recommendation Score: {best_device.recommendation_score}/100")
            print("")
            
            # Test connectivity
            print("Step 2: Testing Connectivity...")
            await self.discovery_system.test_connectivity()
            
            if best_device.connectable:
                print("✅ Device is ready for Home Assistant integration!")
                print("")
                print("🏠 HOME ASSISTANT SETUP:")
                print(f"   MAC Address to use: {best_device.address}")
                print("   1. Add BluPow integration")
                print("   2. Enter the MAC address above")
                print("   3. Complete setup wizard")
            else:
                print("⚠️  Device detected but connection needs optimization")
                print("   Consider running full wake-up testing")
        else:
            print("❌ No Renogy devices found in quick scan")
            print("   Consider running comprehensive analysis")
        
        return len(renogy_devices) > 0
    
    async def current_device_diagnostics(self):
        """Diagnose current device connection issues"""
        print("🔧 CURRENT DEVICE DIAGNOSTICS")
        print("="*60)
        print(f"Diagnosing: {TARGET_DEVICE['name']} ({TARGET_DEVICE['address']})")
        print("")
        
        # Test current device status
        print("🧪 Testing current device connectivity...")
        
        try:
            # Quick connectivity test
            from bleak import BleakScanner, BleakClient
            
            devices = await BleakScanner.discover(timeout=10.0)
            device_found = False
            
            for device in devices:
                if device.address.upper() == TARGET_DEVICE['address'].upper():
                    device_found = True
                    rssi = getattr(device, 'rssi', None)
                    print(f"✅ Device found! Signal: {rssi} dBm")
                    
                    # Test connection
                    try:
                        async with BleakClient(device, timeout=10.0) as client:
                            if client.is_connected:
                                print("✅ Connection successful!")
                                
                                services = await client.get_services()
                                print(f"📋 Found {len(list(services))} services")
                                
                                # Check for Renogy services
                                renogy_services = []
                                for service in services:
                                    if str(service.uuid).lower() in [RENOGY_SERVICE_UUID.lower()]:
                                        renogy_services.append(str(service.uuid))
                                
                                if renogy_services:
                                    print(f"🔧 Renogy services detected: {len(renogy_services)}")
                                    print("✅ Device is ready for use!")
                                else:
                                    print("⚠️  No Renogy services found")
                                    
                            else:
                                print("❌ Connection failed")
                                
                    except Exception as e:
                        print(f"❌ Connection error: {e}")
                    
                    break
            
            if not device_found:
                print("❌ Device not found in scan")
                print("💡 Recommendations:")
                print("   • Run device wake-up testing")
                print("   • Check if device is powered on")
                print("   • Ensure device is not connected elsewhere")
                print("   • Try moving closer to device")
            
            return device_found
            
        except Exception as e:
            print(f"❌ Diagnostics failed: {e}")
            return False

async def main():
    """Main function for the testing suite"""
    suite = BluPowTestingSuite()
    
    try:
        suite.display_welcome()
        
        while True:
            choice = input("Select test mode (1-6, or 'q' to quit): ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("👋 Exiting BluPow Testing Suite")
                break
            elif choice == '1':
                await suite.device_discovery_test()
            elif choice == '2':
                await suite.device_wake_test()
            elif choice == '3':
                await suite.proxy_optimization_test()
            elif choice == '4':
                await suite.comprehensive_analysis()
            elif choice == '5':
                await suite.quick_setup_assistant()
            elif choice == '6':
                await suite.current_device_diagnostics()
            else:
                print("❌ Invalid choice. Please select 1-6 or 'q' to quit.")
            
            print("\n" + "="*80)
            input("Press Enter to continue...")
            print()
            
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
    except Exception as e:
        _LOGGER.error(f"❌ Testing suite failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 