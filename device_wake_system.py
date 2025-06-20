#!/usr/bin/env python3
"""
BluPow Device Wake-Up & Connection Testing System

Specialized system to detect and wake up "sleeping" Renogy devices
Focuses on the specific device D8:B6:73:BF:4F:75 (RNG-CTRL-RVR40) that's showing as offline

This system will:
- Attempt to wake up sleeping Renogy devices
- Test different connection strategies
- Monitor for intermittent device advertising
- Provide detailed connection diagnostics
- Test with different Bluetooth proxies
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    from bleak.exc import BleakError
except ImportError:
    print("Error: bleak library not found. Please install it with:")
    print("  pip install bleak")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Target device information (from your logs)
TARGET_DEVICE = {
    'address': 'D8:B6:73:BF:4F:75',
    'name': 'BTRIC134000035',
    'model': 'RNG-CTRL-RVR40',
    'type': 'charge_controller'
}

# Renogy UUIDs (from cyrils/renogy-bt)
RENOGY_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
RENOGY_TX_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
RENOGY_RX_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
RX_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

# Wake-up strategies
WAKE_STRATEGIES = [
    'continuous_scan',
    'burst_scan',
    'low_power_scan',
    'targeted_scan',
    'proxy_assisted_scan'
]

@dataclass
class WakeAttempt:
    """Wake-up attempt information"""
    timestamp: datetime
    strategy: str
    duration: float
    device_found: bool
    connectable: bool
    rssi: Optional[int]
    error: Optional[str]
    notes: List[str]

class DeviceWakeSystem:
    """Specialized system for waking up sleeping Renogy devices"""
    
    def __init__(self):
        self.target_address = TARGET_DEVICE['address']
        self.target_name = TARGET_DEVICE['name']
        self.wake_attempts: List[WakeAttempt] = []
        self.device_states: Dict[str, Any] = {}
        
    async def continuous_monitoring_scan(self, duration: float = 300.0) -> List[WakeAttempt]:
        """Continuously monitor for device appearance over extended period"""
        _LOGGER.info(f"🔍 Starting continuous monitoring for {self.target_name} ({self.target_address})")
        _LOGGER.info(f"⏱️  Monitoring for {duration/60:.1f} minutes...")
        
        start_time = time.time()
        attempts = []
        last_detection = None
        detection_count = 0
        
        while (time.time() - start_time) < duration:
            attempt_start = time.time()
            
            try:
                # Short burst scan
                devices = await BleakScanner.discover(timeout=5.0)
                
                device_found = False
                target_device = None
                
                for device in devices:
                    if device.address.upper() == self.target_address.upper():
                        device_found = True
                        target_device = device
                        detection_count += 1
                        last_detection = datetime.now()
                        break
                
                attempt_duration = time.time() - attempt_start
                
                # Test connectivity if found
                connectable = False
                rssi = None
                error = None
                notes = []
                
                if device_found and target_device:
                    rssi = getattr(target_device, 'rssi', None)
                    _LOGGER.info(f"✅ Device detected! RSSI: {rssi} dBm (Detection #{detection_count})")
                    
                    # Test connection
                    try:
                        async with BleakClient(target_device, timeout=10.0) as client:
                            if client.is_connected:
                                connectable = True
                                notes.append("Connection successful")
                                
                                # Get services
                                services = await client.get_services()
                                service_count = len(list(services))
                                notes.append(f"Found {service_count} services")
                                
                                # Check for Renogy services
                                renogy_services = []
                                for service in services:
                                    if str(service.uuid).lower() in [RENOGY_SERVICE_UUID.lower(), RX_SERVICE_UUID.lower()]:
                                        renogy_services.append(str(service.uuid))
                                
                                if renogy_services:
                                    notes.append(f"Renogy services: {', '.join(renogy_services)}")
                                else:
                                    notes.append("No Renogy services found")
                                    
                            else:
                                notes.append("Connection established but not active")
                                
                    except Exception as e:
                        error = str(e)
                        notes.append(f"Connection failed: {error}")
                
                # Record attempt
                attempt = WakeAttempt(
                    timestamp=datetime.now(),
                    strategy='continuous_scan',
                    duration=attempt_duration,
                    device_found=device_found,
                    connectable=connectable,
                    rssi=rssi,
                    error=error,
                    notes=notes
                )
                attempts.append(attempt)
                
                # Progress update
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0:  # Every 30 seconds
                    _LOGGER.info(f"⏱️  Progress: {elapsed/60:.1f}min, Detections: {detection_count}")
                
                # Brief pause between scans
                await asyncio.sleep(2.0)
                
            except Exception as e:
                _LOGGER.error(f"❌ Scan error: {e}")
                await asyncio.sleep(5.0)
        
        total_time = time.time() - start_time
        _LOGGER.info(f"📊 Monitoring complete: {detection_count} detections in {total_time/60:.1f} minutes")
        
        if last_detection:
            time_since = datetime.now() - last_detection
            _LOGGER.info(f"🕒 Last detection: {time_since.total_seconds():.0f} seconds ago")
        
        self.wake_attempts.extend(attempts)
        return attempts
    
    async def burst_wake_strategy(self) -> WakeAttempt:
        """High-frequency burst scanning to catch brief advertising"""
        _LOGGER.info("💥 Burst wake strategy - rapid consecutive scans")
        
        start_time = time.time()
        found_count = 0
        best_rssi = None
        
        # Perform 10 rapid scans
        for i in range(10):
            _LOGGER.info(f"   Burst {i+1}/10...")
            
            try:
                devices = await BleakScanner.discover(timeout=2.0)
                
                for device in devices:
                    if device.address.upper() == self.target_address.upper():
                        found_count += 1
                        rssi = getattr(device, 'rssi', None)
                        if best_rssi is None or (rssi and rssi > best_rssi):
                            best_rssi = rssi
                        _LOGGER.info(f"   ✅ Found in burst {i+1}, RSSI: {rssi}")
                        break
                        
            except Exception as e:
                _LOGGER.error(f"   ❌ Burst {i+1} failed: {e}")
            
            # Brief pause between bursts
            await asyncio.sleep(0.5)
        
        duration = time.time() - start_time
        device_found = found_count > 0
        
        notes = [
            f"Detected in {found_count}/10 burst scans",
            f"Best RSSI: {best_rssi}" if best_rssi else "No RSSI data"
        ]
        
        return WakeAttempt(
            timestamp=datetime.now(),
            strategy='burst_scan',
            duration=duration,
            device_found=device_found,
            connectable=False,  # Not tested in burst mode
            rssi=best_rssi,
            error=None,
            notes=notes
        )
    
    async def deep_sleep_wake_strategy(self) -> WakeAttempt:
        """Try to wake device from deep sleep using load simulation"""
        _LOGGER.info("😴 Deep sleep wake strategy - extended monitoring with wake signals")
        
        start_time = time.time()
        
        # Strategy: Monitor for longer periods as device may wake periodically
        detection_attempts = []
        
        for attempt in range(5):
            _LOGGER.info(f"   Wake attempt {attempt+1}/5 (30 second scan)...")
            
            try:
                devices = await BleakScanner.discover(timeout=30.0)
                
                device_found = False
                for device in devices:
                    if device.address.upper() == self.target_address.upper():
                        device_found = True
                        rssi = getattr(device, 'rssi', None)
                        _LOGGER.info(f"   ✅ Device woke up! RSSI: {rssi}")
                        
                        # Try immediate connection while awake
                        try:
                            async with BleakClient(device, timeout=15.0) as client:
                                if client.is_connected:
                                    _LOGGER.info("   🔌 Successfully connected while awake!")
                                    return WakeAttempt(
                                        timestamp=datetime.now(),
                                        strategy='deep_sleep_wake',
                                        duration=time.time() - start_time,
                                        device_found=True,
                                        connectable=True,
                                        rssi=rssi,
                                        error=None,
                                        notes=["Device woke from deep sleep", "Connection successful"]
                                    )
                        except Exception as e:
                            _LOGGER.warning(f"   ⚠️  Device awake but connection failed: {e}")
                        
                        detection_attempts.append(rssi)
                        break
                
                if not device_found:
                    _LOGGER.info(f"   💤 Device still sleeping (attempt {attempt+1})")
                    
            except Exception as e:
                _LOGGER.error(f"   ❌ Wake attempt {attempt+1} failed: {e}")
            
            # Wait between attempts
            if attempt < 4:
                _LOGGER.info("   ⏸️  Waiting 60 seconds before next attempt...")
                await asyncio.sleep(60.0)
        
        duration = time.time() - start_time
        device_found = len(detection_attempts) > 0
        
        notes = [
            f"Device detected in {len(detection_attempts)}/5 attempts",
            f"Detection RSSIs: {detection_attempts}" if detection_attempts else "No detections"
        ]
        
        return WakeAttempt(
            timestamp=datetime.now(),
            strategy='deep_sleep_wake',
            duration=duration,
            device_found=device_found,
            connectable=False,
            rssi=max(detection_attempts) if detection_attempts else None,
            error=None,
            notes=notes
        )
    
    async def proxy_assisted_wake(self) -> WakeAttempt:
        """Test wake-up with different proxy configurations"""
        _LOGGER.info("🌐 Proxy-assisted wake strategy")
        
        start_time = time.time()
        
        # Known proxies from user setup
        proxies = [
            ("esp32-bluetooth-proxy-2105e4", "192.168.51.151", "Primary - +10dB boost"),
            ("proxy-2", "192.168.51.207", "Secondary"),
            ("proxy-3", "192.168.51.109", "Tertiary")
        ]
        
        notes = []
        best_detection = None
        
        for proxy_name, proxy_ip, description in proxies:
            _LOGGER.info(f"   Testing with {proxy_name} ({proxy_ip})")
            notes.append(f"Tested with {proxy_name}")
            
            try:
                # Longer scan when using proxy
                devices = await BleakScanner.discover(timeout=15.0)
                
                for device in devices:
                    if device.address.upper() == self.target_address.upper():
                        rssi = getattr(device, 'rssi', None)
                        _LOGGER.info(f"   ✅ Found via {proxy_name}! RSSI: {rssi}")
                        
                        if best_detection is None or (rssi and rssi > best_detection):
                            best_detection = rssi
                        
                        notes.append(f"Detected via {proxy_name} at {rssi} dBm")
                        
                        # Test connection
                        try:
                            async with BleakClient(device, timeout=10.0) as client:
                                if client.is_connected:
                                    notes.append(f"Connected successfully via {proxy_name}")
                                    return WakeAttempt(
                                        timestamp=datetime.now(),
                                        strategy='proxy_assisted_scan',
                                        duration=time.time() - start_time,
                                        device_found=True,
                                        connectable=True,
                                        rssi=rssi,
                                        error=None,
                                        notes=notes
                                    )
                        except Exception as e:
                            notes.append(f"Connection via {proxy_name} failed: {str(e)}")
                        
                        break
                        
            except Exception as e:
                notes.append(f"Scan via {proxy_name} failed: {str(e)}")
        
        duration = time.time() - start_time
        device_found = best_detection is not None
        
        return WakeAttempt(
            timestamp=datetime.now(),
            strategy='proxy_assisted_scan',
            duration=duration,
            device_found=device_found,
            connectable=False,
            rssi=best_detection,
            error=None,
            notes=notes
        )
    
    async def run_all_wake_strategies(self) -> Dict[str, WakeAttempt]:
        """Run all wake-up strategies"""
        _LOGGER.info("🚀 Running comprehensive wake-up strategies for device detection")
        _LOGGER.info("="*80)
        _LOGGER.info(f"Target Device: {self.target_name} ({self.target_address})")
        _LOGGER.info(f"Model: {TARGET_DEVICE['model']}")
        _LOGGER.info("="*80)
        
        results = {}
        
        # Strategy 1: Burst wake
        _LOGGER.info("\n1️⃣  BURST WAKE STRATEGY")
        results['burst'] = await self.burst_wake_strategy()
        
        # Strategy 2: Deep sleep wake
        _LOGGER.info("\n2️⃣  DEEP SLEEP WAKE STRATEGY")
        results['deep_sleep'] = await self.deep_sleep_wake_strategy()
        
        # Strategy 3: Proxy assisted
        _LOGGER.info("\n3️⃣  PROXY ASSISTED WAKE STRATEGY")
        results['proxy_assisted'] = await self.proxy_assisted_wake()
        
        # Display results
        self.display_wake_results(results)
        
        return results
    
    def display_wake_results(self, results: Dict[str, WakeAttempt]):
        """Display comprehensive wake-up test results"""
        print("\n" + "="*80)
        print("📊 DEVICE WAKE-UP TEST RESULTS")
        print("="*80)
        print(f"🎯 Target: {self.target_name} ({self.target_address})")
        print(f"🏷️  Model: {TARGET_DEVICE['model']}")
        print("")
        
        successful_strategies = []
        
        for strategy_name, attempt in results.items():
            status = "✅ FOUND" if attempt.device_found else "❌ NOT FOUND"
            connection = "🔌 CONNECTED" if attempt.connectable else "🔌 NOT TESTED"
            
            print(f"🧪 {strategy_name.upper().replace('_', ' ')} STRATEGY:")
            print(f"   Status: {status}")
            print(f"   Connection: {connection}")
            print(f"   Duration: {attempt.duration:.1f}s")
            if attempt.rssi:
                print(f"   Signal: {attempt.rssi} dBm")
            
            if attempt.notes:
                print("   Notes:")
                for note in attempt.notes:
                    print(f"      • {note}")
            
            if attempt.error:
                print(f"   Error: {attempt.error}")
            
            print("")
            
            if attempt.device_found:
                successful_strategies.append(strategy_name)
        
        # Summary and recommendations
        print("🎯 SUMMARY & RECOMMENDATIONS:")
        print("="*50)
        
        if successful_strategies:
            print(f"✅ Device detected using: {', '.join(successful_strategies)}")
            print("")
            print("💡 RECOMMENDATIONS:")
            print("   • Device is intermittently available (likely power saving mode)")
            print("   • Consider enabling continuous monitoring in Home Assistant")
            print("   • Check if device has power management settings")
            print("   • Try connecting during active charging periods")
            
            # Find best strategy
            best_attempt = None
            for strategy in successful_strategies:
                attempt = results[strategy]
                if attempt.connectable:
                    best_attempt = attempt
                    break
            
            if not best_attempt:
                best_attempt = max([results[s] for s in successful_strategies], 
                                 key=lambda x: x.rssi or -999)
            
            if best_attempt:
                print(f"   • Best detection method: {best_attempt.strategy}")
                if best_attempt.rssi:
                    print(f"   • Signal strength: {best_attempt.rssi} dBm")
                    
        else:
            print("❌ Device not detected with any strategy")
            print("")
            print("💡 TROUBLESHOOTING STEPS:")
            print("   1. Verify device is powered on and operational")
            print("   2. Check for physical Bluetooth activation button")
            print("   3. Try during active charging/load periods")
            print("   4. Ensure device is not connected to Renogy app")
            print("   5. Power cycle the device if accessible")
            print("   6. Move closer to device (within 5 meters)")
            print("   7. Check device manual for Bluetooth activation")
        
        # Save results
        self.save_wake_results(results)
    
    def save_wake_results(self, results: Dict[str, WakeAttempt]):
        """Save wake-up test results to file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'target_device': TARGET_DEVICE,
            'strategies_tested': len(results),
            'successful_strategies': [name for name, attempt in results.items() if attempt.device_found],
            'results': {}
        }
        
        for strategy_name, attempt in results.items():
            data['results'][strategy_name] = {
                'timestamp': attempt.timestamp.isoformat(),
                'strategy': attempt.strategy,
                'duration': attempt.duration,
                'device_found': attempt.device_found,
                'connectable': attempt.connectable,
                'rssi': attempt.rssi,
                'error': attempt.error,
                'notes': attempt.notes
            }
        
        try:
            import json
            with open('device_wake_results.json', 'w') as f:
                json.dump(data, f, indent=2)
            _LOGGER.info("📄 Wake test results saved to device_wake_results.json")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to save results: {e}")

