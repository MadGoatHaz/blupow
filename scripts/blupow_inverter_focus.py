#!/usr/bin/env python3
"""
🔋 BLUPOW INVERTER FOCUS 🔋
Getting YOUR inverter working first - the foundation proof!

This script focuses on:
1. Finding YOUR configured inverter (D8:B6:73:BF:4F:75)
2. Testing connection and data retrieval
3. Creating a stable polling system
4. Fixing the 5-minute degradation issue
5. Building the foundation for the AI Super Probe
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bleak import BleakScanner
from blupow_client import BluPowClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blupow_inverter_focus.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InverterManager:
    """🔋 Focused inverter management for stability testing"""
    
    def __init__(self, target_mac: str = "D8:B6:73:BF:4F:75"):
        self.target_mac = target_mac
        self.inverter_found = False
        self.connection_history = []
        self.data_history = []
        self.stability_test_results = {}
        
    async def scan_for_inverter(self, duration: int = 15) -> bool:
        """🔍 Scan specifically for the configured inverter"""
        logger.info(f"🔍 Scanning for YOUR inverter: {self.target_mac}")
        
        try:
            devices = await BleakScanner.discover(timeout=duration)
            
            logger.info(f"📡 Found {len(devices)} Bluetooth devices total")
            
            for device in devices:
                logger.info(f"📱 {device.name or 'Unknown'} ({device.address})")
                
                if device.address == self.target_mac:
                    self.inverter_found = True
                    logger.info(f"🎯 FOUND YOUR INVERTER! {device.name or 'BTRIC134000035'} ({device.address})")
                    return True
            
            logger.warning(f"❌ Your configured inverter {self.target_mac} not found in scan")
            return False
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return False
    
    async def test_inverter_connection(self) -> dict:
        """🧪 Test inverter connection and data retrieval"""
        logger.info(f"🧪 Testing connection to YOUR inverter: {self.target_mac}")
        
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'mac_address': self.target_mac,
            'connection_successful': False,
            'connection_time': 0.0,
            'data_retrieved': False,
            'data_field_count': 0,
            'sample_data': {},
            'error': None
        }
        
        start_time = time.time()
        
        try:
            client = BluPowClient(self.target_mac)
            
            # Test connection
            connected = await client.connect()
            connection_time = time.time() - start_time
            test_result['connection_time'] = connection_time
            
            if connected:
                test_result['connection_successful'] = True
                logger.info(f"✅ Connected to inverter in {connection_time:.2f}s")
                
                # Test data retrieval
                data = await client.read_device_info()
                cached_data = client.get_data()
                
                await client.disconnect()
                
                if cached_data and len(cached_data) > 0:
                    test_result['data_retrieved'] = True
                    test_result['data_field_count'] = len(cached_data)
                    test_result['sample_data'] = {k: v for k, v in list(cached_data.items())[:8]}
                    
                    logger.info(f"📊 Retrieved {len(cached_data)} data fields")
                    logger.info("🔋 Sample readings:")
                    for k, v in list(cached_data.items())[:6]:
                        logger.info(f"   {k}: {v}")
                
                else:
                    logger.warning("⚠️ Connected but no data retrieved")
            
            else:
                logger.error(f"❌ Failed to connect to inverter")
                test_result['error'] = "Connection failed"
        
        except Exception as e:
            logger.error(f"❌ Inverter test failed: {e}")
            test_result['error'] = str(e)
        
        self.connection_history.append(test_result)
        return test_result
    
    async def stability_test(self, duration_minutes: int = 10) -> dict:
        """🏃‍♂️ Run stability test to identify the 5-minute degradation issue"""
        logger.info(f"🏃‍♂️ Starting {duration_minutes}-minute stability test...")
        
        test_start = time.time()
        test_results = {
            'start_time': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'connection_attempts': [],
            'success_pattern': [],
            'degradation_detected': False,
            'degradation_time': None,
            'recommendations': []
        }
        
        attempt_count = 0
        consecutive_failures = 0
        
        while (time.time() - test_start) < (duration_minutes * 60):
            attempt_count += 1
            elapsed_minutes = (time.time() - test_start) / 60
            
            logger.info(f"🔄 Stability Test - Attempt {attempt_count} at {elapsed_minutes:.1f} minutes")
            
            # Test connection
            result = await self.test_inverter_connection()
            test_results['connection_attempts'].append(result)
            
            # Track success pattern
            if result['connection_successful'] and result['data_retrieved']:
                test_results['success_pattern'].append(1)
                consecutive_failures = 0
                logger.info(f"✅ Success - {result['data_field_count']} fields in {result['connection_time']:.2f}s")
            else:
                test_results['success_pattern'].append(0)
                consecutive_failures += 1
                logger.warning(f"❌ Failure - {consecutive_failures} consecutive failures")
                
                # Check for degradation pattern
                if consecutive_failures >= 3 and elapsed_minutes > 4:
                    test_results['degradation_detected'] = True
                    test_results['degradation_time'] = elapsed_minutes
                    logger.error(f"🚨 DEGRADATION DETECTED at {elapsed_minutes:.1f} minutes!")
                    break
            
            # Wait before next attempt (30 seconds like HA coordinator)
            await asyncio.sleep(30)
        
        # Analyze results
        total_attempts = len(test_results['connection_attempts'])
        successful_attempts = sum(test_results['success_pattern'])
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        
        logger.info(f"📊 Stability Test Complete:")
        logger.info(f"   Total Attempts: {total_attempts}")
        logger.info(f"   Successful: {successful_attempts}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        if test_results['degradation_detected']:
            logger.error(f"🚨 Degradation detected at {test_results['degradation_time']:.1f} minutes")
            test_results['recommendations'].append("CRITICAL: Resource leak causing 5-minute degradation")
            test_results['recommendations'].append("SOLUTION: Implement subprocess-based coordinator")
        elif success_rate > 80:
            logger.info("🟢 Stable performance - no degradation detected")
            test_results['recommendations'].append("Performance is stable - ready for production")
        else:
            logger.warning("🟡 Inconsistent performance detected")
            test_results['recommendations'].append("Investigate connection timing and resource cleanup")
        
        self.stability_test_results = test_results
        return test_results
    
    async def create_production_config(self) -> dict:
        """📋 Create production-ready configuration for Home Assistant"""
        logger.info("📋 Creating production configuration...")
        
        # Analyze connection history for optimal settings
        successful_connections = [r for r in self.connection_history if r['connection_successful']]
        
        if not successful_connections:
            logger.error("❌ No successful connections - cannot create config")
            return {}
        
        # Calculate optimal settings
        connection_times = [r['connection_time'] for r in successful_connections]
        avg_connection_time = sum(connection_times) / len(connection_times)
        max_connection_time = max(connection_times)
        
        config = {
            'device': {
                'mac_address': self.target_mac,
                'name': 'Renogy Inverter',
                'model': 'RIV1230RCH-SPS',
                'verified_working': True,
                'last_verified': datetime.now().isoformat()
            },
            'connection_profile': {
                'average_connection_time': round(avg_connection_time, 2),
                'max_connection_time': round(max_connection_time, 2),
                'recommended_timeout': round(max_connection_time + 5, 2),
                'success_rate': len(successful_connections) / len(self.connection_history) * 100,
                'optimal_polling_interval': 30
            },
            'home_assistant_config': {
                'coordinator_type': 'subprocess_based',
                'update_interval': 30,
                'timeout': round(max_connection_time + 10, 2),
                'retry_attempts': 3,
                'error_recovery_delay': 60
            },
            'stability_analysis': self.stability_test_results
        }
        
        logger.info("✅ Production configuration created")
        return config
    
    def save_results(self, filename: str = "inverter_focus_results.json"):
        """💾 Save all test results and configuration"""
        results = {
            'inverter_mac': self.target_mac,
            'inverter_found': self.inverter_found,
            'test_timestamp': datetime.now().isoformat(),
            'connection_history': self.connection_history,
            'stability_test': self.stability_test_results,
            'production_config': {}
        }
        
        # Create production config if we have successful connections
        if any(r['connection_successful'] for r in self.connection_history):
            results['production_config'] = asyncio.run(self.create_production_config())
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Results saved to {filename}")


async def main():
    """🚀 Main execution - Focus on getting YOUR inverter working"""
    print("🔋 BLUPOW INVERTER FOCUS - Getting YOUR inverter working!")
    print("   Target: D8:B6:73:BF:4F:75 (Your configured Home Assistant device)")
    print("   Goal: Stable monitoring foundation for the AI Super Probe")
    
    manager = InverterManager()
    
    try:
        # Phase 1: Find the inverter
        print("\n🔍 Phase 1: Scanning for YOUR configured inverter...")
        found = await manager.scan_for_inverter(duration=15)
        
        if not found:
            print("❌ Your inverter not found in scan - checking if it's already connected...")
            print("   Trying direct connection test...")
        
        # Phase 2: Test connection regardless of scan result
        print("\n🧪 Phase 2: Testing direct connection to YOUR inverter...")
        test_result = await manager.test_inverter_connection()
        
        if test_result['connection_successful']:
            print(f"✅ SUCCESS! Connected in {test_result['connection_time']:.2f}s")
            print(f"📊 Retrieved {test_result['data_field_count']} data fields")
            
            # Phase 3: Stability testing
            print("\n🏃‍♂️ Phase 3: Running stability test (8 minutes)...")
            print("   This will identify the 5-minute degradation issue...")
            
            stability_results = await manager.stability_test(duration_minutes=8)
            
            # Phase 4: Create production config
            print("\n📋 Phase 4: Creating production configuration...")
            production_config = await manager.create_production_config()
            
            print("\n" + "="*60)
            print("🎯 INVERTER FOCUS RESULTS")
            print("="*60)
            
            if stability_results['degradation_detected']:
                print(f"🚨 DEGRADATION DETECTED at {stability_results['degradation_time']:.1f} minutes")
                print("   This confirms the 5-minute stability issue!")
                print("   Recommendations:")
                for rec in stability_results['recommendations']:
                    print(f"   • {rec}")
            else:
                print("🟢 No degradation detected - inverter is stable!")
            
            success_rate = sum(stability_results['success_pattern']) / len(stability_results['success_pattern']) * 100
            print(f"📊 Overall Success Rate: {success_rate:.1f}%")
            
        else:
            print(f"❌ Connection failed: {test_result.get('error', 'Unknown error')}")
            print("   Your inverter may be:")
            print("   • Powered off or out of range")
            print("   • Already connected to another device")
            print("   • In a different Bluetooth mode")
        
        # Save results regardless
        manager.save_results()
        print("\n💾 All results saved to 'inverter_focus_results.json'")
        
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        manager.save_results()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        manager.save_results()


if __name__ == "__main__":
    asyncio.run(main())