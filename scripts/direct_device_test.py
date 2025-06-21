#!/usr/bin/env python3
"""
Direct Device Test - Focus on Getting the Available Device Working

GOAL: Test the BT-TH device (C4:D3:6A:66:7E:D4) that we KNOW is available
and get it working reliably without complex configuration systems.

Then identify and fix the 5-minute stability issues.
"""

import asyncio
import json
import logging
import time
import sys
from datetime import datetime
from pathlib import Path
import traceback

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known available device from diagnostics
AVAILABLE_DEVICE = "C4:D3:6A:66:7E:D4"  # BT-TH-6A667ED4
CONFIGURED_DEVICE = "D8:B6:73:BF:4F:75"  # The "missing" inverter

async def test_device_connection(mac_address: str, device_name: str | None = None) -> dict:
    """Test a single device connection thoroughly"""
    
    logger.info(f"🧪 Testing device: {device_name or mac_address}")
    
    test_result = {
        'device': mac_address,
        'device_name': device_name,
        'timestamp': datetime.now(),
        'success': False,
        'connection_time': 0.0,
        'data_retrieval_time': 0.0,
        'total_time': 0.0,
        'data_fields': 0,
        'data_sample': {},
        'error': None,
        'details': {}
    }
    
    start_time = time.time()
    
    try:
        # Create client
        client = BluPowClient(mac_address)
        
        # Test connection
        logger.info(f"🔌 Attempting connection to {mac_address}...")
        connection_start = time.time()
        
        connected = await client.connect()
        connection_time = time.time() - connection_start
        test_result['connection_time'] = connection_time
        
        if not connected:
            raise Exception(f"Connection failed after {connection_time:.2f}s")
        
        logger.info(f"✅ Connected successfully in {connection_time:.2f}s")
        
        # Test data retrieval
        logger.info(f"📊 Retrieving device data...")
        data_start = time.time()
        
        device_data = await client.read_device_info()
        cached_data = client.get_data()
        
        data_time = time.time() - data_start
        test_result['data_retrieval_time'] = data_time
        
        if not cached_data or len(cached_data) < 2:
            raise Exception(f"No meaningful data retrieved (got {len(cached_data) if cached_data else 0} fields)")
        
        logger.info(f"📈 Data retrieved successfully: {len(cached_data)} fields in {data_time:.2f}s")
        
        # Analyze data
        test_result.update({
            'success': True,
            'data_fields': len(cached_data),
            'data_sample': {k: v for k, v in list(cached_data.items())[:10]},  # First 10 fields
            'details': {
                'device_info': device_data,
                'all_data_keys': list(cached_data.keys())
            }
        })
        
        # Clean disconnect
        await client.disconnect()
        logger.info(f"🔌 Disconnected cleanly")
        
    except Exception as e:
        error_msg = str(e)
        test_result['error'] = error_msg
        logger.error(f"❌ Test failed: {error_msg}")
        
        # Try to get more details about the error
        if "connection" in error_msg.lower():
            test_result['error_type'] = 'connection'
        elif "data" in error_msg.lower():
            test_result['error_type'] = 'data_retrieval'
        elif "timeout" in error_msg.lower():
            test_result['error_type'] = 'timeout'
        else:
            test_result['error_type'] = 'unknown'
    
    finally:
        test_result['total_time'] = time.time() - start_time
    
    return test_result