async def main():
    """Main function for device wake testing"""
    wake_system = DeviceWakeSystem()
    
    try:
        print("🔍 BluPow Device Wake-Up & Connection Testing System")
        print("="*60)
        print("This will test various strategies to detect and connect to")
        print(f"your Renogy device: {TARGET_DEVICE['name']} ({TARGET_DEVICE['address']})")
        print("")
        
        # Ask user for test type
        print("Available test modes:")
        print("1. Quick test (all strategies, ~5 minutes)")
        print("2. Extended monitoring (continuous scan, 15 minutes)")
        print("3. Full comprehensive test (all strategies + monitoring)")
        
        choice = input("\nSelect test mode (1-3): ").strip()
        
        if choice == "2":
            print("\n🔍 Starting extended monitoring...")
            await wake_system.continuous_monitoring_scan(duration=900.0)  # 15 minutes
        elif choice == "3":
            print("\n🔍 Starting comprehensive test...")
            await wake_system.run_all_wake_strategies()
            print("\n🔍 Following up with extended monitoring...")
            await wake_system.continuous_monitoring_scan(duration=600.0)  # 10 minutes
        else:
            print("\n🔍 Starting quick test...")
            await wake_system.run_all_wake_strategies()
        
        print("\n🎉 Device wake testing complete!")
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        _LOGGER.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 