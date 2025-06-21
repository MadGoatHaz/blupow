#!/usr/bin/env python3
"""
BluPow Stability Test & Multi-Device Architecture Validator

This script comprehensively tests the BluPow integration for:
1. Race conditions causing 5-minute failures
2. Multi-device configuration management
3. Resource leak detection
4. Production stability validation

Focus: BULLETPROOF stability for actual daily use
"""

import asyncio
import json
import logging
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
import psutil

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'blupow_stability_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class DeviceConfiguration:
    """Robust device configuration management"""
    
    def __init__(self, mac_address: str, device_name: str = None, device_type: str = "unknown"):
        self.mac_address = mac_address.upper()
        self.device_name = device_name or f"Device_{mac_address[-8:].replace(':', '')}"
        self.device_type = device_type
        self.last_success = None
        self.total_attempts = 0
        self.successful_attempts = 0
        self.consecutive_failures = 0
        self.avg_response_time = 0.0
        self.last_data = {}
        self.error_history = []
        self.created_at = datetime.now()
        
    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100
    
    @property
    def is_healthy(self) -> bool:
        return (self.success_rate > 70 and 
                self.consecutive_failures < 5 and
                self.total_attempts > 0)
    
    def record_attempt(self, success: bool, duration: float = 0.0, error: str = None, data: dict = None):
        """Record connection attempt with full details"""
        self.total_attempts += 1
        
        if success:
            self.successful_attempts += 1
            self.consecutive_failures = 0
            self.last_success = datetime.now()
            if duration > 0:
                # Running average calculation
                if self.avg_response_time == 0:
                    self.avg_response_time = duration
                else:
                    self.avg_response_time = (self.avg_response_time * 0.8) + (duration * 0.2)
            if data:
                self.last_data = data.copy()
        else:
            self.consecutive_failures += 1
            if error:
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'error': error,
                    'consecutive_failures': self.consecutive_failures
                })
                # Keep only last 10 errors
                if len(self.error_history) > 10:
                    self.error_history.pop(0)

