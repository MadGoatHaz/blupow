#!/usr/bin/env python3
"""
BluPow Connection Diagnostics
Comprehensive Bluetooth connection testing and troubleshooting
"""

import asyncio
import logging
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target device
TARGET_MAC = "D8:B6:73:BF:4F:75"
TARGET_NAME = "BTRIC134000035"

class ConnectionDiagnostics:
    def __init__(self):
        self.scan_results = []
        self.connection_attempts = []
        
    async def scan_for_device(self, duration=10):
        """Enhanced device scanning with detailed analysis"""
        logger.info(f"🔍 Scanning for {TARGET_NAME} ({TARGET_MAC}) for {duration}s...")
        
        devices_found = []
        scan_count = 0
        
        def detection_callback(device, advertisement_data):
            nonlocal scan_count
            scan_count += 1
            
            if device.address.upper() == TARGET_MAC.upper():
                rssi = advertisement_data.rssi
                devices_found.append({
                    'timestamp': datetime.now(),
                    'rssi': rssi,
                    'name': device.name,
                    'services': list(advertisement_data.service_uuids),
                    'manufacturer_data': dict(advertisement_data.manufacturer_data),
                    'service_data': dict(advertisement_data.service_data)
                })
                logger.info(f"📡 Found {TARGET_NAME}: RSSI {rssi} dBm")
        
        # Perform scan
        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()
        await asyncio.sleep(duration)
        await scanner.stop()
        
        logger.info(f"📊 Scan Results: {len(devices_found)} detections out of {scan_count} total devices")
        
        if devices_found:
            avg_rssi = sum(d['rssi'] for d in devices_found) / len(devices_found)
            min_rssi = min(d['rssi'] for d in devices_found)
            max_rssi = max(d['rssi'] for d in devices_found)
            
            logger.info(f"📶 Signal Strength - Avg: {avg_rssi:.1f} dBm, Range: {min_rssi} to {max_rssi} dBm")
            
            # Signal quality assessment
            if avg_rssi > -60:
                quality = "Excellent"
            elif avg_rssi > -70:
                quality = "Good"  
            elif avg_rssi > -80:
                quality = "Fair"
            else:
                quality = "Poor"
                
            logger.info(f"🎯 Signal Quality: {quality}")
            
            return devices_found[-1]  # Return most recent detection
        else:
            logger.error(f"❌ Device {TARGET_NAME} not found during scan")
            return None
    
    async def test_connection_strategies(self, device_info):
        """Test multiple connection strategies"""
        strategies = [
            {"name": "Standard", "timeout": 10.0},
            {"name": "Extended Timeout", "timeout": 20.0},
            {"name": "Quick", "timeout": 5.0},
        ]
        
        successful_connections = 0
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"🔗 Strategy {i}: {strategy['name']} (timeout: {strategy['timeout']}s)")
            
            success = await self.attempt_connection(
                timeout=strategy['timeout'],
                strategy_name=strategy['name']
            )
            
            if success:
                successful_connections += 1
                logger.info(f"✅ {strategy['name']} connection successful!")
            else:
                logger.warning(f"❌ {strategy['name']} connection failed")
            
            # Wait between attempts
            if i < len(strategies):
                logger.info("⏳ Waiting 5s before next attempt...")
                await asyncio.sleep(5)
        
        return successful_connections
    
    async def attempt_connection(self, timeout=10.0, strategy_name="Standard"):
        """Attempt connection with detailed error reporting"""
        start_time = time.time()
        
        try:
            async with BleakClient(TARGET_MAC, timeout=timeout) as client:
                if client.is_connected:
                    duration = time.time() - start_time
                    logger.info(f"🎉 Connected successfully in {duration:.2f}s")
                    
                    # Get device info
                    try:
                        services = await client.get_services()
                        logger.info(f"📋 Found {len(services.services)} services")
                        
                        for service in services:
                            logger.info(f"   🔹 Service: {service.uuid}")
                            for char in service.characteristics:
                                props = ', '.join(char.properties)
                                logger.info(f"      📝 Characteristic: {char.uuid} ({props})")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Could not enumerate services: {e}")
                    
                    return True
                else:
                    logger.error("❌ Client reports not connected")
                    return False
                    
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"⏰ Connection timeout after {duration:.2f}s")
            return False
            
        except BleakError as e:
            duration = time.time() - start_time
            logger.error(f"🚫 Bleak error after {duration:.2f}s: {e}")
            
            # Specific error analysis
            error_str = str(e).lower()
            if "fail_establish" in error_str:
                logger.info("💡 Suggestion: Device may be busy or in power-saving mode")
            elif "timeout" in error_str:
                logger.info("💡 Suggestion: Try moving closer or check for interference")
            elif "not found" in error_str:
                logger.info("💡 Suggestion: Device may have stopped advertising")
            
            return False
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"💥 Unexpected error after {duration:.2f}s: {e}")
            return False
    
    async def environmental_analysis(self):
        """Analyze Bluetooth environment"""
        logger.info("🌐 Analyzing Bluetooth environment...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        
        # Count devices by type
        device_types = {}
        total_devices = len(devices)
        
        for device in devices:
            name = device.name or "Unknown"
            device_type = "Unknown"
            
            name_lower = name.lower()
            if any(x in name_lower for x in ['esp32', 'proxy']):
                device_type = "ESP32/Proxy"
            elif any(x in name_lower for x in ['phone', 'iphone', 'samsung']):
                device_type = "Phone"
            elif any(x in name_lower for x in ['watch', 'band']):
                device_type = "Wearable"
            elif any(x in name_lower for x in ['tv', 'speaker', 'audio']):
                device_type = "Audio/Video"
            elif 'renogy' in name_lower or 'btric' in name_lower:
                device_type = "Renogy Device"
            
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        logger.info(f"📱 Found {total_devices} total Bluetooth devices:")
        for device_type, count in sorted(device_types.items()):
            logger.info(f"   {device_type}: {count}")
        
        # Check for potential interference
        if total_devices > 20:
            logger.warning("⚠️ High device density detected - may cause interference")
        
        return device_types
    
    async def generate_recommendations(self, scan_result, connection_success_rate, environment):
        """Generate troubleshooting recommendations"""
        logger.info("💡 RECOMMENDATIONS:")
        
        if not scan_result:
            logger.info("1. Device not found during scan:")
            logger.info("   - Check if device is powered on")
            logger.info("   - Verify device is in pairing/advertising mode")
            logger.info("   - Try power cycling the device")
            return
        
        # Signal strength recommendations
        avg_rssi = scan_result.get('rssi', -100)
        if avg_rssi < -80:
            logger.info("1. Weak signal strength:")
            logger.info("   - Move Home Assistant server closer to device")
            logger.info("   - Use ESPHome Bluetooth proxy for range extension")
            logger.info("   - Check for physical obstructions")
        
        # Connection success recommendations
        if connection_success_rate == 0:
            logger.info("2. All connection attempts failed:")
            logger.info("   - Device may be in sleep/power-saving mode")
            logger.info("   - Try connecting during different times of day")
            logger.info("   - Check if device is connected to another system")
        elif connection_success_rate < 0.5:
            logger.info("2. Intermittent connection issues:")
            logger.info("   - Bluetooth interference likely")
            logger.info("   - Try disabling other Bluetooth devices temporarily")
            logger.info("   - Consider using 2.4GHz WiFi channel optimization")
        
        # Environment recommendations
        total_devices = sum(environment.values())
        if total_devices > 15:
            logger.info("3. Congested Bluetooth environment:")
            logger.info("   - High device density detected")
            logger.info("   - Consider Bluetooth frequency management")
            logger.info("   - ESPHome proxies can help with device isolation")
        
        logger.info("4. General recommendations:")
        logger.info("   - Ensure device firmware is up to date")
        logger.info("   - Check Home Assistant Bluetooth integration status")
        logger.info("   - Monitor connection patterns over time")

async def main():
    """Main diagnostic routine"""
    logger.info("🚀 Starting BluPow Connection Diagnostics")
    logger.info("=" * 60)
    
    diagnostics = ConnectionDiagnostics()
    
    # Step 1: Scan for device
    scan_result = await diagnostics.scan_for_device(duration=15)
    
    # Step 2: Analyze environment
    environment = await diagnostics.environmental_analysis()
    
    # Step 3: Test connections if device found
    connection_success_rate = 0
    if scan_result:
        logger.info("\n" + "=" * 60)
        logger.info("🔗 TESTING CONNECTION STRATEGIES")
        logger.info("=" * 60)
        
        successful = await diagnostics.test_connection_strategies(scan_result)
        connection_success_rate = successful / 3  # 3 strategies tested
        
        logger.info(f"\n📊 Connection Success Rate: {connection_success_rate:.1%}")
    
    # Step 4: Generate recommendations
    logger.info("\n" + "=" * 60)
    await diagnostics.generate_recommendations(scan_result, connection_success_rate, environment)
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Diagnostics Complete")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 