#!/usr/bin/env python3
"""
BluPow Focused Stability Test

NO EXTERNAL DEPENDENCIES - Focus on core stability issues:
1. Race conditions causing 5-minute failures  
2. Resource cleanup problems
3. Subprocess management issues
4. Memory/connection leaks

Goal: Identify and fix what's breaking the working setup
"""

import asyncio
import json
import logging
import time
import sys
import os
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'stability_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class FocusedStabilityTest:
    """Focused stability testing to identify the 5-minute failure pattern"""
    
    def __init__(self, mac_address: str = "D8:B6:73:BF:4F:75"):
        self.mac_address = mac_address
        self.test_cycles = []
        self.running_processes = []
        self.start_time = None
        
        # Test configuration - match real usage
        self.test_duration_minutes = 10  # Extended test to catch 5-min failure
        self.poll_interval_seconds = 30  # Match HA coordinator exactly
        
        # Health tracking
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.total_attempts = 0
        self.successful_attempts = 0
        
        # Resource tracking
        self.active_subprocesses = set()
        
    def cleanup_processes(self):
        """Clean up any hanging processes"""
        logger.info("🧹 Cleaning up processes...")
        
        # Kill any remaining subprocesses
        for proc in list(self.active_subprocesses):
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    time.sleep(1)
                    if proc.poll() is None:
                        proc.kill()
                    logger.info(f"🔪 Killed subprocess {proc.pid}")
                self.active_subprocesses.discard(proc)
            except:
                pass
    
    async def test_single_cycle(self) -> Dict[str, Any]:
        """Test a single data retrieval cycle - exactly like the coordinator"""
        cycle_start = time.time()
        
        result = {
            'cycle_number': len(self.test_cycles) + 1,
            'start_time': cycle_start,
            'success': False,
            'duration': 0.0,
            'data_fields': 0,
            'error': None,
            'subprocess_id': None,
            'stdout': '',
            'stderr': ''
        }
        
        try:
            logger.info(f"🔄 Cycle {result['cycle_number']}: Testing {self.mac_address}")
            
            # Create the exact subprocess command used by coordinator
            cmd = [
                "python3", "-c", f"""
import sys
import asyncio
import json
import logging
import time
from pathlib import Path

# Add the integration directory to the path
sys.path.insert(0, '{Path(__file__).parent.parent}')

from blupow_client import BluPowClient

async def get_data():
    client = BluPowClient('{self.mac_address}')
    start_time = time.time()
    
    try:
        # Connect
        connected = await client.connect()
        if not connected:
            return {{'error': 'Connection failed', 'timestamp': time.time()}}
        
        # Read device info first (this populates the internal cache)
        device_data = await client.read_device_info()
        
        # Get cached data (this is what the coordinator expects)
        data = client.get_data()
        
        # Disconnect
        await client.disconnect()
        
        # Add metadata
        if data and len(data) > 2:  # More than just connection_status and last_update
            data['_test_meta'] = {{
                'cycle_time': time.time() - start_time,
                'timestamp': time.time(),
                'mac_address': '{self.mac_address}',
                'connection_method': 'cycle'
            }}
            print(f"SUCCESS: {{json.dumps(data)}}")
        else:
            print(f"ERROR: No data retrieved (got {{len(data) if data else 0}} fields: {{list(data.keys()) if data else 'None'}})")
            
    except Exception as e:
        print(f"ERROR: {{str(e)}}")

asyncio.run(get_data())
"""
            ]
            
            # Create subprocess with same settings as coordinator
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            result['subprocess_id'] = process.pid
            self.active_subprocesses.add(process)
            
            try:
                # Same timeout as coordinator
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=30.0
                )
                
                # Remove from active tracking
                self.active_subprocesses.discard(process)
                
                result['stdout'] = stdout.decode().strip()
                result['stderr'] = stderr.decode().strip()
                
                # Parse results exactly like coordinator
                success_line = None
                for line in result['stdout'].split('\n'):
                    if line.startswith('SUCCESS:'):
                        success_line = line[8:].strip()
                        break
                
                if success_line:
                    try:
                        data = json.loads(success_line)
                        result['success'] = True
                        result['data_fields'] = len(data)
                        result['sample_data'] = {k: v for k, v in list(data.items())[:3]}
                        
                        self.consecutive_successes += 1
                        self.consecutive_failures = 0
                        self.successful_attempts += 1
                        
                        logger.info(f"✅ Cycle {result['cycle_number']}: Success - {len(data)} fields in {result['duration']:.2f}s")
                        
                    except json.JSONDecodeError as e:
                        result['error'] = f"JSON decode error: {e}"
                        logger.error(f"❌ Cycle {result['cycle_number']}: {result['error']}")
                else:
                    # Look for error
                    error_line = None
                    for line in result['stdout'].split('\n'):
                        if line.startswith('ERROR:'):
                            error_line = line[6:].strip()
                            break
                    result['error'] = error_line or "No data received"
                    logger.error(f"❌ Cycle {result['cycle_number']}: {result['error']}")
                
            except asyncio.TimeoutError:
                # Handle timeout exactly like coordinator
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"🔪 Force killing subprocess {process.pid}")
                    process.kill()
                    await process.wait()
                
                self.active_subprocesses.discard(process)
                result['error'] = "Subprocess timeout (30s)"
                logger.error(f"❌ Cycle {result['cycle_number']}: {result['error']}")
                
        except Exception as e:
            result['error'] = f"Cycle error: {str(e)}"
            logger.error(f"❌ Cycle {result['cycle_number']}: {result['error']}")
        
        finally:
            result['duration'] = time.time() - cycle_start
            self.total_attempts += 1
            
            if not result['success']:
                self.consecutive_failures += 1
                self.consecutive_successes = 0
        
        return result
    
    async def run_stability_test(self):
        """Run the focused stability test"""
        logger.info(f"🚀 Starting {self.test_duration_minutes}-minute focused stability test")
        logger.info(f"📊 Device: {self.mac_address}")
        logger.info(f"⏱️ Poll interval: {self.poll_interval_seconds}s (matching HA coordinator)")
        
        self.start_time = datetime.now()
        
        try:
            end_time = self.start_time + timedelta(minutes=self.test_duration_minutes)
            
            while datetime.now() < end_time:
                cycle_result = await self.test_single_cycle()
                self.test_cycles.append(cycle_result)
                
                # Log status every 5 cycles
                if len(self.test_cycles) % 5 == 0:
                    self.log_status()
                
                # Check for the "5-minute death" pattern
                if len(self.test_cycles) >= 10:  # After 5 minutes of 30s intervals
                    recent_failures = sum(1 for c in self.test_cycles[-5:] if not c['success'])
                    if recent_failures >= 4:
                        logger.warning(f"🚨 DETECTED 5-MINUTE FAILURE PATTERN - {recent_failures}/5 recent failures!")
                        self.analyze_failure_pattern()
                
                # Wait for next cycle (exactly like coordinator)
                sleep_time = max(0, self.poll_interval_seconds - cycle_result['duration'])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.cleanup_processes()
            self.generate_report()
    
    def log_status(self):
        """Log current test status"""
        if self.total_attempts > 0:
            success_rate = (self.successful_attempts / self.total_attempts) * 100
            elapsed = datetime.now() - self.start_time
            
            logger.info(f"📊 Status: {self.successful_attempts}/{self.total_attempts} success ({success_rate:.1f}%) | "
                       f"Consecutive: {self.consecutive_successes} success, {self.consecutive_failures} failures | "
                       f"Elapsed: {elapsed}")
    
    def analyze_failure_pattern(self):
        """Analyze the failure pattern to identify root cause"""
        logger.info(f"\n🔍 ANALYZING FAILURE PATTERN:")
        
        # Look at last 10 cycles
        recent_cycles = self.test_cycles[-10:]
        
        # Check for subprocess issues
        subprocess_timeouts = sum(1 for c in recent_cycles if 'timeout' in (c.get('error', '').lower()))
        connection_failures = sum(1 for c in recent_cycles if 'connection failed' in (c.get('error', '').lower()))
        json_errors = sum(1 for c in recent_cycles if 'json' in (c.get('error', '').lower()))
        
        logger.info(f"  Subprocess timeouts: {subprocess_timeouts}/10")
        logger.info(f"  Connection failures: {connection_failures}/10")
        logger.info(f"  JSON decode errors: {json_errors}/10")
        
        # Check for increasing duration (resource buildup)
        durations = [c['duration'] for c in recent_cycles if c['duration'] > 0]
        if len(durations) >= 5:
            avg_early = sum(durations[:3]) / 3
            avg_late = sum(durations[-3:]) / 3
            if avg_late > avg_early * 1.5:
                logger.warning(f"  🐛 RESOURCE BUILDUP DETECTED: Duration increased {avg_early:.2f}s → {avg_late:.2f}s")
        
        # Check stderr for bluetooth issues
        stderr_issues = []
        for c in recent_cycles:
            if c.get('stderr') and len(c['stderr']) > 10:
                stderr_issues.append(c['stderr'][:100])
        
        if stderr_issues:
            logger.info(f"  Recent stderr issues: {len(stderr_issues)}")
            for issue in stderr_issues[-3:]:
                logger.info(f"    - {issue}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        test_duration = datetime.now() - self.start_time
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 FOCUSED STABILITY TEST REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"⏱️ Test Duration: {test_duration}")
        logger.info(f"🔄 Total Cycles: {len(self.test_cycles)}")
        logger.info(f"📊 Success Rate: {(self.successful_attempts/self.total_attempts)*100:.1f}% ({self.successful_attempts}/{self.total_attempts})")
        logger.info(f"🔗 Consecutive Failures: {self.consecutive_failures}")
        
        # Timing analysis
        successful_cycles = [c for c in self.test_cycles if c['success']]
        if successful_cycles:
            avg_duration = sum(c['duration'] for c in successful_cycles) / len(successful_cycles)
            logger.info(f"⏱️ Average Successful Cycle: {avg_duration:.2f}s")
        
        # Failure analysis
        failed_cycles = [c for c in self.test_cycles if not c['success']]
        if failed_cycles:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            error_types = {}
            for cycle in failed_cycles:
                error = cycle.get('error', 'Unknown')
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                logger.info(f"  - {error}: {count} times")
        
        # 5-minute pattern check
        if len(self.test_cycles) >= 10:
            early_success = sum(1 for c in self.test_cycles[:5] if c['success'])
            late_success = sum(1 for c in self.test_cycles[-5:] if c['success'])
            
            logger.info(f"\n🕐 TIME-BASED PATTERN:")
            logger.info(f"  Early success (first 5): {early_success}/5")
            logger.info(f"  Late success (last 5): {late_success}/5")
            
            if early_success >= 3 and late_success <= 2:
                logger.warning(f"  🚨 CONFIRMED: 5-minute degradation pattern detected!")
                logger.warning(f"  🔧 RECOMMENDATION: Focus on resource cleanup and subprocess management")
        
        # Resource tracking
        logger.info(f"\n🧹 RESOURCE TRACKING:")
        logger.info(f"  Active subprocesses at end: {len(self.active_subprocesses)}")
        if self.active_subprocesses:
            logger.warning(f"  🐛 RESOURCE LEAK: {len(self.active_subprocesses)} processes not cleaned up")
        
        # Production readiness
        production_ready = (
            self.successful_attempts / self.total_attempts > 0.9 and
            self.consecutive_failures < 3 and
            len(self.active_subprocesses) == 0
        )
        
        logger.info(f"\n🎯 PRODUCTION READINESS: {'✅ READY' if production_ready else '❌ NOT READY'}")
        
        if not production_ready:
            logger.info(f"  Issues to fix:")
            if self.successful_attempts / self.total_attempts <= 0.9:
                logger.info(f"    - Low success rate ({(self.successful_attempts/self.total_attempts)*100:.1f}% < 90%)")
            if self.consecutive_failures >= 3:
                logger.info(f"    - Too many consecutive failures ({self.consecutive_failures})")
            if len(self.active_subprocesses) > 0:
                logger.info(f"    - Resource leaks ({len(self.active_subprocesses)} active processes)")
        
        logger.info(f"{'='*60}")

async def main():
    """Main test execution"""
    print("🔧 BluPow Focused Stability Test")
    print("Focus: Identify the 5-minute failure pattern")
    print("=" * 50)
    
    # Use the known working inverter MAC
    test = FocusedStabilityTest("D8:B6:73:BF:4F:75")
    
    print(f"Testing device: {test.mac_address}")
    print(f"Test duration: {test.test_duration_minutes} minutes")
    print(f"Poll interval: {test.poll_interval_seconds} seconds")
    print(f"Expected cycles: {int(test.test_duration_minutes * 60 / test.poll_interval_seconds)}")
    print()
    
    await test.run_stability_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc() 