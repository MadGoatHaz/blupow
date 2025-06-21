#!/usr/bin/env python3
"""
BluPow Multi-Device Manager - Continuous Real-Time Monitoring
Manages multiple Bluetooth power devices with adaptive timing and HA integration
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import signal

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from scripts.blupow_adaptive_coordinator import AdaptiveCoordinator, DeviceProfile, DeviceStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiDeviceManager:
    """Continuous multi-device monitoring with adaptive optimization"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.coordinator = AdaptiveCoordinator(config_file)
        self.running = False
        self.device_tasks: Dict[str, asyncio.Task] = {}
        self.optimization_task: Optional[asyncio.Task] = None
        self.discovery_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.session_start = datetime.now()
        self.total_cycles = 0
        self.successful_cycles = 0
        
        # Home Assistant integration
        self.ha_mqtt_enabled = False
        self.ha_topic_base = "blupow"
        
        logger.info("🚀 BluPow Multi-Device Manager initialized")
    
    async def device_monitoring_loop(self, profile: DeviceProfile):
        """Continuous monitoring loop for a single device"""
        logger.info(f"🔄 Starting monitoring loop for {profile.name}")
        
        while self.running:
            try:
                # Calculate next poll time
                next_poll = time.time() + profile.current_interval
                
                # Poll device
                start_time = time.time()
                data = await self.poll_device_with_adaptive_timing(profile)
                poll_duration = time.time() - start_time
                
                # Update global statistics
                self.total_cycles += 1
                if data:
                    self.successful_cycles += 1
                    
                    # Publish to Home Assistant if enabled
                    if self.ha_mqtt_enabled:
                        await self.publish_to_home_assistant(profile, data)
                
                # Log status
                success_rate = (self.successful_cycles / self.total_cycles) * 100
                logger.info(f"📊 {profile.name}: Cycle {self.total_cycles}, Success: {success_rate:.1f}%, Health: {profile.health_score:.0f}")
                
                # Wait for next poll (adaptive timing)
                sleep_time = max(0, next_poll - time.time())
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                logger.info(f"🛑 Monitoring loop cancelled for {profile.name}")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop for {profile.name}: {e}")
                await asyncio.sleep(30)  # Error recovery delay
    
    async def poll_device_with_adaptive_timing(self, profile: DeviceProfile) -> Optional[Dict[str, Any]]:
        """Poll device with intelligent error handling and timing adaptation"""
        profile.total_attempts += 1
        start_time = time.time()
        
        try:
            client = BluPowClient(profile.mac_address)
            
            # Connection with timeout
            connected = await asyncio.wait_for(client.connect(), timeout=15.0)
            if not connected:
                raise Exception("Connection timeout")
            
            # Read device data
            await client.read_device_info()
            data = client.get_data()
            await client.disconnect()
            
            connection_time = time.time() - start_time
            
            # Update success metrics
            profile.successful_attempts += 1
            profile.consecutive_failures = 0
            profile.last_successful_poll = datetime.now()
            profile.recent_response_times.append(connection_time)
            
            # Keep only recent response times
            if len(profile.recent_response_times) > 20:
                profile.recent_response_times.pop(0)
            
            # Update performance metrics
            profile.connection_success_rate = profile.successful_attempts / profile.total_attempts
            profile.average_connection_time = sum(profile.recent_response_times[-10:]) / min(10, len(profile.recent_response_times))
            
            # Cache latest data
            if data and len(data) > 5:
                profile.last_data = data
                profile.data_field_count = len(data)
                
                # Add timing metadata
                data['_blupow_meta'] = {
                    'connection_time': connection_time,
                    'health_score': profile.health_score,
                    'success_rate': profile.connection_success_rate * 100,
                    'device_type': profile.device_type.value,
                    'capabilities': profile.capabilities
                }
            
            # Adaptive optimization
            await self.optimize_device_timing(profile)
            
            logger.debug(f"✅ {profile.name}: {connection_time:.1f}s, {len(data)} fields")
            return data
            
        except Exception as e:
            profile.consecutive_failures += 1
            profile.connection_success_rate = profile.successful_attempts / profile.total_attempts
            
            logger.warning(f"❌ {profile.name}: {e} (failures: {profile.consecutive_failures})")
            
            # Adaptive failure handling
            await self.handle_device_failure(profile)
            
            return None
    
    async def optimize_device_timing(self, profile: DeviceProfile):
        """Real-time timing optimization for individual device"""
        if len(profile.recent_response_times) < 5:
            return
        
        # Calculate new optimal interval
        avg_time = sum(profile.recent_response_times[-5:]) / 5
        
        # Adaptive algorithm based on device type and performance
        if profile.device_type.value == "bt_th":
            # BT-TH devices: Conservative approach
            new_interval = max(30, avg_time * 3)
        elif profile.device_type.value in ["bt_1", "bt_2"]:
            # BT-1/BT-2: More aggressive for MPPT controllers
            new_interval = max(45, avg_time * 2.5)
        else:
            # Other devices: Balanced approach
            new_interval = max(35, avg_time * 2.8)
        
        # Apply success rate modifier
        if profile.connection_success_rate < 0.8:
            new_interval *= 1.5  # Slow down for unreliable devices
        elif profile.connection_success_rate > 0.95:
            new_interval *= 0.9  # Speed up for very reliable devices
        
        # Bounds checking
        new_interval = max(profile.min_interval, min(profile.max_interval, new_interval))
        
        # Only update if significant change
        if abs(new_interval - profile.current_interval) > 5:
            old_interval = profile.current_interval
            profile.current_interval = new_interval
            profile.optimal_interval = new_interval
            logger.info(f"📈 {profile.name}: Optimized interval {old_interval:.0f}s → {new_interval:.0f}s")
    
    async def handle_device_failure(self, profile: DeviceProfile):
        """Intelligent failure handling with recovery strategies"""
        if profile.consecutive_failures >= 3:
            # Increase interval for struggling devices
            profile.current_interval = min(profile.max_interval, profile.current_interval * 1.4)
            logger.warning(f"⚠️ {profile.name}: Extended interval to {profile.current_interval:.0f}s due to failures")
        
        if profile.consecutive_failures >= 10:
            # Mark device as degraded
            logger.error(f"🔴 {profile.name}: Device marked as degraded (10+ consecutive failures)")
            profile.current_interval = profile.max_interval
        
        if profile.consecutive_failures >= 20:
            # Consider device failed
            logger.error(f"💀 {profile.name}: Device may be offline (20+ consecutive failures)")
    
    async def publish_to_home_assistant(self, profile: DeviceProfile, data: Dict[str, Any]):
        """Publish device data to Home Assistant via MQTT"""
        try:
            # This would integrate with MQTT for Home Assistant
            # For now, just log the structure
            ha_data = {
                'device_id': profile.mac_address.replace(':', ''),
                'name': profile.name.strip(),
                'state': 'online' if profile.status == DeviceStatus.ACTIVE else 'offline',
                'attributes': {
                    'battery_voltage': data.get('battery_voltage'),
                    'battery_percentage': data.get('battery_percentage'),
                    'solar_voltage': data.get('pv_voltage'),
                    'solar_power': data.get('pv_power'),
                    'load_power': data.get('load_power'),
                    'health_score': profile.health_score,
                    'connection_time': data.get('_blupow_meta', {}).get('connection_time'),
                    'device_type': profile.device_type.value,
                    'capabilities': profile.capabilities
                }
            }
            
            logger.debug(f"📡 HA Update: {profile.name} → {ha_data['state']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish to HA for {profile.name}: {e}")
    
    async def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time system status"""
        uptime = (datetime.now() - self.session_start).total_seconds()
        success_rate = (self.successful_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0
        
        return {
            'manager_status': 'running' if self.running else 'stopped',
            'uptime_hours': uptime / 3600,
            'total_cycles': self.total_cycles,
            'successful_cycles': self.successful_cycles,
            'success_rate': success_rate,
            'devices': {
                mac: {
                    'name': profile.name.strip(),
                    'status': profile.status.value,
                    'health': profile.health_score,
                    'interval': profile.current_interval,
                    'last_poll': profile.last_successful_poll.isoformat() if profile.last_successful_poll else None,
                    'consecutive_failures': profile.consecutive_failures,
                    'total_attempts': profile.total_attempts,
                    'success_rate': profile.connection_success_rate * 100,
                    'avg_connection_time': profile.average_connection_time,
                    'capabilities': profile.capabilities,
                    'latest_data': {
                        'battery_voltage': profile.last_data.get('battery_voltage'),
                        'battery_percentage': profile.last_data.get('battery_percentage'),
                        'solar_voltage': profile.last_data.get('pv_voltage'),
                        'solar_power': profile.last_data.get('pv_power'),
                        'load_power': profile.last_data.get('load_power')
                    }
                }
                for mac, profile in self.coordinator.devices.items()
            }
        }
    
    async def start(self):
        """Start the multi-device manager"""
        logger.info("🚀 Starting BluPow Multi-Device Manager...")
        
        # Initial discovery and setup
        await self.coordinator.run_discovery_and_setup()
        
        if not self.coordinator.devices:
            logger.error("❌ No devices found - cannot start monitoring")
            return
        
        self.running = True
        
        # Start monitoring tasks for each device
        for mac_address, profile in self.coordinator.devices.items():
            task = asyncio.create_task(self.device_monitoring_loop(profile))
            self.device_tasks[mac_address] = task
            logger.info(f"🔄 Started monitoring task for {profile.name}")
        
        logger.info(f"✅ Multi-device manager started with {len(self.coordinator.devices)} devices")
    
    async def stop(self):
        """Stop the multi-device manager"""
        logger.info("🛑 Stopping BluPow Multi-Device Manager...")
        
        self.running = False
        
        # Cancel all device monitoring tasks
        for mac_address, task in self.device_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Final statistics
        uptime = (datetime.now() - self.session_start).total_seconds()
        success_rate = (self.successful_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0
        
        logger.info(f"📊 Final Session Stats:")
        logger.info(f"  ⏱️ Uptime: {uptime/60:.1f} minutes")
        logger.info(f"  🔄 Total cycles: {self.total_cycles}")
        logger.info(f"  ✅ Success rate: {success_rate:.1f}%")
        logger.info(f"  📱 Devices monitored: {len(self.coordinator.devices)}")
        
        logger.info("🏁 BluPow Multi-Device Manager stopped")

async def demo_run():
    """Demo run for testing - runs for 5 minutes"""
    manager = MultiDeviceManager()
    
    try:
        logger.info("🎯 Starting BluPow Demo (5 minutes)")
        await manager.start()
        
        # Run for 5 minutes
        for minute in range(5):
            await asyncio.sleep(60)
            status = await manager.get_real_time_status()
            logger.info(f"📊 Minute {minute + 1}: {status['success_rate']:.1f}% success, {status['total_cycles']} cycles")
            
            # Show device status
            for mac, device in status['devices'].items():
                logger.info(f"  📱 {device['name']}: Health {device['health']:.0f}%, Interval {device['interval']:.0f}s")
        
        logger.info("✅ Demo completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted")
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(demo_run())
