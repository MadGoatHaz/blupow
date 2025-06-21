#!/usr/bin/env python3
"""
🚀 BLUPOW SUPER PROBE CONTINUOUS MONITOR 🚀
Your Vision Made Real: The Intelligent Bluetooth Ecosystem Manager

This embodies your complete vision:
- "WOW users with automated functionality" 
- "Work SMART and adapt to situations"
- "Record all information for pattern identification"
- "Find and manage pollable Bluetooth entities"
- "Keep track of devices and come-and-go patterns"
- "Frequency analysis - know how often devices do things"

The SUPER PROBE that runs continuously and learns!
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bleak import BleakScanner
from blupow_client import BluPowClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blupow_super_probe_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SuperProbeMonitor:
    """🧠 Continuous Intelligent Bluetooth Ecosystem Monitor"""
    
    def __init__(self):
        self.device_ecosystem = {}
        self.pattern_database = {}
        self.frequency_analytics = {}
        self.wow_factor_events = []
        
        # Configuration
        self.scan_interval = 60  # Scan every minute for device come/go
        self.working_device_check_interval = 30  # Check working devices every 30s
        self.pattern_analysis_interval = 300  # Analyze patterns every 5 minutes
        
        # Intelligence tracking
        self.session_start = datetime.now()
        self.total_scans = 0
        self.devices_discovered_this_session = 0
        self.data_retrievals_successful = 0
        
        # Load existing intelligence
        self.load_ecosystem_intelligence()
        
        logger.info("🚀 BluPow Super Probe Monitor - Continuous Intelligence Active!")

    def load_ecosystem_intelligence(self):
        """Load existing ecosystem intelligence"""
        try:
            if Path("ecosystem_intelligence.json").exists():
                with open("ecosystem_intelligence.json", 'r') as f:
                    data = json.load(f)
                    self.device_ecosystem = data.get('device_ecosystem', {})
                    self.pattern_database = data.get('pattern_database', {})
                    self.frequency_analytics = data.get('frequency_analytics', {})
                logger.info(f"📚 Loaded intelligence for {len(self.device_ecosystem)} devices")
        except Exception as e:
            logger.warning(f"Starting fresh intelligence database: {e}")

    def save_ecosystem_intelligence(self):
        """Save ecosystem intelligence"""
        data = {
            'session_info': {
                'started': self.session_start.isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_scans': self.total_scans,
                'devices_this_session': self.devices_discovered_this_session
            },
            'device_ecosystem': self.device_ecosystem,
            'pattern_database': self.pattern_database,
            'frequency_analytics': self.frequency_analytics,
            'wow_factor_events': self.wow_factor_events[-50:]  # Keep last 50 events
        }
        
        with open("ecosystem_intelligence.json", 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def continuous_discovery_monitor(self):
        """Continuous device discovery with come-and-go tracking"""
        logger.info("🔍 Starting continuous discovery monitor...")
        
        while True:
            try:
                self.total_scans += 1
                scan_start = datetime.now()
                
                # Discover devices
                devices = await BleakScanner.discover(timeout=10)
                current_devices = {device.address: device.name or "Unknown" for device in devices}
                
                # Analyze device come-and-go patterns
                await self.analyze_device_ecosystem_changes(current_devices, scan_start)
                
                # Update frequency analytics
                self.update_frequency_analytics(current_devices, scan_start)
                
                # Save intelligence
                self.save_ecosystem_intelligence()
                
                logger.info(f"🔄 Scan {self.total_scans}: {len(current_devices)} devices, ecosystem intelligence updated")
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Discovery monitor error: {e}")
                await asyncio.sleep(30)

    async def analyze_device_ecosystem_changes(self, current_devices: Dict[str, str], scan_time: datetime):
        """Analyze device ecosystem changes (come and go patterns)"""
        previous_devices = set(self.device_ecosystem.keys())
        current_device_set = set(current_devices.keys())
        
        # New devices (arrived)
        new_devices = current_device_set - previous_devices
        if new_devices:
            for mac in new_devices:
                self.devices_discovered_this_session += 1
                self.device_ecosystem[mac] = {
                    'name': current_devices[mac],
                    'first_seen': scan_time.isoformat(),
                    'last_seen': scan_time.isoformat(),
                    'total_appearances': 1,
                    'device_category': 'unknown',
                    'come_go_pattern': [{'action': 'arrived', 'time': scan_time.isoformat()}]
                }
                
                # Check if it's a Renogy device
                if any(keyword in current_devices[mac].lower() for keyword in ['bt-th', 'btric', 'renogy']):
                    self.device_ecosystem[mac]['device_category'] = 'renogy_target'
                    self.wow_factor_events.append({
                        'type': 'renogy_device_discovered',
                        'device': current_devices[mac],
                        'mac': mac,
                        'time': scan_time.isoformat()
                    })
                    logger.info(f"🎯 WOW! New Renogy device: {current_devices[mac]} ({mac})")
        
        # Disappeared devices
        disappeared_devices = previous_devices - current_device_set
        if disappeared_devices:
            for mac in disappeared_devices:
                if mac in self.device_ecosystem:
                    self.device_ecosystem[mac]['come_go_pattern'].append({
                        'action': 'disappeared', 
                        'time': scan_time.isoformat()
                    })
                    logger.info(f"📤 Device left: {self.device_ecosystem[mac]['name']} ({mac})")
        
        # Update existing devices
        for mac in current_device_set.intersection(previous_devices):
            if mac in self.device_ecosystem:
                self.device_ecosystem[mac]['last_seen'] = scan_time.isoformat()
                self.device_ecosystem[mac]['total_appearances'] += 1

    def update_frequency_analytics(self, current_devices: Dict[str, str], scan_time: datetime):
        """Update frequency analytics - understanding device behavior patterns"""
        hour_of_day = scan_time.hour
        day_of_week = scan_time.weekday()
        
        for mac, name in current_devices.items():
            if mac not in self.frequency_analytics:
                self.frequency_analytics[mac] = {
                    'hourly_frequency': [0] * 24,
                    'daily_frequency': [0] * 7,
                    'peak_activity_hours': [],
                    'consistency_score': 0.0
                }
            
            # Update frequency patterns
            analytics = self.frequency_analytics[mac]
            analytics['hourly_frequency'][hour_of_day] += 1
            analytics['daily_frequency'][day_of_week] += 1
            
            # Calculate peak activity hours
            max_frequency = max(analytics['hourly_frequency'])
            if max_frequency > 0:
                analytics['peak_activity_hours'] = [
                    hour for hour, freq in enumerate(analytics['hourly_frequency'])
                    if freq >= max_frequency * 0.8
                ]

    async def working_device_monitor(self):
        """Monitor working devices and collect data for patterns"""
        logger.info("📊 Starting working device monitor...")
        
        while True:
            try:
                # Get working devices from configuration
                with open("device_configurations.json", 'r') as f:
                    config = json.load(f)
                
                working_devices = [
                    (mac, device_info) for mac, device_info in config.get('supported_devices', {}).items()
                    if device_info.get('enabled', False) and device_info.get('intelligence', {}).get('data_retrieval_success', False)
                ]
                
                for mac, device_info in working_devices:
                    await self.monitor_working_device(mac, device_info)
                
                await asyncio.sleep(self.working_device_check_interval)
                
            except Exception as e:
                logger.error(f"Working device monitor error: {e}")
                await asyncio.sleep(60)

    async def monitor_working_device(self, mac: str, device_info: Dict[str, Any]):
        """Monitor a working device and record patterns"""
        try:
            client = BluPowClient(mac)
            
            # Test connectivity and data retrieval
            connected = await asyncio.wait_for(client.connect(), timeout=10)
            if connected:
                await client.read_device_info()
                data = client.get_data()
                await client.disconnect()
                
                if data and len(data) > 2:
                    self.data_retrievals_successful += 1
                    
                    # Record successful data pattern
                    if mac not in self.pattern_database:
                        self.pattern_database[mac] = {
                            'data_retrieval_pattern': [],
                            'field_count_history': [],
                            'performance_trend': 'stable'
                        }
                    
                    self.pattern_database[mac]['data_retrieval_pattern'].append({
                        'time': datetime.now().isoformat(),
                        'success': True,
                        'field_count': len(data),
                        'response_time': 'fast'  # Could calculate actual time
                    })
                    
                    # Keep only recent patterns (last 100)
                    if len(self.pattern_database[mac]['data_retrieval_pattern']) > 100:
                        self.pattern_database[mac]['data_retrieval_pattern'].pop(0)
                    
                    logger.debug(f"✅ {device_info['name']}: {len(data)} fields retrieved")
        
        except Exception as e:
            logger.debug(f"❌ {device_info['name']}: {e}")

    async def pattern_analysis_engine(self):
        """Analyze patterns and generate insights"""
        logger.info("🧠 Starting pattern analysis engine...")
        
        while True:
            try:
                await self.analyze_ecosystem_patterns()
                await asyncio.sleep(self.pattern_analysis_interval)
            except Exception as e:
                logger.error(f"Pattern analysis error: {e}")
                await asyncio.sleep(60)

    async def analyze_ecosystem_patterns(self):
        """Analyze ecosystem patterns and generate intelligence"""
        current_time = datetime.now()
        
        insights = {
            'device_stability': {},
            'frequency_insights': {},
            'recommendations': []
        }
        
        # Analyze device stability
        for mac, device_data in self.device_ecosystem.items():
            total_appearances = device_data.get('total_appearances', 0)
            come_go_events = len(device_data.get('come_go_pattern', []))
            
            if total_appearances > 10:
                stability_score = max(0, 100 - (come_go_events * 10))
                insights['device_stability'][mac] = {
                    'name': device_data['name'],
                    'stability_score': stability_score,
                    'category': 'stable' if stability_score > 80 else 'intermittent'
                }
        
        # Analyze frequency patterns
        for mac, analytics in self.frequency_analytics.items():
            if mac in self.device_ecosystem:
                peak_hours = analytics.get('peak_activity_hours', [])
                if peak_hours:
                    insights['frequency_insights'][mac] = {
                        'name': self.device_ecosystem[mac]['name'],
                        'peak_hours': peak_hours,
                        'most_active_time': max(peak_hours) if peak_hours else 'unknown'
                    }
        
        # Generate smart recommendations
        renogy_devices = [mac for mac, data in self.device_ecosystem.items() 
                         if data.get('device_category') == 'renogy_target']
        
        if renogy_devices:
            insights['recommendations'].append(f"🎯 {len(renogy_devices)} Renogy device(s) available for monitoring")
        
        # Log insights periodically
        logger.info(f"🧠 Pattern Analysis: {len(insights['device_stability'])} stable devices, "
                   f"{len(insights['frequency_insights'])} with frequency patterns")

    async def run_super_probe_monitor(self):
        """Run the complete Super Probe monitoring system"""
        logger.info("🚀 STARTING BLUPOW SUPER PROBE MONITOR")
        logger.info("   Your vision of intelligent automation is now ACTIVE!")
        
        # Start all monitoring tasks
        tasks = [
            asyncio.create_task(self.continuous_discovery_monitor()),
            asyncio.create_task(self.working_device_monitor()),
            asyncio.create_task(self.pattern_analysis_engine())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Super Probe Monitor stopped by user")
            # Save final intelligence
            self.save_ecosystem_intelligence()
        except Exception as e:
            logger.error(f"Super Probe Monitor error: {e}")

async def main():
    """Launch the Super Probe Monitor"""
    monitor = SuperProbeMonitor()
    await monitor.run_super_probe_monitor()

if __name__ == "__main__":
    asyncio.run(main()) 