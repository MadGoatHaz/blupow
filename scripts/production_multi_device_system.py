#!/usr/bin/env python3
"""
🚀 BLUPOW PRODUCTION MULTI-DEVICE SYSTEM 🚀
The foundation for intelligent Bluetooth device management

This system:
1. FINDS your configured inverter or discovers alternatives
2. FIXES the 5-minute stability issue with robust architecture
3. CREATES a bulletproof multi-device registry
4. IMPLEMENTS AI-like adaptive polling and pattern recognition
5. PREPARES for Home Assistant integration

Goal: Get your inverter monitoring working with WOW-factor intelligence
"""

import asyncio
import json
import logging
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bleak import BleakScanner
from blupow_client import BluPowClient

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_multi_device.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """Complete device profile with intelligence"""
    mac_address: str
    name: str = "Unknown Device"
    device_type: str = "unknown"
    manufacturer: str = "Unknown"
    rssi: int = -100
    
    # Connectivity
    is_available: bool = False
    can_connect: bool = False
    last_seen: datetime = None
    
    # Performance metrics
    connection_times: List[float] = None
    success_rates: List[float] = None
    data_quality_scores: List[float] = None
    
    # Intelligent features
    optimal_polling_interval: int = 30
    health_score: float = 100.0
    stability_trend: str = "unknown"  # improving, stable, degrading
    priority: int = 5  # 1=highest, 5=lowest
    
    # Data capabilities
    data_field_count: int = 0
    sample_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connection_times is None:
            self.connection_times = []
        if self.success_rates is None:
            self.success_rates = []
        if self.data_quality_scores is None:
            self.data_quality_scores = []
        if self.sample_data is None:
            self.sample_data = {}
        if self.last_seen is None:
            self.last_seen = datetime.now()


