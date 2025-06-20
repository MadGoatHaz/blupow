#!/usr/bin/env python3
"""
BluPow Health Monitor - Comprehensive Integration Health Tracking

This script provides continuous monitoring and diagnostics for the BluPow integration,
tracking performance metrics, detecting issues, and providing automated recovery suggestions.
"""

import asyncio
import logging
import time
import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blupow_health_monitor.log', mode='a')
    ]
)
_LOGGER = logging.getLogger(__name__)

class HealthMetrics:
    """Comprehensive health metrics tracking"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'consecutive_failures': 0,
            'max_consecutive_failures': 0,
            'average_response_time': 0.0,
            'response_times': [],
            'error_patterns': {},
            'health_score': 100.0,
            'last_success_time': None,
            'last_failure_time': None,
            'uptime_seconds': 0,
            'system_issues': [],
            'recommendations': []
        }
        
    def record_check(self, success: bool, response_time: float = 0.0, error_type: str = None):
        """Record a health check result"""
        self.metrics['total_checks'] += 1
        
        if success:
            self.metrics['successful_checks'] += 1
            self.metrics['consecutive_failures'] = 0
            self.metrics['last_success_time'] = time.time()
            
            if response_time > 0:
                self.metrics['response_times'].append(response_time)
                # Keep only last 100 response times
                if len(self.metrics['response_times']) > 100:
                    self.metrics['response_times'].pop(0)
                self.metrics['average_response_time'] = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        else:
            self.metrics['failed_checks'] += 1
            self.metrics['consecutive_failures'] += 1
            self.metrics['last_failure_time'] = time.time()
            
            if self.metrics['consecutive_failures'] > self.metrics['max_consecutive_failures']:
                self.metrics['max_consecutive_failures'] = self.metrics['consecutive_failures']
            
            if error_type:
                if error_type not in self.metrics['error_patterns']:
                    self.metrics['error_patterns'][error_type] = 0
                self.metrics['error_patterns'][error_type] += 1
        
        # Update health score
        self._calculate_health_score()
        self.metrics['uptime_seconds'] = time.time() - self.start_time
    
    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if self.metrics['total_checks'] == 0:
            return 100.0
        
        # Base score from success rate
        success_rate = self.metrics['successful_checks'] / self.metrics['total_checks']
        base_score = success_rate * 100
        
        # Penalties for consecutive failures
        consecutive_penalty = min(self.metrics['consecutive_failures'] * 5, 30)
        
        # Penalty for slow response times
        response_penalty = 0
        if self.metrics['average_response_time'] > 30:
            response_penalty = min((self.metrics['average_response_time'] - 30) * 2, 20)
        
        # Penalty for system issues
        system_issues_penalty = len(self.metrics['system_issues']) * 5
        
        final_score = max(0, base_score - consecutive_penalty - response_penalty - system_issues_penalty)
        self.metrics['health_score'] = round(final_score, 1)
        return final_score
    
    def get_health_status(self) -> str:
        """Get textual health status"""
        score = self.metrics['health_score']
        if score >= 90:
            return "🟢 EXCELLENT"
        elif score >= 70:
            return "🟡 GOOD"
        elif score >= 50:
            return "🟠 DEGRADED"
        elif score >= 20:
            return "🔴 POOR"
        else:
            return "💀 CRITICAL"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        return {
            'health_score': self.metrics['health_score'],
            'health_status': self.get_health_status(),
            'uptime_hours': round(self.metrics['uptime_seconds'] / 3600, 1),
            'success_rate': round(self.metrics['successful_checks'] / max(self.metrics['total_checks'], 1) * 100, 1),
            'consecutive_failures': self.metrics['consecutive_failures'],
            'average_response_time': round(self.metrics['average_response_time'], 2),
            'total_checks': self.metrics['total_checks'],
            'error_patterns': self.metrics['error_patterns'],
            'system_issues': self.metrics['system_issues'],
            'recommendations': self.metrics['recommendations']
        }

class SystemHealthChecker:
    """Check system-level health indicators"""
    
    def __init__(self):
        self.last_check_time = 0
        self.check_interval = 300  # 5 minutes
        
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        current_time = time.time()
        
        # Only run full system check every 5 minutes
        if current_time - self.last_check_time < self.check_interval:
            return {'skipped': True, 'reason': 'Check interval not reached'}
        
        self.last_check_time = current_time
        
        health_info = {
            'timestamp': datetime.now().isoformat(),
            'bluetooth': await self._check_bluetooth_health(),
            'system_resources': self._check_system_resources(),
            'home_assistant': await self._check_home_assistant_health(),
            'blupow_integration': await self._check_blupow_integration(),
            'recommendations': []
        }
        
        # Generate recommendations based on findings
        health_info['recommendations'] = self._generate_recommendations(health_info)
        
        return health_info
    
    async def _check_bluetooth_health(self) -> Dict[str, Any]:
        """Check Bluetooth system health"""
        bluetooth_health = {
            'adapter_available': False,
            'scanning_works': False,
            'device_count': 0,
            'error': None
        }
        
        try:
            from bleak import BleakScanner
            
            # Quick scan test
            devices = await BleakScanner.discover(timeout=3.0)
            bluetooth_health.update({
                'adapter_available': True,
                'scanning_works': True,
                'device_count': len(devices)
            })
            
        except Exception as e:
            bluetooth_health['error'] = str(e)
            _LOGGER.warning(f"Bluetooth health check failed: {e}")
        
        return bluetooth_health
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        resources = {
            'memory_available': True,
            'load_acceptable': True,
            'disk_space_ok': True,
            'details': {}
        }
        
        try:
            # Check memory usage
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemAvailable:' in line:
                            available_kb = int(line.split()[1])
                            available_mb = available_kb / 1024
                            resources['details']['memory_available_mb'] = round(available_mb, 1)
                            resources['memory_available'] = available_mb > 100  # At least 100MB
                            break
            except:
                pass
            
            # Check load average
            try:
                load1, load5, load15 = os.getloadavg()
                resources['details']['load_average'] = {
                    '1min': round(load1, 2),
                    '5min': round(load5, 2),
                    '15min': round(load15, 2)
                }
                resources['load_acceptable'] = load5 < 4.0  # Acceptable load
            except:
                pass
            
            # Check disk space
            try:
                statvfs = os.statvfs('/')
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                free_mb = free_bytes / (1024 * 1024)
                resources['details']['disk_free_mb'] = round(free_mb, 1)
                resources['disk_space_ok'] = free_mb > 500  # At least 500MB
            except:
                pass
                
        except Exception as e:
            resources['error'] = str(e)
        
        return resources
    
    async def _check_home_assistant_health(self) -> Dict[str, Any]:
        """Check Home Assistant health indicators"""
        ha_health = {
            'api_accessible': False,
            'logs_accessible': False,
            'config_directory_writable': False,
            'details': {}
        }
        
        try:
            # Check if we can access HA config directory
            config_path = Path('/config')
            if config_path.exists():
                ha_health['config_directory_writable'] = os.access(config_path, os.W_OK)
                
                # Check for recent log files
                log_files = list(config_path.glob('home-assistant.log*'))
                if log_files:
                    ha_health['logs_accessible'] = True
                    
                    # Check for recent BluPow entries
                    try:
                        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                        with open(latest_log, 'r') as f:
                            # Read last 1000 lines
                            lines = f.readlines()[-1000:]
                            blupow_entries = [line for line in lines if 'blupow' in line.lower()]
                            ha_health['details']['recent_blupow_log_entries'] = len(blupow_entries)
                    except:
                        pass
                        
        except Exception as e:
            ha_health['error'] = str(e)
        
        return ha_health
    
    async def _check_blupow_integration(self) -> Dict[str, Any]:
        """Check BluPow integration specific health"""
        integration_health = {
            'files_present': False,
            'configuration_valid': False,
            'dependencies_available': False,
            'details': {}
        }
        
        try:
            # Check if integration files are present
            integration_path = Path('/config/custom_components/blupow')
            if integration_path.exists():
                integration_health['files_present'] = True
                
                # Check for key files
                key_files = ['__init__.py', 'manifest.json', 'coordinator.py', 'sensor.py']
                present_files = []
                for file in key_files:
                    if (integration_path / file).exists():
                        present_files.append(file)
                
                integration_health['details']['present_files'] = present_files
                integration_health['configuration_valid'] = len(present_files) >= 3
            
            # Check dependencies
            try:
                import bleak
                integration_health['dependencies_available'] = True
                integration_health['details']['bleak_version'] = getattr(bleak, '__version__', 'unknown')
            except ImportError:
                integration_health['dependencies_available'] = False
                
        except Exception as e:
            integration_health['error'] = str(e)
        
        return integration_health
    
    def _generate_recommendations(self, health_info: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on health check results"""
        recommendations = []
        
        # Bluetooth recommendations
        if not health_info['bluetooth']['adapter_available']:
            recommendations.append("🔵 Bluetooth adapter not available - check if Bluetooth is enabled and accessible")
        elif not health_info['bluetooth']['scanning_works']:
            recommendations.append("🔵 Bluetooth scanning failed - try restarting Bluetooth service")
        elif health_info['bluetooth']['device_count'] == 0:
            recommendations.append("🔵 No Bluetooth devices found - check if devices are nearby and discoverable")
        
        # Resource recommendations
        resources = health_info['system_resources']
        if not resources['memory_available']:
            recommendations.append("💾 Low memory detected - consider closing other applications")
        if not resources['load_acceptable']:
            recommendations.append("⚡ High system load - performance may be degraded")
        if not resources['disk_space_ok']:
            recommendations.append("💽 Low disk space - consider cleaning up old files")
        
        # Home Assistant recommendations
        ha_health = health_info['home_assistant']
        if not ha_health['config_directory_writable']:
            recommendations.append("📁 Home Assistant config directory not writable - check permissions")
        if not ha_health['logs_accessible']:
            recommendations.append("📋 Cannot access Home Assistant logs - check file permissions")
        
        # Integration recommendations
        integration = health_info['blupow_integration']
        if not integration['files_present']:
            recommendations.append("📦 BluPow integration files not found - reinstall integration")
        if not integration['dependencies_available']:
            recommendations.append("🔗 BluPow dependencies missing - install required packages")
        
        return recommendations

