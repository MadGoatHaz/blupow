#!/usr/bin/env python3
"""
Bluetooth Connection Fix for BluPow

This script implements the proper connect → get data → disconnect pattern
for Renogy devices, addressing the timing issues that cause data retrieval failures.
"""

import asyncio
import logging
import time
import json
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_proper_connection_cycle(mac_address: str):
    """Test the proper connect → get data → disconnect cycle"""
    print(f"🔄 Testing proper connection cycle for {mac_address}")
    
    for attempt in range(3):
        print(f"\n🔄 Attempt {attempt + 1}/3")
        
        try:
            client = BluPowClient(mac_address)
            
            # Step 1: Connect
            print("  🔌 Connecting...")
            start_time = time.time()
            connected = await client.connect()
            connect_time = time.time() - start_time
            
            if not connected:
                print(f"  ❌ Connection failed in {connect_time:.1f}s")
                await asyncio.sleep(5)
                continue
            
            print(f"  ✅ Connected in {connect_time:.1f}s")
            
            # Step 2: Wait for device to be ready (CRITICAL!)
            print("  ⏱️ Waiting for device to be ready...")
            await asyncio.sleep(2.0)  # Give device time to initialize
            
            # Step 3: Get data
            print("  📊 Retrieving data...")
            data_start = time.time()
            data = client.get_data()
            data_time = time.time() - data_start
            
            print(f"  📊 Data retrieval took {data_time:.1f}s")
            print(f"  📊 Data fields: {len(data) if data else 0}")
            
            if data and len(data) > 0:
                print(f"  ✅ SUCCESS! Retrieved {len(data)} fields")
                print(f"  📋 Model: {data.get('model', 'Unknown')}")
                print(f"  🔋 Battery: {data.get('battery_voltage', 'Unknown')}V")
                print(f"  ⚡ Load: {data.get('load_power', 'Unknown')}W")
                
                # Step 4: Disconnect
                print("  🔌 Disconnecting...")
                await client.disconnect()
                print("  ✅ Disconnected cleanly")
                
                return data
            else:
                print("  ❌ No data retrieved")
                await client.disconnect()
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            try:
                await client.disconnect()
            except:
                pass
        
        # Wait between attempts
        if attempt < 2:
            print("  ⏱️ Waiting 5s before next attempt...")
            await asyncio.sleep(5.0)
    
    print("❌ All attempts failed")
    return None

async def test_rapid_cycles(mac_address: str, cycles: int = 5):
    """Test rapid connect → get data → disconnect cycles"""
    print(f"\n🔄 Testing {cycles} rapid cycles...")
    
    successful_cycles = 0
    total_time = 0.0
    
    for i in range(cycles):
        print(f"\n🔄 Cycle {i + 1}/{cycles}")
        
        try:
            cycle_start = time.time()
            
            client = BluPowClient(mac_address)
            
            # Connect
            connected = await client.connect()
            if not connected:
                print("  ❌ Connection failed")
                continue
            
            # Wait for readiness
            await asyncio.sleep(1.5)
            
            # Get data
            data = client.get_data()
            
            # Disconnect immediately
            await client.disconnect()
            
            cycle_time = time.time() - cycle_start
            total_time += cycle_time
            
            if data and len(data) > 5:
                successful_cycles += 1
                print(f"  ✅ Success in {cycle_time:.1f}s ({len(data)} fields)")
            else:
                print(f"  ❌ No data in {cycle_time:.1f}s")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Wait between cycles (CRITICAL for BLE devices!)
        if i < cycles - 1:
            await asyncio.sleep(3.0)
    
    success_rate = successful_cycles / cycles
    avg_time = total_time / successful_cycles if successful_cycles > 0 else 0.0
    
    print(f"\n📊 Rapid Cycle Results:")
    print(f"  Success Rate: {success_rate*100:.0f}% ({successful_cycles}/{cycles})")
    print(f"  Average Time: {avg_time:.1f}s")
    
    return success_rate, avg_time

