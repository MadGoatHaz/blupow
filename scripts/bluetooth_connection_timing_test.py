#!/usr/bin/env python3
"""
Bluetooth Connection Timing Test for Renogy Devices

This script tests different connection patterns to find the optimal timing
for connect → get data → disconnect cycles with Renogy BLE devices.
"""

import asyncio
import logging
import time
import sys
import os
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bluetooth_timing_test.log')
    ]
)
logger = logging.getLogger(__name__)

class ConnectionTimingTest:
    """Test different connection timing patterns"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.results = []
        
    async def test_single_connection_cycle(self, test_name: str) -> dict:
        """Test a single connect → get data → disconnect cycle"""
        logger.info(f"🔄 Starting test: {test_name}")
        
        start_time = time.time()
        client = BluPowClient(self.mac_address)
        
        try:
            # Connect
            connect_start = time.time()
            connected = await client.connect()
            connect_time = time.time() - connect_start
            
            if not connected:
                logger.error(f"❌ {test_name}: Failed to connect")
                return {
                    'test_name': test_name,
                    'success': False,
                    'error': 'Connection failed',
                    'total_time': time.time() - start_time
                }
            
            logger.info(f"✅ {test_name}: Connected in {connect_time:.2f}s")
            
            # Get data
            data_start = time.time()
            data = client.get_data()
            data_time = time.time() - data_start
            
            data_success = bool(data and len(data) > 5)  # Should have multiple fields
            logger.info(f"📊 {test_name}: Data retrieval {'✅ SUCCESS' if data_success else '❌ FAILED'} in {data_time:.2f}s")
            
            if data_success:
                logger.info(f"📋 {test_name}: Retrieved {len(data)} data fields")
            
            # Disconnect
            disconnect_start = time.time()
            await client.disconnect()
            disconnect_time = time.time() - disconnect_start
            
            total_time = time.time() - start_time
            
            result = {
                'test_name': test_name,
                'success': data_success,
                'connect_time': connect_time,
                'data_time': data_time,
                'disconnect_time': disconnect_time,
                'total_time': total_time,
                'data_fields': len(data) if data else 0,
                'data_sample': dict(list(data.items())[:3]) if data else {}
            }
            
            logger.info(f"✅ {test_name}: Complete cycle in {total_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ {test_name}: Exception - {e}")
            try:
                await client.disconnect()
            except:
                pass
            
            return {
                'test_name': test_name,
                'success': False,
                'error': str(e),
                'total_time': time.time() - start_time
            }
    
    async def test_rapid_cycles(self, num_cycles: int = 3, delay_between: float = 1.0):
        """Test multiple rapid cycles to find minimum safe interval"""
        logger.info(f"🔄 Testing {num_cycles} rapid cycles with {delay_between}s delay")
        
        results = []
        for i in range(num_cycles):
            result = await self.test_single_connection_cycle(f"Rapid Cycle {i+1}")
            results.append(result)
            
            if i < num_cycles - 1:  # Don't delay after last cycle
                logger.info(f"⏳ Waiting {delay_between}s before next cycle...")
                await asyncio.sleep(delay_between)
        
        return results
    
    async def test_various_intervals(self):
        """Test different intervals between connections"""
        intervals = [0.5, 1.0, 2.0, 5.0, 10.0]
        
        logger.info("🧪 Testing various intervals between connections")
        
        for interval in intervals:
            logger.info(f"📊 Testing {interval}s interval")
            
            # First connection
            result1 = await self.test_single_connection_cycle(f"Interval Test {interval}s - First")
            
            # Wait specified interval
            logger.info(f"⏳ Waiting {interval}s...")
            await asyncio.sleep(interval)
            
            # Second connection
            result2 = await self.test_single_connection_cycle(f"Interval Test {interval}s - Second")
            
            # Analyze results
            both_successful = result1['success'] and result2['success']
            logger.info(f"📈 {interval}s interval: {'✅ BOTH SUCCESSFUL' if both_successful else '❌ ONE OR BOTH FAILED'}")
            
            self.results.extend([result1, result2])
            
            # Longer pause between different interval tests
            if interval != intervals[-1]:
                await asyncio.sleep(3.0)
    
    async def test_connection_persistence(self):
        """Test how long a connection can stay open before timing out"""
        logger.info("🔄 Testing connection persistence")
        
        client = BluPowClient(self.mac_address)
        start_time = time.time()
        
        try:
            # Connect
            connected = await client.connect()
            if not connected:
                logger.error("❌ Failed to connect for persistence test")
                return
            
            logger.info("✅ Connected for persistence test")
            
            # Try to get data at intervals while keeping connection open
            intervals = [0, 10, 20, 30, 45, 60]  # seconds
            
            for interval in intervals:
                if interval > 0:
                    logger.info(f"⏳ Waiting {interval}s with connection open...")
                    await asyncio.sleep(interval - (intervals[intervals.index(interval)-1] if interval != intervals[0] else 0))
                
                try:
                    data = client.get_data()
                    success = bool(data and len(data) > 5)
                    elapsed = time.time() - start_time
                    
                    logger.info(f"📊 At {elapsed:.1f}s: Data retrieval {'✅ SUCCESS' if success else '❌ FAILED'}")
                    
                    if not success:
                        logger.warning(f"⚠️  Connection appears to have timed out after {elapsed:.1f}s")
                        break
                        
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(f"❌ At {elapsed:.1f}s: Exception - {e}")
                    break
            
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Persistence test exception: {e}")
            try:
                await client.disconnect()
            except:
                pass
    
    def print_summary(self):
        """Print test results summary"""
        if not self.results:
            logger.info("📋 No test results to summarize")
            return
        
        successful_tests = [r for r in self.results if r.get('success', False)]
        failed_tests = [r for r in self.results if not r.get('success', False)]
        
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful tests: {len(successful_tests)}")
        logger.info(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            avg_total_time = sum(r['total_time'] for r in successful_tests) / len(successful_tests)
            avg_connect_time = sum(r.get('connect_time', 0) for r in successful_tests) / len(successful_tests)
            avg_data_time = sum(r.get('data_time', 0) for r in successful_tests) / len(successful_tests)
            
            logger.info(f"⏱️  Average total cycle time: {avg_total_time:.2f}s")
            logger.info(f"🔗 Average connect time: {avg_connect_time:.2f}s")
            logger.info(f"📊 Average data retrieval time: {avg_data_time:.2f}s")
        
        if failed_tests:
            logger.info("❌ Failed test details:")
            for test in failed_tests:
                logger.info(f"   - {test['test_name']}: {test.get('error', 'Unknown error')}")

async def main():
    """Main test function"""
    # You need to update this MAC address to match your Renogy device
    MAC_ADDRESS = "E0:5A:1B:C1:34:00"  # Replace with your device's MAC
    
    if len(sys.argv) > 1:
        MAC_ADDRESS = sys.argv[1]
    
    logger.info("🚀 Starting Bluetooth Connection Timing Tests")
    logger.info(f"🎯 Target device: {MAC_ADDRESS}")
    logger.info("=" * 60)
    
    tester = ConnectionTimingTest(MAC_ADDRESS)
    
    try:
        # Test 1: Basic single connection
        logger.info("🧪 TEST 1: Basic single connection cycle")
        result = await tester.test_single_connection_cycle("Basic Single Connection")
        tester.results.append(result)
        
        await asyncio.sleep(2)
        
        # Test 2: Rapid cycles
        logger.info("\n🧪 TEST 2: Rapid connection cycles")
        rapid_results = await tester.test_rapid_cycles(3, 1.0)
        tester.results.extend(rapid_results)
        
        await asyncio.sleep(5)
        
        # Test 3: Various intervals
        logger.info("\n🧪 TEST 3: Various intervals between connections")
        await tester.test_various_intervals()
        
        await asyncio.sleep(5)
        
        # Test 4: Connection persistence
        logger.info("\n🧪 TEST 4: Connection persistence test")
        await tester.test_connection_persistence()
        
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
    
    finally:
        logger.info("\n📋 Generating test summary...")
        tester.print_summary()
        
        logger.info("\n💡 RECOMMENDATIONS:")
        logger.info("- Use connect → get data → disconnect pattern")
        logger.info("- Allow 2-5 seconds between connection cycles")
        logger.info("- Don't keep connections open longer than 30 seconds")
        logger.info("- Monitor connection health and retry on failures")

if __name__ == "__main__":
    asyncio.run(main()) 