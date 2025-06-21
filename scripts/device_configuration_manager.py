#!/usr/bin/env python3
"""
BluPow Device Configuration Manager

ROBUST multi-device architecture with proper indexing:
- Auto-discovery of available devices
- Persistent device configurations  
- Individual device testing and health monitoring
- Clean separation of device profiles
- Production-ready stability testing

Goal: BULLETPROOF device management for actual daily use
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

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'device_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class DeviceProfile:
    """Individual device profile with complete configuration and health tracking"""
    
    def __init__(self, mac_address: str, discovered_name: str = None):
        self.mac_address = mac_address.upper()
        self.discovered_name = discovered_name or f"Device_{mac_address[-8:].replace(':', '')}"
        self.friendly_name = None
        self.device_type = "unknown"
        self.manufacturer = "Unknown"
        self.model = "Unknown"
        self.firmware_version = None
        
        # Configuration
        self.polling_interval = 30  # seconds
        self.connection_timeout = 30  # seconds  
        self.enabled = True
        self.priority = 1  # 1=highest, lower numbers = higher priority
        
        # Health and performance tracking
        self.created_at = datetime.now()
        self.last_seen = None
        self.last_successful_connection = None
        self.last_successful_data = None
        self.total_connection_attempts = 0
        self.successful_connections = 0
        self.consecutive_failures = 0
        self.total_data_retrievals = 0
        self.successful_data_retrievals = 0
        
        # Latest data cache
        self.latest_data = {}
        self.data_schema = {}  # Track what data fields this device provides
        
        # Error tracking
        self.recent_errors = []
        self.error_patterns = {}
        
        # Discovery info
        self.discovery_rssi = None
        self.discovery_timestamp = None
        
    @property
    def connection_success_rate(self) -> float:
        if self.total_connection_attempts == 0:
            return 0.0
        return (self.successful_connections / self.total_connection_attempts) * 100
    
    @property
    def data_success_rate(self) -> float:
        if self.total_data_retrievals == 0:
            return 0.0
        return (self.successful_data_retrievals / self.total_data_retrievals) * 100
    
    @property
    def overall_health(self) -> str:
        if self.total_connection_attempts == 0:
            return "untested"
        
        conn_rate = self.connection_success_rate
        data_rate = self.data_success_rate
        
        if conn_rate >= 90 and data_rate >= 85 and self.consecutive_failures < 3:
            return "excellent"
        elif conn_rate >= 75 and data_rate >= 70 and self.consecutive_failures < 5:
            return "good"  
        elif conn_rate >= 50 and data_rate >= 50 and self.consecutive_failures < 10:
            return "fair"
        else:
            return "poor"
    
    @property
    def is_production_ready(self) -> bool:
        return (self.overall_health in ["excellent", "good"] and 
                self.enabled and
                len(self.latest_data) > 2)
    
    def record_connection_attempt(self, success: bool, duration: float = 0.0, error: str = None):
        """Record connection attempt with full tracking"""
        self.total_connection_attempts += 1
        self.last_seen = datetime.now()
        
        if success:
            self.successful_connections += 1
            self.consecutive_failures = 0
            self.last_successful_connection = datetime.now()
        else:
            self.consecutive_failures += 1
            if error:
                self.recent_errors.append({
                    'timestamp': datetime.now(),
                    'type': 'connection',
                    'error': error,
                    'duration': duration
                })
                # Track error patterns
                error_key = error.split(':')[0]  # Get main error type
                self.error_patterns[error_key] = self.error_patterns.get(error_key, 0) + 1
        
        # Keep recent errors list manageable
        if len(self.recent_errors) > 20:
            self.recent_errors = self.recent_errors[-15:]
    
    def record_data_retrieval(self, success: bool, data: dict = None, error: str = None):
        """Record data retrieval attempt"""
        self.total_data_retrievals += 1
        
        if success and data:
            self.successful_data_retrievals += 1
            self.last_successful_data = datetime.now()
            self.latest_data = data.copy()
            
            # Update data schema (track what fields this device provides)
            for key, value in data.items():
                if key not in self.data_schema:
                    self.data_schema[key] = {
                        'type': type(value).__name__,
                        'first_seen': datetime.now(),
                        'sample_value': value
                    }
        else:
            if error:
                self.recent_errors.append({
                    'timestamp': datetime.now(),
                    'type': 'data_retrieval',
                    'error': error
                })
    
    def update_device_info(self, device_data: dict):
        """Update device information from successful connection"""
        if not device_data:
            return
            
        # Extract device information
        if 'model' in device_data:
            self.model = device_data['model']
        if 'firmware_version' in device_data:
            self.firmware_version = device_data['firmware_version']
        if 'manufacturer' in device_data:
            self.manufacturer = device_data['manufacturer']
            
        # Determine device type from model/name
        model_lower = self.model.lower()
        name_lower = self.discovered_name.lower()
        
        if 'inverter' in model_lower or 'riv' in model_lower:
            self.device_type = "inverter"
        elif 'mppt' in model_lower or 'controller' in model_lower:
            self.device_type = "mppt_controller"
        elif 'bt-th' in name_lower:
            self.device_type = "bt_th_sensor"
        else:
            self.device_type = "renogy_device"
            
        # Set friendly name if not already set
        if not self.friendly_name:
            if self.device_type == "inverter":
                self.friendly_name = f"Renogy Inverter ({self.mac_address[-8:]})"
            elif self.device_type == "mppt_controller":
                self.friendly_name = f"Renogy MPPT Controller ({self.mac_address[-8:]})"
            elif self.device_type == "bt_th_sensor":
                self.friendly_name = f"Renogy BT-TH Sensor ({self.mac_address[-8:]})"
            else:
                self.friendly_name = f"Renogy Device ({self.mac_address[-8:]})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'mac_address': self.mac_address,
            'discovered_name': self.discovered_name,
            'friendly_name': self.friendly_name,
            'device_type': self.device_type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'firmware_version': self.firmware_version,
            'polling_interval': self.polling_interval,
            'connection_timeout': self.connection_timeout,
            'enabled': self.enabled,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_successful_connection': self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            'last_successful_data': self.last_successful_data.isoformat() if self.last_successful_data else None,
            'total_connection_attempts': self.total_connection_attempts,
            'successful_connections': self.successful_connections,
            'consecutive_failures': self.consecutive_failures,
            'total_data_retrievals': self.total_data_retrievals,
            'successful_data_retrievals': self.successful_data_retrievals,
            'latest_data': self.latest_data,
            'data_schema': {k: {**v, 'first_seen': v['first_seen'].isoformat() if isinstance(v.get('first_seen'), datetime) else v.get('first_seen')} for k, v in self.data_schema.items()},
            'recent_errors': [
                {**err, 'timestamp': err['timestamp'].isoformat() if isinstance(err.get('timestamp'), datetime) else err.get('timestamp')} 
                for err in self.recent_errors[-10:]  # Only save last 10 errors
            ],
            'error_patterns': self.error_patterns,
            'discovery_rssi': self.discovery_rssi,
            'discovery_timestamp': self.discovery_timestamp.isoformat() if self.discovery_timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceProfile':
        """Create from dictionary (JSON deserialization)"""
        profile = cls(data['mac_address'], data.get('discovered_name'))
        
        # Restore all fields
        for key, value in data.items():
            if hasattr(profile, key) and key != 'mac_address':
                if key.endswith('_at') or key.endswith('_connection') or key.endswith('_data') or key == 'discovery_timestamp':
                    # Convert ISO strings back to datetime
                    if value:
                        setattr(profile, key, datetime.fromisoformat(value))
                    else:
                        setattr(profile, key, None)
                elif key == 'recent_errors':
                    # Convert error timestamps
                    profile.recent_errors = [
                        {**err, 'timestamp': datetime.fromisoformat(err['timestamp']) if err.get('timestamp') else None}
                        for err in value
                    ]
                elif key == 'data_schema':
                    # Convert schema timestamps
                    profile.data_schema = {
                        k: {**v, 'first_seen': datetime.fromisoformat(v['first_seen']) if v.get('first_seen') else None}
                        for k, v in value.items()
                    }
                else:
                    setattr(profile, key, value)
        
        return profile

class DeviceConfigurationManager:
    """Robust multi-device configuration management"""
    
    def __init__(self, config_file: str = "device_configurations.json"):
        self.config_file = Path(config_file)
        self.devices: Dict[str, DeviceProfile] = {}
        self.discovery_in_progress = False
        
        # Load existing configurations
        self.load_configurations()
    
    def load_configurations(self):
        """Load device configurations from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                for mac, device_data in data.items():
                    self.devices[mac] = DeviceProfile.from_dict(device_data)
                
                logger.info(f"📂 Loaded {len(self.devices)} device configurations")
            else:
                logger.info(f"📂 No existing configuration file found - starting fresh")
        except Exception as e:
            logger.error(f"❌ Failed to load configurations: {e}")
    
    def save_configurations(self):
        """Save device configurations to file"""
        try:
            data = {mac: profile.to_dict() for mac, profile in self.devices.items()}
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"💾 Saved {len(self.devices)} device configurations")
        except Exception as e:
            logger.error(f"❌ Failed to save configurations: {e}")
    
    async def discover_devices(self, timeout: float = 15.0) -> List[DeviceProfile]:
        """Discover available Bluetooth devices and create/update profiles"""
        if self.discovery_in_progress:
            logger.warning("🔍 Discovery already in progress")
            return []
        
        self.discovery_in_progress = True
        discovered_profiles = []
        
        try:
            logger.info(f"🔍 Starting device discovery (timeout: {timeout}s)")
            
            # Use the diagnostics scanning capability
            from diagnostics import scan_devices
            
            devices = await scan_devices(timeout)
            logger.info(f"📱 Found {len(devices)} Bluetooth devices")
            
            # Process discovered devices
            for name, address in devices:
                address = address.upper()
                
                # Check if this looks like a Renogy device
                is_renogy = any(keyword in name.lower() for keyword in ['renogy', 'bt-th', 'riv', 'mppt'])
                
                if is_renogy or address in self.devices:
                    # Create or update device profile
                    if address not in self.devices:
                        profile = DeviceProfile(address, name)
                        self.devices[address] = profile
                        logger.info(f"🆕 Created new device profile: {name} ({address})")
                    else:
                        profile = self.devices[address]
                        if profile.discovered_name != name:
                            profile.discovered_name = name
                            logger.info(f"🔄 Updated device name: {address} -> {name}")
                    
                    # Update discovery info
                    profile.discovery_timestamp = datetime.now()
                    profile.last_seen = datetime.now()
                    
                    discovered_profiles.append(profile)
            
            logger.info(f"✅ Discovery complete: {len(discovered_profiles)} relevant devices found")
            
        except Exception as e:
            logger.error(f"❌ Device discovery failed: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.discovery_in_progress = False
            self.save_configurations()
        
        return discovered_profiles
    
    async def test_device(self, mac_address: str) -> Dict[str, Any]:
        """Comprehensive device testing"""
        if mac_address not in self.devices:
            return {'success': False, 'error': 'Device not found in configuration'}
        
        profile = self.devices[mac_address]
        test_start = time.time()
        
        test_result = {
            'device': mac_address,
            'friendly_name': profile.friendly_name,
            'test_timestamp': datetime.now(),
            'success': False,
            'connection_duration': 0.0,
            'data_retrieval_duration': 0.0,
            'total_duration': 0.0,
            'data_fields': 0,
            'error': None,
            'warnings': []
        }
        
        try:
            logger.info(f"🧪 Testing device: {profile.friendly_name} ({mac_address})")
            
            # Create client
            client = BluPowClient(mac_address)
            
            # Test connection
            connection_start = time.time()
            connected = await client.connect()
            connection_duration = time.time() - connection_start
            
            if not connected:
                raise Exception(f"Connection failed after {connection_duration:.2f}s")
            
            test_result['connection_duration'] = connection_duration
            
            # Test data retrieval
            data_start = time.time()
            device_data = await client.read_device_info()
            data_duration = time.time() - data_start
            
            if not device_data or len(device_data) < 2:
                raise Exception(f"No meaningful data retrieved (got {len(device_data) if device_data else 0} fields)")
            
            # Get cached data
            cached_data = client.get_data()
            
            # Disconnect cleanly
            await client.disconnect()
            
            # Record success
            test_result.update({
                'success': True,
                'data_retrieval_duration': data_duration,
                'total_duration': time.time() - test_start,
                'data_fields': len(cached_data),
                'sample_data': {k: v for k, v in list(cached_data.items())[:5]},
                'device_info': {k: v for k, v in device_data.items() if k in ['model', 'firmware_version', 'manufacturer']}
            })
            
            # Update profile
            profile.record_connection_attempt(True, connection_duration)
            profile.record_data_retrieval(True, cached_data)
            profile.update_device_info(device_data)
            
            logger.info(f"✅ {profile.friendly_name}: SUCCESS - {len(cached_data)} fields in {test_result['total_duration']:.2f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start
            error_msg = str(e)
            
            test_result.update({
                'success': False,
                'total_duration': test_duration,
                'error': error_msg
            })
            
            # Update profile
            profile.record_connection_attempt(False, test_duration, error_msg)
            profile.record_data_retrieval(False, error=error_msg)
            
            logger.error(f"❌ {profile.friendly_name}: FAILED - {error_msg}")
        
        finally:
            self.save_configurations()
        
        return test_result
    
    def get_production_ready_devices(self) -> List[DeviceProfile]:
        """Get list of devices ready for production use"""
        return [profile for profile in self.devices.values() if profile.is_production_ready]
    
    def get_device_summary(self) -> Dict[str, Any]:
        """Get summary of all devices"""
        total_devices = len(self.devices)
        production_ready = len(self.get_production_ready_devices())
        
        health_stats = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'untested': 0}
        type_stats = {}
        
        for profile in self.devices.values():
            health_stats[profile.overall_health] += 1
            type_stats[profile.device_type] = type_stats.get(profile.device_type, 0) + 1
        
        return {
            'total_devices': total_devices,
            'production_ready': production_ready,
            'health_distribution': health_stats,
            'device_types': type_stats,
            'last_discovery': max([p.discovery_timestamp for p in self.devices.values() if p.discovery_timestamp], default=None)
        }
    
    def print_device_status(self):
        """Print comprehensive device status"""
        summary = self.get_device_summary()
        
        print(f"\n{'='*60}")
        print(f"🏠 DEVICE CONFIGURATION STATUS")
        print(f"{'='*60}")
        print(f"📊 Total Devices: {summary['total_devices']}")
        print(f"✅ Production Ready: {summary['production_ready']}")
        print(f"📈 Health Distribution: {summary['health_distribution']}")
        print(f"🔧 Device Types: {summary['device_types']}")
        print()
        
        if not self.devices:
            print(f"❌ No devices configured. Run discovery first.")
            return
        
        print(f"📱 DEVICE DETAILS:")
        for i, (mac, profile) in enumerate(self.devices.items(), 1):
            status_emoji = {"excellent": "🟢", "good": "🟡", "fair": "🟠", "poor": "🔴", "untested": "⚪"}
            
            print(f"\n  {i}. {profile.friendly_name or profile.discovered_name}")
            print(f"     MAC: {mac}")
            print(f"     Type: {profile.device_type.title()}")
            print(f"     Health: {status_emoji[profile.overall_health]} {profile.overall_health.upper()}")
            print(f"     Connection Success: {profile.connection_success_rate:.1f}% ({profile.successful_connections}/{profile.total_connection_attempts})")
            
            if profile.latest_data:
                print(f"     Data Fields: {len(profile.latest_data)}")
                print(f"     Last Data: {profile.last_successful_data}")
            
            if profile.consecutive_failures > 0:
                print(f"     ⚠️ Consecutive Failures: {profile.consecutive_failures}")
            
            print(f"     Production Ready: {'✅ YES' if profile.is_production_ready else '❌ NO'}")

async def main():
    """Main device configuration management interface"""
    print("🔧 BluPow Device Configuration Manager")
    print("Robust multi-device architecture with proper indexing")
    print("=" * 60)
    
    manager = DeviceConfigurationManager()
    
    while True:
        manager.print_device_status()
        
        print(f"\n🎯 ACTIONS:")
        print(f"  1. Discover devices")
        print(f"  2. Test specific device")
        print(f"  3. Test all devices")
        print(f"  4. Enable/disable device")
        print(f"  5. View device details")
        print(f"  6. Export configuration")
        print(f"  7. Exit")
        
        choice = input(f"\nSelect action (1-7): ").strip()
        
        if choice == "1":
            print(f"\n🔍 Starting device discovery...")
            discovered = await manager.discover_devices(timeout=15.0)
            print(f"✅ Discovery complete: {len(discovered)} devices found")
            
        elif choice == "2":
            if not manager.devices:
                print(f"❌ No devices configured. Run discovery first.")
                continue
                
            print(f"\n📱 Available devices:")
            for i, (mac, profile) in enumerate(manager.devices.items(), 1):
                print(f"  {i}. {profile.friendly_name or profile.discovered_name} ({mac})")
            
            try:
                device_num = int(input(f"Select device number: ").strip())
                if 1 <= device_num <= len(manager.devices):
                    mac = list(manager.devices.keys())[device_num - 1]
                    print(f"\n🧪 Testing device...")
                    result = await manager.test_device(mac)
                    
                    if result['success']:
                        print(f"✅ Test successful: {result['data_fields']} fields in {result['total_duration']:.2f}s")
                    else:
                        print(f"❌ Test failed: {result['error']}")
                else:
                    print(f"❌ Invalid device number")
            except ValueError:
                print(f"❌ Invalid input")
                
        elif choice == "3":
            if not manager.devices:
                print(f"❌ No devices configured. Run discovery first.")
                continue
                
            print(f"\n🧪 Testing all {len(manager.devices)} devices...")
            for mac in manager.devices.keys():
                result = await manager.test_device(mac)
                # Results already logged by test_device
            
            print(f"✅ All device tests complete")
            
        elif choice == "4":
            if not manager.devices:
                print(f"❌ No devices configured. Run discovery first.")
                continue
                
            print(f"\n📱 Available devices:")
            for i, (mac, profile) in enumerate(manager.devices.items(), 1):
                status = "✅ ENABLED" if profile.enabled else "❌ DISABLED"
                print(f"  {i}. {profile.friendly_name or profile.discovered_name} ({mac}) - {status}")
            
            try:
                device_num = int(input(f"Select device number: ").strip())
                if 1 <= device_num <= len(manager.devices):
                    mac = list(manager.devices.keys())[device_num - 1]
                    profile = manager.devices[mac]
                    profile.enabled = not profile.enabled
                    status = "ENABLED" if profile.enabled else "DISABLED"
                    print(f"✅ Device {profile.friendly_name} is now {status}")
                    manager.save_configurations()
                else:
                    print(f"❌ Invalid device number")
            except ValueError:
                print(f"❌ Invalid input")
                
        elif choice == "5":
            if not manager.devices:
                print(f"❌ No devices configured. Run discovery first.")
                continue
                
            print(f"\n📱 Available devices:")
            for i, (mac, profile) in enumerate(manager.devices.items(), 1):
                print(f"  {i}. {profile.friendly_name or profile.discovered_name} ({mac})")
            
            try:
                device_num = int(input(f"Select device number: ").strip())
                if 1 <= device_num <= len(manager.devices):
                    mac = list(manager.devices.keys())[device_num - 1]
                    profile = manager.devices[mac]
                    
                    print(f"\n📋 DEVICE DETAILS: {profile.friendly_name}")
                    print(f"   MAC Address: {profile.mac_address}")
                    print(f"   Device Type: {profile.device_type}")
                    print(f"   Model: {profile.model}")
                    print(f"   Manufacturer: {profile.manufacturer}")
                    print(f"   Firmware: {profile.firmware_version}")
                    print(f"   Health: {profile.overall_health}")
                    print(f"   Enabled: {'Yes' if profile.enabled else 'No'}")
                    print(f"   Created: {profile.created_at}")
                    print(f"   Last Seen: {profile.last_seen}")
                    print(f"   Connection Success: {profile.connection_success_rate:.1f}%")
                    print(f"   Data Success: {profile.data_success_rate:.1f}%")
                    print(f"   Data Fields: {len(profile.latest_data)}")
                    
                    if profile.recent_errors:
                        print(f"\n   Recent Errors:")
                        for error in profile.recent_errors[-3:]:
                            print(f"     - {error['timestamp']}: {error['error']}")
                else:
                    print(f"❌ Invalid device number")
            except ValueError:
                print(f"❌ Invalid input")
                
        elif choice == "6":
            export_file = f"device_config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            manager.save_configurations()
            print(f"✅ Configuration exported to: {export_file}")
            
        elif choice == "7":
            print(f"👋 Exiting device configuration manager")
            break
            
        else:
            print(f"❌ Invalid choice")
        
        input(f"\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc() 