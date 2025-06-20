#!/usr/bin/env python3
"""
BluPow Stability Test Script
Tests the reliability improvements to the subprocess coordinator.
"""

import asyncio
import sys
import time
import logging
from datetime import datetime

# Add the custom component path
sys.path.append("/config/custom_components")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_connection_stability():
    """Test connection stability with multiple attempts."""
    print("🔧 BluPow Stability Test")
    print("=" * 50)
    
    mac_address = "D8:B6:73:BF:4F:75"
    total_tests = 10
    success_count = 0
    failure_count = 0
    timeout_count = 0
    
    results = []
    
    for test_num in range(1, total_tests + 1):
        print(f"\n📊 Test {test_num}/{total_tests}")
        print("-" * 30)
        
        start_time = time.time()
        
        # Create the same subprocess script as the coordinator
        script = f'''
import asyncio
import sys
import logging
import signal

# Configure minimal logging
logging.basicConfig(level=logging.ERROR)
sys.path.append("/config/custom_components")

# Timeout handler
def timeout_handler(signum, frame):
    print("ERROR:Script timeout")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(35)  # Timeout

async def get_data():
    client = None
    try:
        from blupow.blupow_client import BluPowClient
        
        client = BluPowClient("{mac_address}")
        
        # Connection attempt with retries
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"RETRY:Attempt {{attempt + 1}}")
                    await asyncio.sleep(2.0)
                
                connected = await client.connect()
                if connected:
                    break
                else:
                    if attempt == max_retries - 1:
                        print("ERROR:All connection attempts failed")
                        return False
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"ERROR:Connection exception: {{str(e)}}")
                    return False
        
        # Read data
        data = await client.read_device_info()
        
        # CRITICAL: Properly await disconnect
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception as e:
            print(f"WARNING:Disconnect error: {{str(e)}}")
        
        if data and len(data) > 0:
            json_data = {{}}
            for k, v in data.items():
                if v is not None:
                    json_data[k] = str(v) if not isinstance(v, (int, float, bool, str)) else v
                else:
                    json_data[k] = None
            
            print("SUCCESS:" + str(json_data))
            return True
        else:
            print("ERROR:No data retrieved")
            return False
            
    except Exception as e:
        print(f"ERROR:Script exception: {{str(e)}}")
        return False
    finally:
        if client:
            try:
                if hasattr(client, 'is_connected') and client.is_connected:
                    await client.disconnect()
            except Exception:
                pass
        signal.alarm(0)

try:
    result = asyncio.run(get_data())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"ERROR:Runtime exception: {{str(e)}}")
    sys.exit(1)
'''
        
        try:
            # Run subprocess test
            process = await asyncio.create_subprocess_exec(
                'python3', '-c', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                execution_time = time.time() - start_time
                
                output = stdout.decode().strip()
                stderr_output = stderr.decode().strip()
                
                if output.startswith("SUCCESS:"):
                    success_count += 1
                    print(f"✅ SUCCESS in {execution_time:.1f}s")
                    
                    # Extract key data
                    try:
                        data_str = output[8:]
                        data = eval(data_str)
                        key_values = {k: v for k, v in data.items() 
                                    if k in ['model', 'input_voltage', 'battery_voltage', 'temperature'] 
                                    and v is not None}
                        print(f"📊 Data: {key_values}")
                    except:
                        print("📊 Data parsing failed")
                    
                    results.append({
                        'test': test_num,
                        'status': 'success',
                        'time': execution_time,
                        'data_fields': len(data) if 'data' in locals() else 0
                    })
                    
                elif output.startswith("ERROR:"):
                    failure_count += 1
                    error_msg = output[6:]
                    print(f"❌ FAILED: {error_msg}")
                    results.append({
                        'test': test_num,
                        'status': 'failed',
                        'time': execution_time,
                        'error': error_msg
                    })
                    
                else:
                    failure_count += 1
                    print(f"❌ UNKNOWN OUTPUT: {output}")
                    results.append({
                        'test': test_num,
                        'status': 'unknown',
                        'time': execution_time,
                        'output': output
                    })
                
                if stderr_output:
                    print(f"⚠️ stderr: {stderr_output}")
                    
            except asyncio.TimeoutError:
                timeout_count += 1
                execution_time = time.time() - start_time
                print(f"⏰ TIMEOUT after {execution_time:.1f}s")
                
                if process.returncode is None:
                    process.kill()
                    
                results.append({
                    'test': test_num,
                    'status': 'timeout',
                    'time': execution_time
                })
                
        except Exception as e:
            failure_count += 1
            execution_time = time.time() - start_time
            print(f"💥 EXCEPTION: {e}")
            results.append({
                'test': test_num,
                'status': 'exception',
                'time': execution_time,
                'error': str(e)
            })
        
        # Brief delay between tests
        await asyncio.sleep(2.0)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📈 STABILITY TEST RESULTS")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Successes: {success_count} ({success_count/total_tests*100:.1f}%)")
    print(f"❌ Failures: {failure_count} ({failure_count/total_tests*100:.1f}%)")
    print(f"⏰ Timeouts: {timeout_count} ({timeout_count/total_tests*100:.1f}%)")
    
    # Calculate average times
    success_times = [r['time'] for r in results if r['status'] == 'success']
    if success_times:
        avg_success_time = sum(success_times) / len(success_times)
        print(f"⏱️ Average Success Time: {avg_success_time:.1f}s")
    
    # Stability assessment
    success_rate = success_count / total_tests
    if success_rate >= 0.9:
        print("🎉 EXCELLENT stability (≥90% success)")
    elif success_rate >= 0.7:
        print("✅ GOOD stability (≥70% success)")
    elif success_rate >= 0.5:
        print("⚠️ MODERATE stability (≥50% success)")
    else:
        print("❌ POOR stability (<50% success)")
    
    return success_rate >= 0.8  # Consider 80%+ as acceptable

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection_stability())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1) 