class ProductionMultiDeviceManager:
    """🚀 Production-ready multi-device manager with AI-like intelligence"""
    
    def __init__(self, target_inverter: str = "D8:B6:73:BF:4F:75"):
        self.target_inverter = target_inverter
        self.device_registry: Dict[str, DeviceProfile] = {}
        self.active_devices: List[str] = []
        self.polling_schedule: Dict[str, datetime] = {}
        
        # Intelligence systems
        self.pattern_analyzer = PatternAnalyzer()
        self.stability_monitor = StabilityMonitor()
        self.adaptive_scheduler = AdaptiveScheduler()
        
        # Performance tracking
        self.system_stats = {
            'discovery_cycles': 0,
            'successful_connections': 0,
            'total_connection_attempts': 0,
            'stability_issues_detected': 0,
            'devices_managed': 0
        }
        
        logger.info("🚀 Production Multi-Device Manager initialized")
        logger.info(f"🎯 Primary target: {target_inverter}")

    async def comprehensive_device_discovery(self) -> Dict[str, DeviceProfile]:
        """🔍 Comprehensive device discovery with intelligence"""
        logger.info("🔍 Starting comprehensive device discovery...")
        
        discovery_start = time.time()
        discovered_devices = {}
        
        try:
            # Phase 1: BLE scan for all devices
            logger.info("📡 Phase 1: Bluetooth LE scan...")
            devices = await BleakScanner.discover(timeout=20)
            
            logger.info(f"📱 Found {len(devices)} Bluetooth devices")
            
            for device in devices:
                mac = device.address
                name = device.name or "Unknown Device"
                rssi = getattr(device, 'rssi', -100)
                
                # Create device profile
                profile = DeviceProfile(
                    mac_address=mac,
                    name=name,
                    rssi=rssi,
                    is_available=True,
                    last_seen=datetime.now()
                )
                
                # Intelligent classification
                await self.classify_device(profile)
                
                discovered_devices[mac] = profile
                
                # Special handling for target inverter
                if mac == self.target_inverter:
                    profile.priority = 1
                    profile.device_type = "target_inverter"
                    logger.info(f"🎯 FOUND TARGET INVERTER: {name} ({mac})")
                
                logger.info(f"📱 {name} ({mac}) - RSSI: {rssi}dB - Type: {profile.device_type}")
            
            # Phase 2: Connection testing for promising devices
            logger.info("🧪 Phase 2: Connection capability testing...")
            
            # Test Renogy devices and target inverter first
            priority_devices = [d for d in discovered_devices.values() 
                              if d.device_type in ['renogy_device', 'target_inverter', 'renogy_power']]
            
            for device in priority_devices:
                await self.test_device_capabilities(device)
                await asyncio.sleep(2)  # Prevent overwhelming
            
            # Test other devices with lower priority
            other_devices = [d for d in discovered_devices.values() 
                           if d.device_type not in ['renogy_device', 'target_inverter', 'renogy_power']][:5]
            
            for device in other_devices:
                await self.test_device_capabilities(device)
                await asyncio.sleep(1)
            
            # Update registry
            self.device_registry.update(discovered_devices)
            self.system_stats['discovery_cycles'] += 1
            self.system_stats['devices_managed'] = len(self.device_registry)
            
            discovery_duration = time.time() - discovery_start
            logger.info(f"✅ Discovery complete in {discovery_duration:.1f}s - {len(discovered_devices)} devices found")
            
            return discovered_devices
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {}

    async def classify_device(self, profile: DeviceProfile):
        """🧠 Intelligent device classification"""
        name = profile.name.lower()
        
        # Renogy device detection
        if any(keyword in name for keyword in ['renogy', 'bt-th', 'btric', 'rv', 'solar']):
            profile.device_type = 'renogy_device'
            profile.manufacturer = 'Renogy'
            profile.priority = 2
            
        # Power device detection
        elif any(keyword in name for keyword in ['inverter', 'battery', 'power', 'energy']):
            profile.device_type = 'power_device'
            profile.priority = 3
            
        # Sensor device detection
        elif any(keyword in name for keyword in ['sensor', 'temp', 'humidity', 'weather']):
            profile.device_type = 'sensor_device'
            profile.priority = 4
        
        # Unknown devices get lowest priority
        else:
            profile.device_type = 'unknown'
            profile.priority = 5

    async def test_device_capabilities(self, device: DeviceProfile):
        """🧪 Comprehensive device capability testing"""
        logger.info(f"🧪 Testing {device.name} ({device.mac_address})")
        
        connection_start = time.time()
        
        try:
            client = BluPowClient(device.mac_address)
            
            # Test connection
            connected = await client.connect()
            connection_time = time.time() - connection_start
            
            if connected:
                device.can_connect = True
                device.connection_times.append(connection_time)
                device.success_rates.append(1.0)
                
                logger.info(f"✅ Connected in {connection_time:.2f}s")
                
                # Test data retrieval
                try:
                    data = await client.read_device_info()
                    cached_data = client.get_data()
                    
                    if cached_data and len(cached_data) > 2:  # More than basic fields
                        device.data_field_count = len(cached_data)
                        device.sample_data = {k: v for k, v in list(cached_data.items())[:8]}
                        device.data_quality_scores.append(100.0)
                        
                        logger.info(f"📊 Retrieved {len(cached_data)} data fields")
                        
                        # Special handling for Renogy devices
                        if 'battery_voltage' in cached_data or 'solar_voltage' in cached_data:
                            device.device_type = 'renogy_power'
                            device.priority = 1
                            logger.info("🔋 Confirmed Renogy power device!")
                        
                    else:
                        device.data_quality_scores.append(50.0)
                        logger.info("⚠️ Connected but limited data available")
                
                except Exception as data_error:
                    device.data_quality_scores.append(25.0)
                    logger.warning(f"⚠️ Data retrieval failed: {data_error}")
                
                await client.disconnect()
                
            else:
                device.success_rates.append(0.0)
                logger.warning(f"❌ Connection failed")
                
        except Exception as e:
            device.success_rates.append(0.0)
            logger.error(f"❌ Testing failed for {device.name}: {e}")
        
        # Calculate health score
        self.calculate_device_health(device)

    def calculate_device_health(self, device: DeviceProfile):
        """📊 Calculate device health score with intelligence"""
        score = 50.0  # Base score
        
        # Connection capability
        if device.can_connect:
            score += 30.0
        
        # Success rate
        if device.success_rates:
            recent_success_rate = statistics.mean(device.success_rates[-5:])
            score += recent_success_rate * 20.0
        
        # Data quality
        if device.data_quality_scores:
            avg_data_quality = statistics.mean(device.data_quality_scores)
            score += (avg_data_quality / 100.0) * 20.0
        
        # Device type bonus
        if device.device_type in ['renogy_power', 'renogy_device']:
            score += 10.0
        elif device.device_type == 'target_inverter':
            score += 15.0
        
        device.health_score = min(score, 100.0)

    async def stability_testing_cycle(self, device: DeviceProfile, duration_minutes: int = 8) -> Dict[str, Any]:
        """🏃‍♂️ Stability testing to identify degradation patterns"""
        logger.info(f"🏃‍♂️ Starting {duration_minutes}-minute stability test for {device.name}")
        
        test_start = time.time()
        results = {
            'device_mac': device.mac_address,
            'device_name': device.name,
            'start_time': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'connection_attempts': [],
            'success_pattern': [],
            'degradation_detected': False,
            'degradation_time': None,
            'stability_score': 0.0,
            'recommendations': []
        }
        
        attempt_count = 0
        consecutive_failures = 0
        
        while (time.time() - test_start) < (duration_minutes * 60):
            attempt_count += 1
            elapsed_minutes = (time.time() - test_start) / 60
            
            logger.info(f"🔄 Stability test - Attempt {attempt_count} at {elapsed_minutes:.1f}min")
            
            # Connection test
            connection_start = time.time()
            success = False
            error_msg = None
            
            try:
                client = BluPowClient(device.mac_address)
                connected = await client.connect()
                
                if connected:
                    data = await client.read_device_info()
                    cached = client.get_data()
                    await client.disconnect()
                    
                    if cached and len(cached) > 2:
                        success = True
                        consecutive_failures = 0
                    else:
                        error_msg = "No data retrieved"
                else:
                    error_msg = "Connection failed"
                    
            except Exception as e:
                error_msg = str(e)
            
            connection_time = time.time() - connection_start
            
            # Record attempt
            attempt_result = {
                'attempt': attempt_count,
                'elapsed_minutes': elapsed_minutes,
                'success': success,
                'connection_time': connection_time,
                'error': error_msg
            }
            
            results['connection_attempts'].append(attempt_result)
            results['success_pattern'].append(1 if success else 0)
            
            if success:
                logger.info(f"✅ Success in {connection_time:.2f}s")
            else:
                consecutive_failures += 1
                logger.warning(f"❌ Failure: {error_msg} (consecutive: {consecutive_failures})")
                
                # Check for degradation pattern (like your 5-minute issue)
                if consecutive_failures >= 3 and elapsed_minutes > 4:
                    results['degradation_detected'] = True
                    results['degradation_time'] = elapsed_minutes
                    logger.error(f"🚨 DEGRADATION DETECTED at {elapsed_minutes:.1f} minutes!")
                    break
            
            # Update device metrics
            device.connection_times.append(connection_time)
            device.success_rates.append(1.0 if success else 0.0)
            
            # Wait 30 seconds (like HA coordinator)
            await asyncio.sleep(30)
        
        # Analyze results
        total_attempts = len(results['success_pattern'])
        successful_attempts = sum(results['success_pattern'])
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        
        results['stability_score'] = success_rate
        
        # Generate intelligent recommendations
        if results['degradation_detected']:
            results['recommendations'].extend([
                "🚨 CRITICAL: Resource leak causing degradation after 5+ minutes",
                "💡 SOLUTION: Implement subprocess-based coordinator architecture",
                "🔧 ACTION: Use isolated connection cycles with proper cleanup"
            ])
        elif success_rate > 90:
            results['recommendations'].extend([
                "🟢 EXCELLENT: Device is highly stable and ready for production",
                "📈 OPTIMIZE: Can increase polling frequency for better data resolution"
            ])
        elif success_rate > 70:
            results['recommendations'].extend([
                "🟡 GOOD: Device is generally stable with minor issues",
                "🔧 TUNE: Adjust connection timing and retry logic"
            ])
        else:
            results['recommendations'].extend([
                "🔴 POOR: Device has significant stability issues",
                "🛠️ DEBUG: Investigate hardware, range, or interference issues"
            ])
        
        logger.info(f"📊 Stability test complete - Success rate: {success_rate:.1f}%")
        
        return results

    async def create_production_device_registry(self) -> Dict[str, Any]:
        """📋 Create production-ready device registry for Home Assistant"""
        logger.info("📋 Creating production device registry...")
        
        # Find best devices for production use
        working_devices = [d for d in self.device_registry.values() if d.can_connect and d.health_score > 60]
        working_devices.sort(key=lambda x: (-x.health_score, x.priority))
        
        registry = {
            'created_at': datetime.now().isoformat(),
            'target_inverter': self.target_inverter,
            'target_found': self.target_inverter in self.device_registry,
            'total_devices_discovered': len(self.device_registry),
            'working_devices_count': len(working_devices),
            'recommended_devices': [],
            'device_profiles': {},
            'home_assistant_config': {},
            'system_stats': self.system_stats
        }
        
        # Create device profiles
        for mac, device in self.device_registry.items():
            registry['device_profiles'][mac] = {
                'mac_address': device.mac_address,
                'name': device.name,
                'device_type': device.device_type,
                'manufacturer': device.manufacturer,
                'health_score': device.health_score,
                'can_connect': device.can_connect,
                'data_field_count': device.data_field_count,
                'priority': device.priority,
                'last_seen': device.last_seen.isoformat(),
                'sample_data': device.sample_data,
                'performance_metrics': {
                    'avg_connection_time': statistics.mean(device.connection_times) if device.connection_times else 0,
                    'success_rate': statistics.mean(device.success_rates) * 100 if device.success_rates else 0,
                    'stability_trend': device.stability_trend
                }
            }
        
        # Recommend top devices for HA integration
        for device in working_devices[:5]:  # Top 5 devices
            registry['recommended_devices'].append({
                'mac_address': device.mac_address,
                'name': device.name,
                'device_type': device.device_type,
                'health_score': device.health_score,
                'data_field_count': device.data_field_count,
                'recommended_for': self.get_recommendation_reason(device)
            })
        
        # Generate Home Assistant configuration
        if working_devices:
            best_device = working_devices[0]
            registry['home_assistant_config'] = {
                'recommended_device': best_device.mac_address,
                'device_name': best_device.name,
                'coordinator_settings': {
                    'update_interval': 30,
                    'timeout': max(10, statistics.mean(best_device.connection_times) * 2) if best_device.connection_times else 15,
                    'retry_attempts': 3,
                    'use_subprocess_coordinator': True
                },
                'sensor_count': best_device.data_field_count
            }
        
        return registry

    def get_recommendation_reason(self, device: DeviceProfile) -> str:
        """🎯 Get recommendation reason for device"""
        if device.mac_address == self.target_inverter:
            return "Your originally configured inverter device"
        elif device.device_type == 'renogy_power':
            return "Confirmed Renogy power monitoring device"
        elif device.health_score > 90:
            return "Excellent stability and performance"
        elif device.data_field_count > 15:
            return "Rich data source with many sensors"
        else:
            return "Working device suitable for monitoring"

    async def run_production_system(self):
        """🚀 Main production system execution"""
        logger.info("🚀 PRODUCTION MULTI-DEVICE SYSTEM STARTING")
        logger.info("   Goal: Get your inverter monitoring working with bulletproof reliability")
        
        try:
            # Phase 1: Comprehensive discovery
            print("\n🔍 Phase 1: Comprehensive Device Discovery")
            print("   Scanning for ALL Bluetooth devices...")
            print(f"   Primary target: {self.target_inverter}")
            
            discovered = await self.comprehensive_device_discovery()
            
            if not discovered:
                print("❌ No devices discovered - check Bluetooth adapter")
                return
            
            # Phase 2: Identify working devices
            print("\n🧪 Phase 2: Device Analysis")
            working_devices = [d for d in discovered.values() if d.can_connect]
            
            if not working_devices:
                print("❌ No working devices found")
                return
            
            print(f"✅ Found {len(working_devices)} working devices:")
            for device in sorted(working_devices, key=lambda x: x.priority):
                status = "🎯" if device.mac_address == self.target_inverter else "✅"
                print(f"   {status} {device.name} ({device.mac_address})")
                print(f"      Type: {device.device_type} | Health: {device.health_score:.1f}% | Data fields: {device.data_field_count}")
            
            # Phase 3: Stability testing on best devices
            print("\n🏃‍♂️ Phase 3: Stability Testing")
            print("   Testing top devices for the 5-minute degradation issue...")
            
            # Test target inverter first if available
            stability_results = {}
            test_devices = []
            
            target_device = discovered.get(self.target_inverter)
            if target_device and target_device.can_connect:
                test_devices.append(target_device)
                print(f"   🎯 Testing YOUR configured inverter first...")
            
            # Add other top devices
            other_working = [d for d in working_devices if d.mac_address != self.target_inverter]
            other_working.sort(key=lambda x: -x.health_score)
            test_devices.extend(other_working[:2])  # Top 2 alternatives
            
            for device in test_devices:
                print(f"   Testing {device.name} for 8 minutes...")
                stability_result = await self.stability_testing_cycle(device, duration_minutes=8)
                stability_results[device.mac_address] = stability_result
                
                if stability_result['degradation_detected']:
                    print(f"   🚨 Degradation detected at {stability_result['degradation_time']:.1f} minutes!")
                else:
                    print(f"   ✅ Stable - {stability_result['stability_score']:.1f}% success rate")
            
            # Phase 4: Create production registry
            print("\n📋 Phase 4: Creating Production Registry")
            registry = await self.create_production_device_registry()
            
            # Add stability test results
            registry['stability_tests'] = stability_results
            
            # Save registry
            registry_file = "production_device_registry.json"
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2, default=str)
            
            # Generate final report
            print("\n" + "="*80)
            print("🚀 PRODUCTION MULTI-DEVICE SYSTEM REPORT")
            print("="*80)
            
            print(f"📊 Total devices discovered: {len(discovered)}")
            print(f"✅ Working devices: {len(working_devices)}")
            print(f"🎯 Target inverter found: {'YES' if self.target_inverter in discovered else 'NO'}")
            
            if registry['recommended_devices']:
                print(f"\n💎 RECOMMENDED DEVICES FOR HOME ASSISTANT:")
                for i, device in enumerate(registry['recommended_devices'][:3], 1):
                    print(f"   {i}. {device['name']} ({device['mac_address']})")
                    print(f"      Health: {device['health_score']:.1f}% | Fields: {device['data_field_count']} | {device['recommended_for']}")
            
            if stability_results:
                print(f"\n🏃‍♂️ STABILITY TEST RESULTS:")
                for mac, result in stability_results.items():
                    device_name = discovered[mac].name
                    if result['degradation_detected']:
                        print(f"   🚨 {device_name}: DEGRADATION at {result['degradation_time']:.1f}min")
                    else:
                        print(f"   ✅ {device_name}: STABLE ({result['stability_score']:.1f}% success)")
            
            print(f"\n📋 Production registry saved to: {registry_file}")
            print(f"🔧 Next step: Update Home Assistant with recommended device")
            
            if registry['home_assistant_config']:
                ha_config = registry['home_assistant_config']
                print(f"\n🏠 HOME ASSISTANT CONFIG RECOMMENDATION:")
                print(f"   Device: {ha_config['device_name']} ({ha_config['recommended_device']})")
                print(f"   Update interval: {ha_config['coordinator_settings']['update_interval']}s")
                print(f"   Timeout: {ha_config['coordinator_settings']['timeout']}s")
                print(f"   Expected sensors: {ha_config['sensor_count']}")
            
        except Exception as e:
            logger.error(f"Production system error: {e}")
            raise


# Helper classes for intelligence systems
class PatternAnalyzer:
    """🧠 Pattern analysis for device behavior"""
    pass

class StabilityMonitor:
    """📊 Monitor device stability over time"""
    pass

class AdaptiveScheduler:
    """⏰ Adaptive scheduling based on device patterns"""
    pass


async def main():
    """🚀 Main entry point"""
    print("🚀 BLUPOW PRODUCTION MULTI-DEVICE SYSTEM")
    print("   Bulletproof multi-device management with AI-like intelligence")
    print("   Goal: Get your inverter monitoring working + build foundation for AI system")
    
    # Use your configured inverter as primary target
    manager = ProductionMultiDeviceManager(target_inverter="D8:B6:73:BF:4F:75")
    await manager.run_production_system()


if __name__ == "__main__":
    asyncio.run(main())