async def run_stability_test(mac_address: str, device_name: str, cycles: int = 10):
    """Run multiple test cycles to identify stability issues"""
    
    logger.info(f"🚀 Starting stability test for {device_name}")
    logger.info(f"📊 Device: {mac_address}")
    logger.info(f"🔄 Test cycles: {cycles}")
    logger.info(f"⏱️ Interval: 30s (matching coordinator)")
    
    results = []
    consecutive_failures = 0
    
    for cycle in range(1, cycles + 1):
        logger.info(f"\n🔄 Cycle {cycle}/{cycles}")
        
        # Test the device
        result = await test_device_connection(mac_address, device_name)
        results.append(result)
        
        if result['success']:
            consecutive_failures = 0
            logger.info(f"✅ Cycle {cycle}: SUCCESS - {result['data_fields']} fields in {result['total_time']:.2f}s")
        else:
            consecutive_failures += 1
            logger.error(f"❌ Cycle {cycle}: FAILED - {result['error']}")
            
            # Check for failure patterns
            if consecutive_failures >= 3:
                logger.warning(f"🚨 STABILITY ISSUE: {consecutive_failures} consecutive failures!")
                break
        
        # Sleep between cycles (match coordinator timing)
        if cycle < cycles:
            await asyncio.sleep(30)
    
    # Analyze results
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 STABILITY TEST RESULTS")
    logger.info(f"{'='*60}")
    
    successful_cycles = [r for r in results if r['success']]
    failed_cycles = [r for r in results if not r['success']]
    
    success_rate = (len(successful_cycles) / len(results)) * 100
    
    logger.info(f"📈 Success Rate: {success_rate:.1f}% ({len(successful_cycles)}/{len(results)})")
    logger.info(f"🔄 Total Cycles: {len(results)}")
    logger.info(f"✅ Successful: {len(successful_cycles)}")
    logger.info(f"❌ Failed: {len(failed_cycles)}")
    
    if successful_cycles:
        avg_connection_time = sum(r['connection_time'] for r in successful_cycles) / len(successful_cycles)
        avg_data_time = sum(r['data_retrieval_time'] for r in successful_cycles) / len(successful_cycles)
        avg_total_time = sum(r['total_time'] for r in successful_cycles) / len(successful_cycles)
        
        logger.info(f"⏱️ Avg Connection Time: {avg_connection_time:.2f}s")
        logger.info(f"⏱️ Avg Data Time: {avg_data_time:.2f}s")
        logger.info(f"⏱️ Avg Total Time: {avg_total_time:.2f}s")
    
    if failed_cycles:
        logger.info(f"\n❌ FAILURE ANALYSIS:")
        error_types = {}
        for result in failed_cycles:
            error_type = result.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for error_type, count in error_types.items():
            logger.info(f"  - {error_type}: {count} failures")
        
        # Show recent errors
        logger.info(f"\n🔍 Recent Errors:")
        for result in failed_cycles[-3:]:
            logger.info(f"  - {result['error']}")
    
    # Production readiness assessment
    production_ready = success_rate >= 90 and consecutive_failures < 3
    
    logger.info(f"\n🎯 PRODUCTION READINESS: {'✅ READY' if production_ready else '❌ NOT READY'}")
    
    if not production_ready:
        logger.info(f"🔧 Issues to address:")
        if success_rate < 90:
            logger.info(f"  - Low success rate: {success_rate:.1f}% (need 90%+)")
        if consecutive_failures >= 3:
            logger.info(f"  - Stability issues: {consecutive_failures} consecutive failures")
    
    return results

async def main():
    """Main test execution"""
    print("🔧 Direct Device Test - Getting Available Device Working")
    print("=" * 60)
    
    # Test both devices to understand the situation
    print(f"🔍 Testing available devices:")
    print(f"  1. Available BT-TH: {AVAILABLE_DEVICE}")
    print(f"  2. Configured Inverter: {CONFIGURED_DEVICE}")
    print()
    
    # Test available device first
    print(f"🧪 Testing AVAILABLE device (BT-TH)...")
    available_result = await test_device_connection(AVAILABLE_DEVICE, "BT-TH-6A667ED4")
    
    if available_result['success']:
        print(f"✅ Available device works!")
        print(f"   Data fields: {available_result['data_fields']}")
        print(f"   Sample data: {list(available_result['data_sample'].keys())[:5]}")
        
        # Run stability test on working device
        choice = input(f"\n🚀 Run stability test on working device? (y/n): ").lower()
        if choice == 'y':
            await run_stability_test(AVAILABLE_DEVICE, "BT-TH-6A667ED4", cycles=10)
    else:
        print(f"❌ Available device failed: {available_result['error']}")
    
    print()
    
    # Test configured device
    print(f"🧪 Testing CONFIGURED device (Inverter)...")
    configured_result = await test_device_connection(CONFIGURED_DEVICE, "Configured_Inverter")
    
    if configured_result['success']:
        print(f"✅ Configured device works!")
        print(f"   Data fields: {configured_result['data_fields']}")
        print(f"   Sample data: {list(configured_result['data_sample'].keys())[:5]}")
    else:
        print(f"❌ Configured device failed: {configured_result['error']}")
    
    print(f"\n{'='*60}")
    print(f"📋 SUMMARY AND RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if available_result['success'] and not configured_result['success']:
        print(f"✅ SOLUTION IDENTIFIED:")
        print(f"   - Available device (BT-TH) works: {AVAILABLE_DEVICE}")
        print(f"   - Configured device (Inverter) missing: {CONFIGURED_DEVICE}")
        print(f"   - UPDATE CONFIGURATION to use working device")
        print(f"   - Test stability with working device first")
    elif configured_result['success'] and not available_result['success']:
        print(f"✅ CURRENT CONFIG WORKS:")
        print(f"   - Configured device works: {CONFIGURED_DEVICE}")
        print(f"   - Focus on stability testing with current config")
    elif both_work := (available_result['success'] and configured_result['success']):
        print(f"✅ BOTH DEVICES WORK:")
        print(f"   - Available: {AVAILABLE_DEVICE}")
        print(f"   - Configured: {CONFIGURED_DEVICE}")
        print(f"   - Implement multi-device support")
    else:
        print(f"❌ BOTH DEVICES FAILED:")
        print(f"   - Available error: {available_result['error']}")
        print(f"   - Configured error: {configured_result['error']}")
        print(f"   - Check Bluetooth setup and permissions")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc() 