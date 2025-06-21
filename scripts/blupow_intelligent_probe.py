#!/usr/bin/env python3
"""
🚀 BLUPOW INTELLIGENT PROBE 🚀
Your Vision Made Real: The Smart Bluetooth Device Manager

This system embodies your vision:
- "WOW users with automated functionality"
- "Work SMART and adapt to situations" 
- "Record all information for pattern identification"
- "Find and manage pollable Bluetooth entities"
- "Keep track of devices and come-and-go patterns"

The INTELLIGENT PROBE that finds what works and adapts!
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bleak import BleakScanner, BleakClient
from blupow_client import BluPowClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeviceIntelligence:
    """Smart device profile with learning capabilities"""
    mac_address: str
    name: str = "Unknown"
    
    # Discovery patterns
    discovery_count: int = 0
    first_seen: datetime = None
    last_seen: datetime = None
    discovery_pattern: List[datetime] = None
    
    # Connection intelligence
    connection_attempts: int = 0
    successful_connections: int = 0
    connection_pattern: List[bool] = None
    
    # Data retrieval intelligence  
    data_attempts: int = 0
    successful_data_retrievals: int = 0
    data_field_counts: List[int] = None
    
    # Adaptive learning
    optimal_retry_interval: int = 30
    confidence_score: float = 0.0
    device_category: str = "unknown"
    
    # Smart recommendations
    recommended_action: str = "investigate"
    user_friendly_status: str = "analyzing"
    
    def __post_init__(self):
        if self.discovery_pattern is None:
            self.discovery_pattern = []
        if self.connection_pattern is None:
            self.connection_pattern = []
        if self.data_field_counts is None:
            self.data_field_counts = []
        if self.first_seen is None:
            self.first_seen = datetime.now()

class IntelligentBluetoothProbe:
    """🧠 The Smart BluPow Probe - Adapts and Learns"""
    
    def __init__(self):
        self.device_intelligence: Dict[str, DeviceIntelligence] = {}
        self.session_start = datetime.now()
        self.scan_count = 0
        self.probe_intelligence_file = Path("probe_intelligence.json")
        
        # Load existing intelligence
        self.load_intelligence()
        
        logger.info("🧠 Intelligent BluPow Probe initialized - Ready to adapt and learn!")

    def load_intelligence(self):
        """Load existing device intelligence"""
        if self.probe_intelligence_file.exists():
            try:
                with open(self.probe_intelligence_file, 'r') as f:
                    data = json.load(f)
                
                for mac, device_data in data.get('devices', {}).items():
                    # Convert datetime strings back
                    if device_data.get('first_seen'):
                        device_data['first_seen'] = datetime.fromisoformat(device_data['first_seen'])
                    if device_data.get('last_seen'):
                        device_data['last_seen'] = datetime.fromisoformat(device_data['last_seen'])
                    
                    # Convert list fields properly
                    for field in ['discovery_pattern', 'connection_pattern', 'data_field_counts']:
                        if field not in device_data:
                            device_data[field] = []
                    
                    self.device_intelligence[mac] = DeviceIntelligence(**device_data)
                
                logger.info(f"📚 Loaded intelligence for {len(self.device_intelligence)} devices")
            except Exception as e:
                logger.warning(f"Could not load intelligence: {e}")

    def save_intelligence(self):
        """Save device intelligence for learning"""
        data = {
            'session_start': self.session_start.isoformat(),
            'last_updated': datetime.now().isoformat(),
            'scan_count': self.scan_count,
            'devices': {}
        }
        
        for mac, intelligence in self.device_intelligence.items():
            device_data = asdict(intelligence)
            # Convert datetime objects to strings  
            device_data['first_seen'] = intelligence.first_seen.isoformat()
            device_data['last_seen'] = intelligence.last_seen.isoformat()
            # Convert datetime lists to strings
            device_data['discovery_pattern'] = [dt.isoformat() for dt in intelligence.discovery_pattern]
            data['devices'][mac] = device_data
        
        with open(self.probe_intelligence_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def intelligent_discovery(self) -> List[DeviceIntelligence]:
        """Smart discovery that learns device patterns"""
        logger.info("🔍 Starting intelligent discovery - learning device patterns...")
        
        self.scan_count += 1
        devices = await BleakScanner.discover(timeout=15)
        
        current_time = datetime.now()
        discovered_this_scan = []
        
        for device in devices:
            mac = device.address
            name = device.name or "Unknown"
            
            if mac not in self.device_intelligence:
                # New device discovered
                self.device_intelligence[mac] = DeviceIntelligence(
                    mac_address=mac,
                    name=name,
                    first_seen=current_time,
                    last_seen=current_time
                )
                logger.info(f"🆕 New device discovered: {name} ({mac})")
            else:
                # Update existing device
                intelligence = self.device_intelligence[mac]
                intelligence.last_seen = current_time
                intelligence.name = name  # Update name if it changed
            
            # Record discovery pattern
            intelligence = self.device_intelligence[mac]
            intelligence.discovery_count += 1
            intelligence.discovery_pattern.append(current_time)
            
            # Keep only recent discovery pattern (last 20)
            if len(intelligence.discovery_pattern) > 20:
                intelligence.discovery_pattern.pop(0)
            
            discovered_this_scan.append(intelligence)
        
        logger.info(f"📡 Discovered {len(discovered_this_scan)} devices this scan")
        
        # Update intelligence for all devices
        self.update_device_intelligence()
        self.save_intelligence()
        
        return discovered_this_scan

    def update_device_intelligence(self):
        """Update intelligence and recommendations for all devices"""
        for intelligence in self.device_intelligence.values():
            self.analyze_device_patterns(intelligence)
            self.generate_smart_recommendations(intelligence)

    def analyze_device_patterns(self, intelligence: DeviceIntelligence):
        """Analyze patterns and update confidence scores"""
        # Discovery pattern analysis
        if len(intelligence.discovery_pattern) >= 3:
            # Device appears consistently
            intelligence.confidence_score += 0.2
            if intelligence.discovery_count >= 5:
                intelligence.device_category = "stable"
        
        # Connection success analysis
        if intelligence.connection_attempts > 0:
            success_rate = intelligence.successful_connections / intelligence.connection_attempts
            intelligence.confidence_score = success_rate * 0.6
            
            if success_rate > 0.8:
                intelligence.device_category = "reliable"
            elif success_rate > 0.3:
                intelligence.device_category = "intermittent"
            else:
                intelligence.device_category = "problematic"
        
        # Data retrieval analysis
        if intelligence.successful_data_retrievals > 0:
            intelligence.confidence_score += 0.3
            
            # Analyze data consistency
            if intelligence.data_field_counts:
                avg_fields = sum(intelligence.data_field_counts) / len(intelligence.data_field_counts)
                if avg_fields > 10:
                    intelligence.device_category = "rich_data"

    def generate_smart_recommendations(self, intelligence: DeviceIntelligence):
        """Generate intelligent recommendations based on patterns"""
        # Target devices (Renogy)
        is_target_device = any(keyword in intelligence.name.lower() for keyword in 
                             ['bt-th', 'btric', 'renogy', 'solar'])
        
        if is_target_device:
            if intelligence.successful_connections > 0:
                intelligence.recommended_action = "use_for_monitoring"
                intelligence.user_friendly_status = "✅ Ready for Home Assistant"
            elif intelligence.connection_attempts == 0:
                intelligence.recommended_action = "test_connection"  
                intelligence.user_friendly_status = "🧪 Test connectivity"
            elif intelligence.connection_attempts > 3 and intelligence.successful_connections == 0:
                intelligence.recommended_action = "troubleshoot_pairing"
                intelligence.user_friendly_status = "🔧 Check pairing mode"
            else:
                intelligence.recommended_action = "retry_connection"
                intelligence.user_friendly_status = "🔄 Retry connection"
        else:
            intelligence.recommended_action = "monitor_only"
            intelligence.user_friendly_status = "📱 Non-target device"

    async def intelligent_connectivity_test(self, intelligence: DeviceIntelligence) -> bool:
        """Smart connectivity testing with adaptive strategies"""
        logger.info(f"🧪 Testing connectivity for {intelligence.name} ({intelligence.mac_address})")
        
        intelligence.connection_attempts += 1
        
        try:
            # Try different connection strategies based on device category
            if intelligence.device_category == "problematic":
                # Use longer timeout for problematic devices
                timeout = 20
            else:
                timeout = 10
            
            # Test with BluPowClient first
            client = BluPowClient(intelligence.mac_address)
            connected = await asyncio.wait_for(client.connect(), timeout=timeout)
            
            if connected:
                intelligence.successful_connections += 1
                intelligence.connection_pattern.append(True)
                
                # Try to get data
                intelligence.data_attempts += 1
                try:
                    await client.read_device_info()
                    data = client.get_data()
                    
                    if data and len(data) > 2:
                        intelligence.successful_data_retrievals += 1
                        intelligence.data_field_counts.append(len(data))
                        logger.info(f"✅ {intelligence.name}: {len(data)} data fields")
                        
                        await client.disconnect()
                        return True
                    else:
                        logger.warning(f"⚠️ {intelligence.name}: Connected but no data")
                except Exception as e:
                    logger.warning(f"⚠️ {intelligence.name}: Connection OK, data error: {e}")
                
                await client.disconnect()
            else:
                intelligence.connection_pattern.append(False)
                logger.warning(f"❌ {intelligence.name}: Connection failed")
            
        except asyncio.TimeoutError:
            intelligence.connection_pattern.append(False)
            logger.warning(f"⏰ {intelligence.name}: Connection timeout")
        except Exception as e:
            intelligence.connection_pattern.append(False)
            logger.warning(f"❌ {intelligence.name}: Error - {e}")
        
        # Keep only recent connection pattern
        if len(intelligence.connection_pattern) > 10:
            intelligence.connection_pattern.pop(0)
        
        return False

    async def generate_intelligence_report(self) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        
        # Categorize devices
        target_devices = []
        working_devices = []
        problematic_devices = []
        
        for intelligence in self.device_intelligence.values():
            is_target = any(keyword in intelligence.name.lower() for keyword in 
                          ['bt-th', 'btric', 'renogy', 'solar'])
            
            if is_target:
                target_devices.append(intelligence)
                
                if intelligence.successful_data_retrievals > 0:
                    working_devices.append(intelligence)
                elif intelligence.connection_attempts > 2 and intelligence.successful_connections == 0:
                    problematic_devices.append(intelligence)
        
        report = {
            'session_info': {
                'started': self.session_start.isoformat(),
                'duration_minutes': (datetime.now() - self.session_start).total_seconds() / 60,
                'scans_performed': self.scan_count
            },
            'discovery_summary': {
                'total_devices': len(self.device_intelligence),
                'target_devices': len(target_devices),
                'working_devices': len(working_devices),
                'problematic_devices': len(problematic_devices)
            },
            'working_devices': [
                {
                    'name': d.name,
                    'mac': d.mac_address,
                    'data_fields': d.data_field_counts[-1] if d.data_field_counts else 0,
                    'success_rate': (d.successful_connections / d.connection_attempts * 100) if d.connection_attempts > 0 else 0,
                    'recommendation': d.recommended_action,
                    'status': d.user_friendly_status
                }
                for d in working_devices
            ],
            'problematic_devices': [
                {
                    'name': d.name,
                    'mac': d.mac_address,
                    'attempts': d.connection_attempts,
                    'recommendation': d.recommended_action,
                    'status': d.user_friendly_status
                }
                for d in problematic_devices
            ],
            'recommendations': self.generate_user_recommendations(working_devices, problematic_devices)
        }
        
        return report

    def generate_user_recommendations(self, working_devices: List[DeviceIntelligence], 
                                    problematic_devices: List[DeviceIntelligence]) -> List[str]:
        """Generate actionable user recommendations"""
        recommendations = []
        
        if working_devices:
            recommendations.append(f"✅ {len(working_devices)} device(s) ready for Home Assistant monitoring")
            for device in working_devices:
                recommendations.append(f"   • Configure HA with MAC: {device.mac_address} ({device.name})")
        
        if problematic_devices:
            recommendations.append(f"🔧 {len(problematic_devices)} device(s) need troubleshooting:")
            for device in problematic_devices:
                if "pairing" in device.recommended_action:
                    recommendations.append(f"   • {device.name}: Check if device needs pairing mode")
                elif "troubleshoot" in device.recommended_action:
                    recommendations.append(f"   • {device.name}: Verify power and Bluetooth settings")
        
        if not working_devices and not problematic_devices:
            recommendations.append("🔍 No Renogy devices found - check device power and range")
        
        return recommendations

    async def run_intelligent_probe(self):
        """Main intelligent probe execution - your vision in action!"""
        logger.info("🚀 STARTING INTELLIGENT BLUPOW PROBE")
        logger.info("   This system will WOW you with its adaptive intelligence!")
        
        try:
            # Phase 1: Intelligent Discovery
            logger.info("🔍 Phase 1: Intelligent Device Discovery")
            discovered_devices = await self.intelligent_discovery()
            
            # Phase 2: Smart Connectivity Testing
            logger.info("🧪 Phase 2: Intelligent Connectivity Testing")
            target_devices = [d for d in discovered_devices if any(keyword in d.name.lower() 
                            for keyword in ['bt-th', 'btric', 'renogy', 'solar'])]
            
            for device in target_devices:
                await self.intelligent_connectivity_test(device)
                await asyncio.sleep(2)  # Respectful delay
            
            # Phase 3: Intelligence Analysis
            logger.info("📊 Phase 3: Intelligence Analysis & Recommendations")
            report = await self.generate_intelligence_report()
            
            # Display results
            print("\n" + "="*60)
            print("🧠 INTELLIGENT BLUPOW PROBE RESULTS")  
            print("="*60)
            
            print(f"📡 Session Summary:")
            print(f"   • Scans performed: {report['session_info']['scans_performed']}")
            print(f"   • Total devices found: {report['discovery_summary']['total_devices']}")
            print(f"   • Target devices: {report['discovery_summary']['target_devices']}")
            print(f"   • Working devices: {report['discovery_summary']['working_devices']}")
            
            print(f"\n🎯 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   {rec}")
            
            if report['working_devices']:
                print(f"\n✅ WORKING DEVICES:")
                for device in report['working_devices']:
                    print(f"   • {device['name']} ({device['mac']})")
                    print(f"     Data fields: {device['data_fields']}, Success: {device['success_rate']:.1f}%")
            
            # Save intelligence
            self.save_intelligence()
            
            # Save report
            with open('intelligent_probe_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info("💾 Intelligence saved - system learns and adapts!")
            
        except Exception as e:
            logger.error(f"Probe error: {e}")

async def main():
    """Run the Intelligent BluPow Probe"""
    probe = IntelligentBluetoothProbe()
    await probe.run_intelligent_probe()

if __name__ == "__main__":
    asyncio.run(main()) 