async def find_optimal_timing(mac_address: str):
    """Find the optimal timing parameters"""
    print(f"\n⏱️ Finding optimal timing for {mac_address}")
    
    # Test different wait times after connection
    wait_times = [0.5, 1.0, 1.5, 2.0, 3.0]
    
    for wait_time in wait_times:
        print(f"\n⏱️ Testing {wait_time}s wait time...")
        
        success_count = 0
        for i in range(3):
            try:
                client = BluPowClient(mac_address)
                
                connected = await client.connect()
                if connected:
                    await asyncio.sleep(wait_time)  # Variable wait time
                    data = client.get_data()
                    await client.disconnect()
                    
                    if data and len(data) > 5:
                        success_count += 1
                        print(f"    Test {i+1}: ✅ Success")
                    else:
                        print(f"    Test {i+1}: ❌ No data")
                else:
                    print(f"    Test {i+1}: ❌ Connection failed")
                
                await asyncio.sleep(2.0)  # Wait between tests
                
            except Exception as e:
                print(f"    Test {i+1}: ❌ Error: {e}")
        
        success_rate = success_count / 3
        print(f"  {wait_time}s wait: {success_rate*100:.0f}% success")
        
        if success_rate >= 0.8:  # 80% success threshold
            print(f"  🎯 Optimal wait time found: {wait_time}s")
            return wait_time
    
    print("  ⚠️ No optimal wait time found, using default 2.0s")
    return 2.0

async def test_subprocess_format(mac_address: str):
    """Test the exact format expected by the coordinator subprocess"""
    print(f"\n🔧 Testing subprocess format for {mac_address}")
    
    try:
        client = BluPowClient(mac_address)
        
        connected = await client.connect()
        if connected:
            await asyncio.sleep(2.0)  # Wait for readiness
            data = client.get_data()
            await client.disconnect()
            
            if data and len(data) > 0:
                # This is the exact format the coordinator expects
                success_output = f"SUCCESS: {json.dumps(data)}"
                print("📤 Subprocess output format:")
                print(success_output)
                return success_output
            else:
                error_output = "ERROR: No data retrieved"
                print("📤 Subprocess output format:")
                print(error_output)
                return error_output
        else:
            error_output = "ERROR: Connection failed"
            print("📤 Subprocess output format:")
            print(error_output)
            return error_output
            
    except Exception as e:
        error_output = f"ERROR: {e}"
        print("📤 Subprocess output format:")
        print(error_output)
        return error_output

async def main():
    """Main testing workflow"""
    # Use the discovered device
    mac_address = "D8:B6:73:BF:4F:75"
    
    print("🚀 BluPow Bluetooth Connection Fix")
    print("=" * 50)
    print(f"Testing device: {mac_address}")
    
    try:
        # Test 1: Proper connection cycle
        print("\n🧪 TEST 1: Proper Connection Cycle")
        data = await test_proper_connection_cycle(mac_address)
        
        if data:
            print("✅ Basic connection cycle working!")
            
            # Test 2: Find optimal timing
            print("\n🧪 TEST 2: Optimal Timing Analysis")
            optimal_wait = await find_optimal_timing(mac_address)
            
            # Test 3: Rapid cycles with optimal timing
            print("\n🧪 TEST 3: Rapid Cycles Test")
            success_rate, avg_time = await test_rapid_cycles(mac_address, cycles=5)
            
            # Test 4: Subprocess format
            print("\n🧪 TEST 4: Subprocess Format Test")
            subprocess_output = await test_subprocess_format(mac_address)
            
            # Final recommendations
            print("\n🎯 RECOMMENDATIONS:")
            print(f"  • Optimal wait time after connect: {optimal_wait}s")
            print(f"  • Rapid cycle success rate: {success_rate*100:.0f}%")
            print(f"  • Average cycle time: {avg_time:.1f}s")
            print(f"  • Recommended polling interval: {max(avg_time * 3, 15.0):.0f}s")
            
            if success_rate >= 0.8:
                print("✅ Device is ready for reliable operation!")
            else:
                print("⚠️ Device may need longer intervals or additional tuning")
        else:
            print("❌ Basic connection cycle failed - device may not be compatible")
    
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted")
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
    
    print("\n✨ Connection fix testing complete!")

if __name__ == "__main__":
    asyncio.run(main()) 