class BluPowHealthMonitor:
    """Main health monitoring coordinator"""
    
    def __init__(self, mac_address: str = None):
        self.mac_address = mac_address
        self.metrics = HealthMetrics()
        self.system_checker = SystemHealthChecker()
        self.running = False
        self.check_interval = 60  # Check every minute
        self.last_report_time = 0
        self.report_interval = 300  # Report every 5 minutes
        
    async def start_monitoring(self, duration_minutes: int = None):
        """Start continuous health monitoring"""
        _LOGGER.info(f"🏥 Starting BluPow health monitoring (MAC: {self.mac_address or 'Auto-detect'})")
        
        if duration_minutes:
            _LOGGER.info(f"⏱️ Monitoring duration: {duration_minutes} minutes")
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running:
                # Perform health check
                await self._perform_health_check()
                
                # System health check (less frequent)
                system_health = await self.system_checker.check_system_health()
                if not system_health.get('skipped', False):
                    self._analyze_system_health(system_health)
                
                # Periodic reporting
                await self._report_if_needed()
                
                # Check if duration limit reached
                if duration_minutes and (time.time() - start_time) >= duration_minutes * 60:
                    _LOGGER.info(f"⏰ Monitoring duration limit reached ({duration_minutes} minutes)")
                    break
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            _LOGGER.info("👋 Monitoring interrupted by user")
        except Exception as e:
            _LOGGER.error(f"💥 Monitoring error: {e}")
            _LOGGER.debug(traceback.format_exc())
        finally:
            self.running = False
            await self._generate_final_report()
    
    async def _perform_health_check(self):
        """Perform a single health check"""
        start_time = time.time()
        
        try:
            # Try to perform a connection test
            success = await self._test_connection()
            response_time = time.time() - start_time
            
            self.metrics.record_check(success, response_time)
            
            if success:
                _LOGGER.debug(f"✅ Health check passed in {response_time:.2f}s")
            else:
                _LOGGER.warning(f"❌ Health check failed after {response_time:.2f}s")
                
        except Exception as e:
            response_time = time.time() - start_time
            error_type = type(e).__name__
            self.metrics.record_check(False, response_time, error_type)
            _LOGGER.error(f"💥 Health check exception: {e}")
    
    async def _test_connection(self) -> bool:
        """Test connection to BluPow device"""
        if not self.mac_address:
            # Auto-detect device
            self.mac_address = await self._auto_detect_device()
            if not self.mac_address:
                return False
        
        try:
            # Quick connection test
            test_script = f'''
import asyncio
import sys
sys.path.append("/config/custom_components")

async def quick_test():
    try:
        from blupow.blupow_client import BluPowClient
        client = BluPowClient("{self.mac_address}")
        connected = await client.connect()
        if connected:
            await client.disconnect()
            return True
        return False
    except Exception:
        return False

result = asyncio.run(quick_test())
sys.exit(0 if result else 1)
'''
            
            process = await asyncio.create_subprocess_exec(
                'python3', '-c', test_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                await asyncio.wait_for(process.communicate(), timeout=15.0)
                return process.returncode == 0
            except asyncio.TimeoutError:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
                return False
                
        except Exception as e:
            _LOGGER.debug(f"Connection test failed: {e}")
            return False
    
    async def _auto_detect_device(self) -> Optional[str]:
        """Auto-detect BluPow device"""
        try:
            from bleak import BleakScanner
            devices = await BleakScanner.discover(timeout=5.0)
            
            for device in devices:
                name = device.name or ""
                if any(keyword in name.lower() for keyword in ['bt-th', 'blupow', 'renogy', 'btric']):
                    _LOGGER.info(f"🔍 Auto-detected potential BluPow device: {device.address} ({name})")
                    return device.address
            
            return None
        except Exception:
            return None
    
    def _analyze_system_health(self, system_health: Dict[str, Any]):
        """Analyze system health and update metrics"""
        issues = []
        
        # Check Bluetooth health
        if not system_health['bluetooth']['adapter_available']:
            issues.append('bluetooth_adapter_unavailable')
        elif not system_health['bluetooth']['scanning_works']:
            issues.append('bluetooth_scanning_failed')
        
        # Check resources
        resources = system_health['system_resources']
        if not resources['memory_available']:
            issues.append('low_memory')
        if not resources['load_acceptable']:
            issues.append('high_system_load')
        
        # Update metrics
        self.metrics.metrics['system_issues'] = issues
        self.metrics.metrics['recommendations'] = system_health['recommendations']
    
    async def _report_if_needed(self):
        """Generate periodic health reports"""
        current_time = time.time()
        
        if current_time - self.last_report_time >= self.report_interval:
            await self._generate_health_report()
            self.last_report_time = current_time
    
    async def _generate_health_report(self):
        """Generate and log health report"""
        summary = self.metrics.get_summary()
        
        _LOGGER.info(
            f"📊 BluPow Health Report: {summary['health_status']} "
            f"(Score: {summary['health_score']}/100, "
            f"Success Rate: {summary['success_rate']}%, "
            f"Consecutive Failures: {summary['consecutive_failures']})"
        )
        
        if summary['error_patterns']:
            _LOGGER.warning(f"🚨 Error Patterns: {summary['error_patterns']}")
        
        if summary['recommendations']:
            _LOGGER.info("💡 Recommendations:")
            for rec in summary['recommendations']:
                _LOGGER.info(f"   {rec}")
        
        # Save detailed report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'mac_address': self.mac_address,
            'health_summary': summary,
            'uptime_hours': summary['uptime_hours']
        }
        
        try:
            with open('blupow_health_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
        except Exception as e:
            _LOGGER.warning(f"Failed to save health report: {e}")
    
    async def _generate_final_report(self):
        """Generate final comprehensive report"""
        _LOGGER.info("📋 Generating final BluPow health report...")
        
        summary = self.metrics.get_summary()
        
        print("\n" + "="*60)
        print("🏥 BLUPOW HEALTH MONITORING FINAL REPORT")
        print("="*60)
        print(f"📊 Overall Health: {summary['health_status']}")
        print(f"🎯 Health Score: {summary['health_score']}/100")
        print(f"⏱️ Monitoring Duration: {summary['uptime_hours']} hours")
        print(f"✅ Success Rate: {summary['success_rate']}%")
        print(f"🔄 Total Checks: {summary['total_checks']}")
        print(f"❌ Consecutive Failures: {summary['consecutive_failures']}")
        print(f"⚡ Avg Response Time: {summary['average_response_time']}s")
        
        if summary['error_patterns']:
            print(f"\n🚨 Error Patterns:")
            for error_type, count in summary['error_patterns'].items():
                print(f"   {error_type}: {count} occurrences")
        
        if summary['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"   {rec}")
        
        print("="*60)

async def main():
    """Main entry point for health monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BluPow Health Monitor")
    parser.add_argument('--mac', help='MAC address of BluPow device')
    parser.add_argument('--duration', type=int, help='Monitoring duration in minutes')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    monitor = BluPowHealthMonitor(args.mac)
    monitor.check_interval = args.interval
    
    try:
        await monitor.start_monitoring(args.duration)
    except KeyboardInterrupt:
        print("\n👋 Health monitoring stopped by user")
    except Exception as e:
        print(f"💥 Health monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 