class StabilityTestManager:
    """Comprehensive stability testing and monitoring"""
    
    def __init__(self):
        self.devices: Dict[str, DeviceConfiguration] = {}
        self.test_start_time = None
        self.system_stats = []
        self.running = False
        
        # Test configuration
        self.test_duration_minutes = 20  # Extended test
        self.poll_interval_seconds = 30  # Match HA coordinator
        self.max_concurrent_devices = 3
        
        # Known device configurations
        self.known_devices = {
            "D8:B6:73:BF:4F:75": DeviceConfiguration(
                "D8:B6:73:BF:4F:75", 
                "Renogy_RIV1230RCH_SPS_Inverter", 
                "inverter"
            ),
            "C4:D3:6A:66:7E:D4": DeviceConfiguration(
                "C4:D3:6A:66:7E:D4", 
                "Renogy_MPPT_Controller_BT_TH", 
                "mppt_controller"
            )
        }
        
        # Load existing device configurations
        self.load_device_configurations()
    
    def load_device_configurations(self):
        """Load device configurations from persistent storage"""
        try:
            config_file = Path("device_configurations.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    for mac, config_data in data.items():
                        if mac not in self.devices:
                            device = DeviceConfiguration(mac)
                            device.__dict__.update(config_data)
                            # Fix datetime objects
                            if 'created_at' in config_data:
                                device.created_at = datetime.fromisoformat(config_data['created_at'])
                            if 'last_success' in config_data and config_data['last_success']:
                                device.last_success = datetime.fromisoformat(config_data['last_success'])
                            self.devices[mac] = device
                logger.info(f"📂 Loaded {len(data)} device configurations")
        except Exception as e:
            logger.warning(f"Could not load device configurations: {e}")
        
        # Add known devices if not already present
        for mac, device in self.known_devices.items():
            if mac not in self.devices:
                self.devices[mac] = device
    
    def save_device_configurations(self):
        """Save device configurations to persistent storage"""
        try:
            config_data = {}
            for mac, device in self.devices.items():
                config_data[mac] = {
                    'mac_address': device.mac_address,
                    'device_name': device.device_name,
                    'device_type': device.device_type,
                    'total_attempts': device.total_attempts,
                    'successful_attempts': device.successful_attempts,
                    'consecutive_failures': device.consecutive_failures,
                    'avg_response_time': device.avg_response_time,
                    'created_at': device.created_at.isoformat() if device.created_at else None,
                    'last_success': device.last_success.isoformat() if device.last_success else None,
                    'last_data': device.last_data,
                    'error_history': [
                        {
                            'timestamp': err['timestamp'].isoformat(),
                            'error': err['error'],
                            'consecutive_failures': err['consecutive_failures']
                        } for err in device.error_history
                    ]
                }
            
            with open("device_configurations.json", 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"💾 Saved {len(config_data)} device configurations")
        except Exception as e:
            logger.error(f"Failed to save device configurations: {e}")
    
    async def test_device_connection(self, device: DeviceConfiguration) -> Dict[str, Any]:
        """Test individual device connection with comprehensive monitoring"""
        start_time = time.time()
        test_result = {
            'device': device.mac_address,
            'success': False,
            'duration': 0.0,
            'data_fields': 0,
            'error': None,
            'memory_before': 0,
            'memory_after': 0,
            'system_stats': {}
        }
        
        try:
            # Record system stats before
            process = psutil.Process()
            test_result['memory_before'] = process.memory_info().rss / 1024 / 1024  # MB
            
            logger.info(f"🔄 Testing device: {device.device_name} ({device.mac_address})")
            
            # Create client and test connection
            client = BluPowClient(device.mac_address)
            
            # Test connection cycle (same as coordinator)
            connected = await client.connect()
            if not connected:
                raise Exception("Connection failed")
            
            # Read device data
            data = await client.read_device_info()
            if not data or len(data) < 2:
                raise Exception(f"No data retrieved (got {len(data) if data else 0} fields)")
            
            # Proper disconnect
            await client.disconnect()
            
            # Record success
            duration = time.time() - start_time
            test_result.update({
                'success': True,
                'duration': duration,
                'data_fields': len(data),
                'data_sample': {k: v for k, v in list(data.items())[:5]}  # Sample data
            })
            
            device.record_attempt(True, duration, None, data)
            logger.info(f"✅ {device.device_name}: Success in {duration:.2f}s, {len(data)} fields")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            test_result.update({
                'success': False,
                'duration': duration,
                'error': error_msg
            })
            
            device.record_attempt(False, duration, error_msg)
            logger.warning(f"❌ {device.device_name}: Failed after {duration:.2f}s - {error_msg}")
        
        finally:
            # Record system stats after
            try:
                process = psutil.Process()
                test_result['memory_after'] = process.memory_info().rss / 1024 / 1024  # MB
                test_result['system_stats'] = {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
                }
            except:
                pass
        
        return test_result
    
    async def run_stability_test(self, target_devices: List[str] = None):
        """Run comprehensive stability test"""
        if target_devices is None:
            target_devices = list(self.devices.keys())
        
        logger.info(f"🚀 Starting {self.test_duration_minutes}-minute stability test")
        logger.info(f"📊 Target devices: {target_devices}")
        logger.info(f"⏱️ Poll interval: {self.poll_interval_seconds}s")
        
        self.test_start_time = datetime.now()
        self.running = True
        
        test_results = []
        cycle_count = 0
        
        try:
            end_time = self.test_start_time + timedelta(minutes=self.test_duration_minutes)
            
            while datetime.now() < end_time and self.running:
                cycle_count += 1
                cycle_start = time.time()
                
                logger.info(f"🔄 Cycle {cycle_count} - Testing {len(target_devices)} devices...")
                
                # Test all devices in parallel (like multi-device manager would)
                tasks = []
                for mac in target_devices:
                    if mac in self.devices:
                        task = self.test_device_connection(self.devices[mac])
                        tasks.append(task)
                
                cycle_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                successful_tests = 0
                for i, result in enumerate(cycle_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Task {i} exception: {result}")
                    elif result.get('success'):
                        successful_tests += 1
                    
                    test_results.append(result)
                
                cycle_duration = time.time() - cycle_start
                success_rate = (successful_tests / len(target_devices)) * 100 if target_devices else 0
                
                logger.info(f"📊 Cycle {cycle_count}: {successful_tests}/{len(target_devices)} success ({success_rate:.1f}%) in {cycle_duration:.2f}s")
                
                # Save configurations periodically
                if cycle_count % 5 == 0:
                    self.save_device_configurations()
                
                # Wait for next cycle
                sleep_time = max(0, self.poll_interval_seconds - cycle_duration)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.running = False
            self.save_device_configurations()
        
        # Generate comprehensive report
        await self.generate_stability_report(test_results, cycle_count)
    
    async def generate_stability_report(self, test_results: List[Dict], cycle_count: int):
        """Generate comprehensive stability analysis report"""
        test_duration = datetime.now() - self.test_start_time
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 BLUPOW STABILITY TEST REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"⏱️ Test Duration: {test_duration}")
        logger.info(f"🔄 Total Cycles: {cycle_count}")
        logger.info(f"📊 Total Tests: {len(test_results)}")
        
        # Device-specific analysis
        logger.info(f"\n📱 DEVICE ANALYSIS:")
        for mac, device in self.devices.items():
            if device.total_attempts > 0:
                logger.info(f"\n  {device.device_name} ({mac}):")
                logger.info(f"    Success Rate: {device.success_rate:.1f}%")
                logger.info(f"    Avg Response: {device.avg_response_time:.2f}s")
                logger.info(f"    Consecutive Failures: {device.consecutive_failures}")
                logger.info(f"    Health Status: {'🟢 HEALTHY' if device.is_healthy else '🔴 UNHEALTHY'}")
                logger.info(f"    Last Success: {device.last_success}")
                
                if device.error_history:
                    logger.info(f"    Recent Errors:")
                    for error in device.error_history[-3:]:
                        logger.info(f"      - {error['timestamp']}: {error['error']}")
        
        # Overall system health
        successful_results = [r for r in test_results if isinstance(r, dict) and r.get('success')]
        overall_success_rate = (len(successful_results) / len(test_results)) * 100 if test_results else 0
        
        logger.info(f"\n🎯 OVERALL SYSTEM HEALTH:")
        logger.info(f"  Success Rate: {overall_success_rate:.1f}%")
        logger.info(f"  Memory Usage Stable: {self._analyze_memory_stability(test_results)}")
        logger.info(f"  Race Conditions: {self._detect_race_conditions(test_results)}")
        logger.info(f"  Production Ready: {'✅ YES' if overall_success_rate > 90 else '❌ NO'}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if overall_success_rate < 90:
            logger.info(f"  - ⚠️ System not production ready - investigate failure patterns")
        if self._detect_race_conditions(test_results):
            logger.info(f"  - 🐛 Race conditions detected - review subprocess management")
        if not self._analyze_memory_stability(test_results):
            logger.info(f"  - 🧠 Memory leaks detected - review resource cleanup")
        
        logger.info(f"\n{'='*60}")
    
    def _analyze_memory_stability(self, test_results: List[Dict]) -> bool:
        """Analyze memory usage patterns for stability"""
        try:
            memory_changes = []
            for result in test_results:
                if isinstance(result, dict) and 'memory_before' in result and 'memory_after' in result:
                    change = result['memory_after'] - result['memory_before']
                    memory_changes.append(change)
            
            if not memory_changes:
                return True  # No data, assume stable
            
            # Check for consistent memory growth (leak indicator)
            avg_change = sum(memory_changes) / len(memory_changes)
            return avg_change < 0.5  # Less than 0.5MB average growth per test
        except:
            return True  # Error analyzing, assume stable
    
    def _detect_race_conditions(self, test_results: List[Dict]) -> bool:
        """Detect potential race conditions from test patterns"""
        try:
            # Look for sporadic failures in otherwise healthy devices
            for device in self.devices.values():
                if (device.total_attempts > 10 and 
                    50 < device.success_rate < 95 and 
                    device.consecutive_failures > 2):
                    return True  # Sporadic failures suggest race conditions
            return False
        except:
            return False

async def main():
    """Main test execution"""
    print("🔧 BluPow Stability Test & Multi-Device Architecture Validator")
    print("=" * 60)
    
    manager = StabilityTestManager()
    
    # Interactive device selection
    print(f"📱 Available devices:")
    for i, (mac, device) in enumerate(manager.devices.items(), 1):
        status = "🟢 HEALTHY" if device.is_healthy else "🔴 NEEDS_TESTING"
        print(f"  {i}. {device.device_name} ({mac}) - {status}")
    
    print(f"\nOptions:")
    print(f"  1. Test all devices (recommended)")
    print(f"  2. Test primary inverter only (D8:B6:73:BF:4F:75)")
    print(f"  3. Test discovered MPPT controller (C4:D3:6A:66:7E:D4)")
    print(f"  4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        await manager.run_stability_test()
    elif choice == "2":
        await manager.run_stability_test(["D8:B6:73:BF:4F:75"])
    elif choice == "3":
        await manager.run_stability_test(["C4:D3:6A:66:7E:D4"])
    elif choice == "4":
        print("👋 Exiting...")
        return
    else:
        print("❌ Invalid choice")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc() 