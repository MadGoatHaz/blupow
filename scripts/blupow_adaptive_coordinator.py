#!/usr/bin/env python3
"""
BluPow Adaptive Coordinator - Next Generation Multi-Device Management
Intelligently discovers, tests, and optimally manages multiple Bluetooth power devices
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import sys

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Supported device types"""
    BT_TH = "bt_th"  # Temperature/Humidity sensor (like your current device)
    BT_1 = "bt_1"    # BT-1 Module (MPPT Controllers)
    BT_2 = "bt_2"    # BT-2 Module (Advanced Controllers)
    BATTERY = "battery"  # Smart Batteries
    INVERTER = "inverter"  # Smart Inverters
    SHUNT = "shunt"  # Smart Shunts
    UNKNOWN = "unknown"

class DeviceStatus(Enum):
    """Device operational status"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISCOVERING = "discovering"
    OPTIMIZING = "optimizing"

@dataclass
class DeviceProfile:
    """Profile for a discovered device"""
    mac_address: str
    name: str
    device_type: DeviceType
    rssi: int
    last_seen: datetime
    
    # Connection characteristics
    optimal_interval: float = 30.0
    connection_success_rate: float = 0.0
    average_connection_time: float = 0.0
    data_field_count: int = 0
    
    # Adaptive timing
    min_interval: float = 15.0
    max_interval: float = 300.0
    current_interval: float = 30.0
    consecutive_failures: int = 0
    
    # Performance metrics
    total_attempts: int = 0
    successful_attempts: int = 0
    last_successful_poll: Optional[datetime] = None
    recent_response_times: List[float] = field(default_factory=list)
    
    # Device-specific data
    last_data: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    firmware_version: Optional[str] = None
    model: Optional[str] = None
    
    @property
    def status(self) -> DeviceStatus:
        """Determine current device status"""
        if self.total_attempts == 0:
            return DeviceStatus.DISCOVERING
        
        if self.connection_success_rate < 0.3:
            return DeviceStatus.FAILED
        elif self.connection_success_rate < 0.7:
            return DeviceStatus.DEGRADED
        else:
            return DeviceStatus.ACTIVE
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if self.total_attempts == 0:
            return 0.0
        
        success_score = self.connection_success_rate * 40
        timing_score = min(30, (30 - min(30, self.average_connection_time)) * 2)
        consistency_score = min(20, len(self.recent_response_times) * 2)
        recency_score = 10 if self.last_successful_poll and \
                       (datetime.now() - self.last_successful_poll).seconds < 300 else 0
        
        return success_score + timing_score + consistency_score + recency_score

class AdaptiveCoordinator:
    """Intelligent multi-device coordinator with adaptive timing"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.devices: Dict[str, DeviceProfile] = {}
        self.config_file = config_file
        self.running = False
        self.discovery_active = False
        
        # Adaptive parameters
        self.global_health_threshold = 70.0
        self.optimization_interval = 300  # 5 minutes
        self.discovery_interval = 600    # 10 minutes
        
        # Performance tracking
        self.start_time = datetime.now()
        self.total_polls = 0
        self.successful_polls = 0
        
        logger.info("🚀 BluPow Adaptive Coordinator initialized")
    
    async def discover_devices(self) -> List[DeviceProfile]:
        """Discover all compatible Bluetooth power devices"""
        logger.info("🔍 Starting intelligent device discovery...")
        
        try:
            from bleak import BleakScanner
            
            # Scan for devices
            devices = await BleakScanner.discover(timeout=15.0)
            discovered = []
            
            # Known device patterns
            device_patterns = {
                DeviceType.BT_TH: ["BT-TH-", "BTTH"],
                DeviceType.BT_1: ["BT-1-", "BT1"],
                DeviceType.BT_2: ["BT-2-", "BT2"],
                DeviceType.BATTERY: ["RBT", "BAT-"],
                DeviceType.INVERTER: ["RIV", "INV-", "BTRIC"],
                DeviceType.SHUNT: ["SHUNT", "RSH"]
            }
            
            for device in devices:
                if not device.name:
                    continue
                
                # Identify device type
                device_type = DeviceType.UNKNOWN
                for dtype, patterns in device_patterns.items():
                    if any(pattern in device.name.upper() for pattern in patterns):
                        device_type = dtype
                        break
                
                # Create profile for power-related devices
                if device_type != DeviceType.UNKNOWN:
                    profile = DeviceProfile(
                        mac_address=device.address,
                        name=device.name,
                        device_type=device_type,
                        rssi=getattr(device, 'rssi', -100),
                        last_seen=datetime.now()
                    )
                    discovered.append(profile)
                    logger.info(f"📱 Discovered {device_type.value}: {device.name} ({device.address})")
            
            logger.info(f"🎯 Discovery complete: {len(discovered)} compatible devices found")
            return discovered
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            return []
    
    async def test_device_capabilities(self, profile: DeviceProfile) -> bool:
        """Test device capabilities and determine optimal settings"""
        logger.info(f"🧪 Testing capabilities for {profile.name}")
        
        client = BluPowClient(profile.mac_address)
        test_results = []
        
        try:
            # Test multiple connection attempts with timing
            for attempt in range(3):
                start_time = time.time()
                
                try:
                    connected = await client.connect()
                    if connected:
                        # Read device data
                        data = await client.read_device_info()
                        cached_data = client.get_data()
                        await client.disconnect()
                        
                        connection_time = time.time() - start_time
                        test_results.append({
                            'success': True,
                            'connection_time': connection_time,
                            'data_fields': len(cached_data),
                            'data': cached_data
                        })
                        
                        # Update profile with device info
                        if cached_data:
                            profile.model = cached_data.get('model', 'Unknown')
                            profile.firmware_version = cached_data.get('firmware_version')
                            profile.last_data = cached_data
                            profile.data_field_count = len(cached_data)
                            
                            # Identify capabilities
                            capabilities = []
                            if 'battery_voltage' in cached_data:
                                capabilities.append('battery_monitoring')
                            if 'pv_voltage' in cached_data:
                                capabilities.append('solar_monitoring')
                            if 'load_power' in cached_data:
                                capabilities.append('load_monitoring')
                            if 'power_generation_today' in cached_data:
                                capabilities.append('daily_statistics')
                            
                            profile.capabilities = capabilities
                        
                        logger.info(f"  ✅ Attempt {attempt + 1}: {connection_time:.1f}s, {len(cached_data)} fields")
                    else:
                        test_results.append({'success': False, 'connection_time': 30.0})
                        logger.info(f"  ❌ Attempt {attempt + 1}: Connection failed")
                
                except Exception as e:
                    test_results.append({'success': False, 'connection_time': 30.0})
                    logger.warning(f"  ❌ Attempt {attempt + 1}: {e}")
                
                # Wait between attempts
                if attempt < 2:
                    await asyncio.sleep(10)
            
            # Analyze results
            successful_tests = [r for r in test_results if r['success']]
            if successful_tests:
                profile.connection_success_rate = len(successful_tests) / len(test_results)
                profile.average_connection_time = statistics.mean([r['connection_time'] for r in successful_tests])
                profile.recent_response_times = [r['connection_time'] for r in successful_tests]
                
                # Calculate optimal interval based on connection time and device type
                base_interval = max(30, profile.average_connection_time * 3)
                if profile.device_type == DeviceType.BT_TH:
                    profile.optimal_interval = max(30, base_interval)
                elif profile.device_type in [DeviceType.BT_1, DeviceType.BT_2]:
                    profile.optimal_interval = max(60, base_interval * 1.5)
                else:
                    profile.optimal_interval = max(45, base_interval * 1.2)
                
                profile.current_interval = profile.optimal_interval
                profile.last_successful_poll = datetime.now()
                
                logger.info(f"🎯 {profile.name} capabilities test complete:")
                logger.info(f"  📊 Success rate: {profile.connection_success_rate*100:.0f}%")
                logger.info(f"  ⏱️ Avg connection: {profile.average_connection_time:.1f}s")
                logger.info(f"  🔄 Optimal interval: {profile.optimal_interval:.0f}s")
                logger.info(f"  🎛️ Capabilities: {', '.join(profile.capabilities)}")
                
                return True
            else:
                logger.warning(f"❌ {profile.name} failed all capability tests")
                return False
                
        except Exception as e:
            logger.error(f"❌ Capability testing failed for {profile.name}: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        active_devices = [p for p in self.devices.values() if p.status == DeviceStatus.ACTIVE]
        degraded_devices = [p for p in self.devices.values() if p.status == DeviceStatus.DEGRADED]
        failed_devices = [p for p in self.devices.values() if p.status == DeviceStatus.FAILED]
        
        total_health = statistics.mean([p.health_score for p in self.devices.values()]) if self.devices else 0
        
        return {
            'system_health': total_health,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'total_devices': len(self.devices),
            'active_devices': len(active_devices),
            'degraded_devices': len(degraded_devices),
            'failed_devices': len(failed_devices),
            'total_polls': self.total_polls,
            'successful_polls': self.successful_polls,
            'success_rate': (self.successful_polls / self.total_polls * 100) if self.total_polls > 0 else 0,
            'devices': {
                mac: {
                    'name': profile.name,
                    'type': profile.device_type.value,
                    'status': profile.status.value,
                    'health': profile.health_score,
                    'interval': profile.current_interval,
                    'capabilities': profile.capabilities,
                    'last_data_fields': profile.data_field_count
                }
                for mac, profile in self.devices.items()
            }
        }
    
    async def run_discovery_and_setup(self):
        """Complete discovery and setup process"""
        logger.info("🎯 Starting comprehensive device discovery and setup")
        
        # Discover devices
        discovered = await self.discover_devices()
        
        if not discovered:
            logger.warning("⚠️ No compatible devices found")
            return
        
        # Test each device
        for profile in discovered:
            logger.info(f"🧪 Testing {profile.name}...")
            success = await self.test_device_capabilities(profile)
            
            if success:
                self.devices[profile.mac_address] = profile
                logger.info(f"✅ {profile.name} added to active devices")
            else:
                logger.warning(f"❌ {profile.name} failed capability tests")
        
        logger.info(f"🎉 Setup complete: {len(self.devices)} devices ready for monitoring")
        
        # Print summary
        status = self.get_system_status()
        logger.info("📊 System Status:")
        logger.info(f"  Active devices: {status['active_devices']}")
        logger.info(f"  System health: {status['system_health']:.0f}%")
        
        for mac, device_info in status['devices'].items():
            logger.info(f"  📱 {device_info['name']}: {device_info['status']} (Health: {device_info['health']:.0f}%)")

async def main():
    """Main execution function"""
    coordinator = AdaptiveCoordinator()
    
    try:
        await coordinator.run_discovery_and_setup()
        
        if coordinator.devices:
            logger.info("🔄 Starting monitoring loop...")
            status = coordinator.get_system_status()
            print("\n" + "="*60)
            print("🎯 BLUPOW ADAPTIVE COORDINATOR STATUS")
            print("="*60)
            print(json.dumps(status, indent=2))
        else:
            logger.warning("⚠️ No devices available for monitoring")
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Coordinator error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
