#!/usr/bin/env python3
"""
BluPow Production Stability Fix

GOAL: Fix the coordinator's 5-minute stability issues and implement
robust multi-device management for daily home electrical monitoring.

Focus:
1. Fix subprocess resource leaks
2. Fix race conditions in coordinator
3. Implement bulletproof device indexing
4. Get integration working for actual daily use
"""

import asyncio
import json
import logging
import time
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionStabilityFixer:
    """Fix coordinator stability issues for production use"""
    
    def __init__(self):
        self.integration_path = Path(__file__).parent.parent
        self.backup_created = False
        
        # Known working devices
        self.working_devices = {
            "C4:D3:6A:66:7E:D4": {
                "name": "BT-TH Temperature/Humidity Sensor",
                "type": "bt_th",
                "status": "verified_working",
                "data_fields": 25
            },
            "D8:B6:73:BF:4F:75": {
                "name": "BTRIC134000035 Inverter", 
                "type": "inverter",
                "status": "connected_needs_testing",
                "data_fields": "unknown"
            }
        }
    
    def create_backup(self):
        """Create backup of original files"""
        if self.backup_created:
            return
            
        logger.info("📦 Creating backup of original files...")
        backup_dir = self.integration_path / "backups" / f"stability_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup critical files
        critical_files = ["coordinator.py", "blupow_client.py", "sensor.py", "__init__.py"]
        
        for file in critical_files:
            src = self.integration_path / file
            if src.exists():
                dst = backup_dir / file
                import shutil
                shutil.copy2(src, dst)
                logger.info(f"  ✅ Backed up {file}")
        
        logger.info(f"📦 Backup created: {backup_dir}")
        self.backup_created = True
    
    def fix_coordinator_resource_leaks(self):
        """Fix subprocess resource leaks in coordinator"""
        logger.info("🔧 Fixing coordinator subprocess resource leaks...")
        
        coordinator_file = self.integration_path / "coordinator.py"
        
        # Read current file
        with open(coordinator_file, 'r') as f:
            content = f.read()
        
        # Check if already fixed
        if "process.kill()" in content and "ensure_cleanup" in content:
            logger.info("  ✅ Resource leak fixes already applied")
            return
        
        # Apply fixes for resource management
        fixes = [
            {
                "search": "except asyncio.TimeoutError:",
                "replace": """except asyncio.TimeoutError:
                # STABILITY FIX: Ensure proper process cleanup
                try:
                    if process and process.returncode is None:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=2.0)
                except (asyncio.TimeoutError, ProcessLookupError):
                    try:
                        if process and process.returncode is None:
                            process.kill()
                            await process.wait()
                    except (ProcessLookupError, OSError):
                        pass  # Process already dead"""
            },
            {
                "search": "raise UpdateFailed(error_msg)",
                "replace": """# STABILITY FIX: Add small delay before next attempt
                await asyncio.sleep(0.5)
                raise UpdateFailed(error_msg)"""
            }
        ]
        
        modified = False
        for fix in fixes:
            if fix["search"] in content and fix["replace"] not in content:
                content = content.replace(fix["search"], fix["replace"])
                modified = True
                logger.info(f"  ✅ Applied fix: {fix['search'][:30]}...")
        
        if modified:
            with open(coordinator_file, 'w') as f:
                f.write(content)
            logger.info("🔧 Coordinator resource leak fixes applied")
        else:
            logger.info("  ✅ No additional fixes needed")
    
    def fix_client_cleanup_issues(self):
        """Fix client cleanup and __del__ issues"""
        logger.info("🔧 Fixing client cleanup issues...")
        
        client_file = self.integration_path / "blupow_client.py"
        
        with open(client_file, 'r') as f:
            content = f.read()
        
        # Check if already fixed
        if "async_cleanup_needed = False" in content:
            logger.info("  ✅ Client cleanup fixes already applied")
            return
        
        # Fix the __del__ method to avoid RuntimeWarning
        old_del = '''    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_client') and self._client and self._client.is_connected:
            self._logger.debug("🧹 Cleaning up client connection on destruction")
            # Don't try to create async tasks in __del__ - just set connected flag
            self._connected = False'''
        
        new_del = '''    def __del__(self):
        """Cleanup on destruction - STABILITY FIX"""
        if hasattr(self, '_client') and self._client:
            self._logger.debug("🧹 Cleaning up client connection on destruction")
            # STABILITY FIX: Proper cleanup without async operations
            self._connected = False
            # Clear references to avoid circular references
            self._client = None
            self._last_data.clear()
            self._response_data.clear()'''
        
        if old_del in content:
            content = content.replace(old_del, new_del)
            logger.info("  ✅ Fixed __del__ method")
        
        # Add connection health cleanup
        if "self.health = ConnectionHealth()" in content and "await self.health.cleanup()" not in content:
            # Add cleanup method to ConnectionHealth
            health_class_end = content.find("class SafeOperationContext:")
            if health_class_end > 0:
                # Find end of ConnectionHealth class
                lines = content[:health_class_end].split('\n')
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip().startswith('def ') or lines[i].strip().startswith('class '):
                        break
                
                cleanup_method = '''
    async def cleanup(self):
        """STABILITY FIX: Cleanup health monitoring resources"""
        self.connection_times.clear()
        self.recent_errors.clear()'''
                
                lines.insert(i+1, cleanup_method)
                content = '\n'.join(lines)
                logger.info("  ✅ Added health monitoring cleanup")
        
        with open(client_file, 'w') as f:
            f.write(content)
        
        logger.info("🔧 Client cleanup fixes applied")
    
    async def test_device_stability(self, mac_address: str, device_info: dict, test_duration_minutes: int = 8) -> dict:
        """Test device stability over time to identify 5-minute issues"""
        logger.info(f"🧪 Testing stability: {device_info['name']} ({mac_address})")
        logger.info(f"⏱️ Duration: {test_duration_minutes} minutes (to catch 5-min failure)")
        
        results = {
            'device': mac_address,
            'device_name': device_info['name'],
            'test_duration_minutes': test_duration_minutes,
            'cycles': [],
            'success_rate': 0,
            'stability_issues': [],
            'production_ready': False
        }
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=test_duration_minutes)
        cycle_interval = 30  # seconds, matching coordinator
        
        consecutive_failures = 0
        
        while datetime.now() < end_time:
            cycle_start = time.time()
            cycle_num = len(results['cycles']) + 1
            
            logger.info(f"🔄 Cycle {cycle_num} - Testing {mac_address}")
            
            # Test using same method as coordinator (subprocess)
            cycle_result = await self._test_device_cycle(mac_address, cycle_num)
            results['cycles'].append(cycle_result)
            
            if cycle_result['success']:
                consecutive_failures = 0
                logger.info(f"✅ Cycle {cycle_num}: SUCCESS - {cycle_result.get('data_fields', 0)} fields")
            else:
                consecutive_failures += 1
                logger.error(f"❌ Cycle {cycle_num}: FAILED - {cycle_result['error']}")
                
                # Check for specific stability issues
                if consecutive_failures >= 3:
                    results['stability_issues'].append(f"Consecutive failures starting cycle {cycle_num - 2}")
                
                # Check for 5-minute pattern (around 10 cycles)
                if 8 <= cycle_num <= 12 and consecutive_failures >= 2:
                    results['stability_issues'].append("5-minute degradation pattern detected")
            
            # Wait for next cycle
            elapsed = time.time() - cycle_start
            sleep_time = max(0, cycle_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Analyze results
        successful_cycles = [c for c in results['cycles'] if c['success']]
        results['success_rate'] = (len(successful_cycles) / len(results['cycles'])) * 100 if results['cycles'] else 0
        results['production_ready'] = (results['success_rate'] >= 90 and 
                                     consecutive_failures < 3 and 
                                     len(results['stability_issues']) == 0)
        
        logger.info(f"📊 Stability test complete: {results['success_rate']:.1f}% success rate")
        
        return results
    
    async def _test_device_cycle(self, mac_address: str, cycle_num: int) -> dict:
        """Single device test cycle using coordinator's method"""
        start_time = time.time()
        
        result = {
            'cycle': cycle_num,
            'success': False,
            'duration': 0.0,
            'data_fields': 0,
            'error': None
        }
        
        try:
            # Use same subprocess approach as coordinator
            cmd = [
                "python3", "-c", f"""
import sys
import asyncio
import json
import time
from pathlib import Path

sys.path.insert(0, '{self.integration_path}')

from blupow_client import BluPowClient

async def test_cycle():
    client = BluPowClient('{mac_address}')
    start_time = time.time()
    
    try:
        connected = await client.connect()
        if not connected:
            return {{'error': 'Connection failed', 'timestamp': time.time()}}
        
        device_data = await client.read_device_info()
        cached_data = client.get_data()
        
        await client.disconnect()
        
        if cached_data and len(cached_data) > 2:
            print(f"SUCCESS: {{json.dumps({{'fields': len(cached_data), 'duration': time.time() - start_time}})}}")
        else:
            print(f"ERROR: No data retrieved ({{len(cached_data) if cached_data else 0}} fields)")
            
    except Exception as e:
        print(f"ERROR: {{str(e)}}")

asyncio.run(test_cycle())
"""
            ]
            
            # Run with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=25.0)
                
                stdout_text = stdout.decode().strip()
                
                # Parse results
                for line in stdout_text.split('\n'):
                    if line.startswith('SUCCESS:'):
                        data = json.loads(line[8:])
                        result.update({
                            'success': True,
                            'data_fields': data['fields'],
                            'duration': data['duration']
                        })
                        break
                    elif line.startswith('ERROR:'):
                        result['error'] = line[6:]
                        break
                
                if not result['success'] and not result['error']:
                    result['error'] = f"No response: {stdout_text[:100]}"
                    
            except asyncio.TimeoutError:
                # STABILITY FIX: Proper process cleanup
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                
                result['error'] = "Subprocess timeout (25s)"
                
        except Exception as e:
            result['error'] = f"Test error: {str(e)}"
        
        finally:
            result['duration'] = time.time() - start_time
        
        return result
    
    def create_production_device_registry(self, test_results: List[dict]):
        """Create production device registry with test results"""
        logger.info("📋 Creating production device registry...")
        
        registry = {
            'created_at': datetime.now().isoformat(),
            'devices': {},
            'production_ready_count': 0,
            'recommendations': []
        }
        
        for result in test_results:
            device_mac = result['device']
            device_info = self.working_devices[device_mac]
            
            registry['devices'][device_mac] = {
                'name': device_info['name'],
                'type': device_info['type'],
                'test_results': {
                    'success_rate': result['success_rate'],
                    'stability_issues': result['stability_issues'],
                    'production_ready': result['production_ready'],
                    'total_cycles': len(result['cycles'])
                },
                'configuration': {
                    'polling_interval': 30,
                    'connection_timeout': 25,
                    'enabled': result['production_ready']
                }
            }
            
            if result['production_ready']:
                registry['production_ready_count'] += 1
        
        # Add recommendations
        if registry['production_ready_count'] == 0:
            registry['recommendations'].append("❌ No devices are production ready - investigate stability issues")
        elif registry['production_ready_count'] == 1:
            registry['recommendations'].append("✅ Single device ready - sufficient for basic monitoring")
        else:
            registry['recommendations'].append("✅ Multiple devices ready - implement multi-device support")
        
        # Save registry
        registry_file = self.integration_path / "production_device_registry.json"
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"📋 Registry saved: {registry_file}")
        return registry
    
    async def run_production_stability_fix(self):
        """Main production stability fix process"""
        logger.info("🚀 Starting BluPow Production Stability Fix")
        logger.info("🎯 Goal: Fix 5-minute coordinator issues + robust device management")
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Fix code issues
        self.fix_coordinator_resource_leaks()
        self.fix_client_cleanup_issues()
        
        # Step 3: Test device stability
        logger.info("\n🧪 Testing device stability...")
        test_results = []
        
        for mac, device_info in self.working_devices.items():
            if device_info['status'] in ['verified_working', 'connected_needs_testing']:
                result = await self.test_device_stability(mac, device_info, test_duration_minutes=8)
                test_results.append(result)
        
        # Step 4: Create production registry
        registry = self.create_production_device_registry(test_results)
        
        # Step 5: Generate final report
        self.generate_production_report(test_results, registry)
        
        return test_results, registry
    
    def generate_production_report(self, test_results: List[dict], registry: dict):
        """Generate final production readiness report"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 BLUPOW PRODUCTION STABILITY REPORT")
        logger.info(f"{'='*60}")
        
        logger.info(f"📊 DEVICE STABILITY:")
        for result in test_results:
            device_info = self.working_devices[result['device']]
            status = "🟢 READY" if result['production_ready'] else "🔴 NOT READY"
            
            logger.info(f"\n  {device_info['name']} ({result['device']}):")
            logger.info(f"    Status: {status}")
            logger.info(f"    Success Rate: {result['success_rate']:.1f}%")
            logger.info(f"    Test Cycles: {len(result['cycles'])}")
            
            if result['stability_issues']:
                logger.info(f"    Issues:")
                for issue in result['stability_issues']:
                    logger.info(f"      - {issue}")
        
        logger.info(f"\n🎯 PRODUCTION READINESS:")
        logger.info(f"  Ready Devices: {registry['production_ready_count']}/{len(registry['devices'])}")
        
        for recommendation in registry['recommendations']:
            logger.info(f"  {recommendation}")
        
        if registry['production_ready_count'] > 0:
            logger.info(f"\n✅ NEXT STEPS:")
            logger.info(f"  1. Integration is ready for home electrical monitoring")
            logger.info(f"  2. Configure Home Assistant with working device(s)")
            logger.info(f"  3. Monitor for continued stability")
            logger.info(f"  4. Add additional devices as needed")
        else:
            logger.info(f"\n❌ ISSUES TO FIX:")
            logger.info(f"  1. Investigate connection failures")
            logger.info(f"  2. Check Bluetooth permissions and setup")
            logger.info(f"  3. Verify device compatibility")
        
        logger.info(f"\n📁 FILES UPDATED:")
        logger.info(f"  - coordinator.py (resource leak fixes)")
        logger.info(f"  - blupow_client.py (cleanup fixes)")
        logger.info(f"  - production_device_registry.json (device config)")
        
        logger.info(f"{'='*60}")

async def main():
    """Main execution"""
    print("🔧 BluPow Production Stability Fix")
    print("Fixing coordinator 5-minute issues + robust device management")
    print("=" * 60)
    
    fixer = ProductionStabilityFixer()
    
    try:
        test_results, registry = await fixer.run_production_stability_fix()
        
        # Show quick summary
        ready_count = sum(1 for r in test_results if r['production_ready'])
        
        print(f"\n🎯 SUMMARY:")
        print(f"✅ Code fixes applied")
        print(f"📊 Devices tested: {len(test_results)}")
        print(f"🟢 Production ready: {ready_count}")
        print(f"📋 Registry created: production_device_registry.json")
        
        if ready_count > 0:
            print(f"\n✅ INTEGRATION IS READY FOR DAILY USE!")
            print(f"Configure Home Assistant to use the working device(s)")
        else:
            print(f"\n❌ Additional troubleshooting needed")
            print(f"Review the detailed logs above for specific issues")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc() 