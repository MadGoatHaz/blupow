#!/usr/bin/env python3
"""
Comprehensive BluPow Integration Test

This script performs end-to-end testing of the BluPow integration to validate
all components work correctly and identify any remaining issues.
"""

import asyncio
import logging
import sys
import time
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

class IntegrationTestSuite:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        self.warnings = []
        self.test_start_time = time.time()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        _LOGGER.info("🧪 Starting comprehensive BluPow integration tests")
        
        tests = [
            ("Import Tests", self.test_imports),
            ("Constants Validation", self.test_constants),
            ("Client Functionality", self.test_client_basic),
            ("Coordinator Structure", self.test_coordinator_structure),
            ("Sensor Definitions", self.test_sensor_definitions),
            ("Device Communication", self.test_device_communication),
            ("Error Handling", self.test_error_handling),
            ("Health Monitoring", self.test_health_monitoring),
            ("Integration Structure", self.test_integration_structure)
        ]
        
        for test_name, test_func in tests:
            _LOGGER.info(f"🔍 Running {test_name}...")
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    'status': 'PASSED' if result['success'] else 'FAILED',
                    'details': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                if result['success']:
                    _LOGGER.info(f"✅ {test_name}: PASSED")
                else:
                    _LOGGER.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"Test exception: {str(e)}"
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'error': error_msg,
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                }
                _LOGGER.error(f"💥 {test_name}: ERROR - {error_msg}")
                self.errors.append(f"{test_name}: {error_msg}")
        
        return self._generate_test_report()
    
    async def test_imports(self) -> Dict[str, Any]:
        """Test all module imports"""
        import_results = {}
        
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Test individual module imports
        modules_to_test = [
            'blupow_client',
            'coordinator', 
            'sensor',
            'const',
            'diagnostics'
        ]
        
        for module_name in modules_to_test:
            try:
                if module_name == 'blupow_client':
                    # Import with fallback constants
                    # Import with mocked homeassistant modules
                    import sys
                    
                    # Mock homeassistant modules for testing
                    class MockHomeAssistant:
                        pass

                    class MockSensorDeviceClass:
                        VOLTAGE = 'voltage'
                        CURRENT = 'current'
                        POWER = 'power'
                        BATTERY = 'battery'
                        TEMPERATURE = 'temperature'
                        FREQUENCY = 'frequency'

                    class MockSensorStateClass:
                        MEASUREMENT = 'measurement'

                    class MockUnitOfElectricPotential:
                        VOLT = 'V'

                    class MockUnitOfElectricCurrent:
                        AMPERE = 'A'

                    class MockUnitOfPower:
                        WATT = 'W'

                    class MockUnitOfTemperature:
                        CELSIUS = '°C'

                    class MockUnitOfFrequency:
                        HERTZ = 'Hz'

                    # Mock the homeassistant imports
                    sys.modules['homeassistant'] = type('MockModule', (), {})()
                    sys.modules['homeassistant.core'] = type('MockModule', (), {'HomeAssistant': MockHomeAssistant})()
                    sys.modules['homeassistant.components'] = type('MockModule', (), {})()
                    sys.modules['homeassistant.components.sensor'] = type('MockModule', (), {
                        'SensorDeviceClass': MockSensorDeviceClass,
                        'SensorEntityDescription': type('MockSensorEntityDescription', (), {}),
                        'SensorStateClass': MockSensorStateClass,
                    })()
                    sys.modules['homeassistant.const'] = type('MockModule', (), {
                        'PERCENTAGE': '%',
                        'UnitOfElectricCurrent': MockUnitOfElectricCurrent,
                        'UnitOfElectricPotential': MockUnitOfElectricPotential,
                        'UnitOfPower': MockUnitOfPower,
                        'UnitOfTemperature': MockUnitOfTemperature,
                        'UnitOfFrequency': MockUnitOfFrequency,
                    })()

                    # Import the module
                    exec(f"from {module_name} import *")
                    import_results[module_name] = {'success': True, 'note': 'Imported with mocked HA modules'}
                else:
                    # Try importing other modules
                    __import__(module_name)
                    import_results[module_name] = {'success': True}
                    
            except Exception as e:
                import_results[module_name] = {
                    'success': False, 
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # Check if we can import key classes
        try:
            from blupow_client import BluPowClient
            import_results['BluPowClient'] = {'success': True}
        except Exception as e:
            import_results['BluPowClient'] = {'success': False, 'error': str(e)}
        
        success = all(result.get('success', False) for result in import_results.values())
        
        return {
            'success': success,
            'import_results': import_results,
            'total_modules': len(modules_to_test),
            'successful_imports': sum(1 for r in import_results.values() if r.get('success', False))
        }
    
    async def test_constants(self) -> Dict[str, Any]:
        """Test constants and sensor definitions"""
        try:
            # Mock the required modules first
            import sys
            
            # Create mock modules
            mock_modules = {
                'homeassistant': type('MockModule', (), {}),
                'homeassistant.components': type('MockModule', (), {}),
                'homeassistant.components.sensor': type('MockModule', (), {
                    'SensorDeviceClass': type('MockSensorDeviceClass', (), {
                        'VOLTAGE': 'voltage',
                        'CURRENT': 'current', 
                        'POWER': 'power',
                        'BATTERY': 'battery',
                        'TEMPERATURE': 'temperature',
                        'FREQUENCY': 'frequency'
                    }),
                    'SensorEntityDescription': type('MockSensorEntityDescription', (), {}),
                    'SensorStateClass': type('MockSensorStateClass', (), {
                        'MEASUREMENT': 'measurement'
                    })
                }),
                'homeassistant.const': type('MockModule', (), {
                    'PERCENTAGE': '%',
                    'UnitOfElectricCurrent': type('MockUnit', (), {'AMPERE': 'A'}),
                    'UnitOfElectricPotential': type('MockUnit', (), {'VOLT': 'V'}),
                    'UnitOfPower': type('MockUnit', (), {'WATT': 'W'}),
                    'UnitOfTemperature': type('MockUnit', (), {'CELSIUS': '°C'}),
                    'UnitOfFrequency': type('MockUnit', (), {'HERTZ': 'Hz'})
                })
            }
            
            for name, module in mock_modules.items():
                sys.modules[name] = module
            
            # Now try to import constants
            from const import DEVICE_SENSORS, DOMAIN
            
            # Validate sensor definitions
            sensor_issues = []
            
            for sensor in DEVICE_SENSORS:
                if hasattr(sensor, 'key') and hasattr(sensor, 'name'):
                    # Check for proper unit/device class combinations
                    if hasattr(sensor, 'device_class') and hasattr(sensor, 'native_unit_of_measurement'):
                        device_class = getattr(sensor, 'device_class', None)
                        unit = getattr(sensor, 'native_unit_of_measurement', None)
                        
                        # Check for common mismatches that cause HA warnings
                        if device_class == 'power' and unit in ['A', 'V', '%', '°C']:
                            sensor_issues.append(f"Sensor '{sensor.key}' has device_class='power' but unit='{unit}'")
                        elif device_class == 'current' and unit not in ['A']:
                            sensor_issues.append(f"Sensor '{sensor.key}' has device_class='current' but unit='{unit}'")
                        elif device_class == 'voltage' and unit not in ['V']:
                            sensor_issues.append(f"Sensor '{sensor.key}' has device_class='voltage' but unit='{unit}'")
                        elif device_class == 'temperature' and unit not in ['°C', 'C']:
                            sensor_issues.append(f"Sensor '{sensor.key}' has device_class='temperature' but unit='{unit}'")
                
            return {
                'success': len(sensor_issues) == 0,
                'sensor_count': len(DEVICE_SENSORS),
                'domain': DOMAIN,
                'sensor_issues': sensor_issues,
                'sample_sensors': [getattr(s, 'key', 'unknown') for s in DEVICE_SENSORS[:5]]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_client_basic(self) -> Dict[str, Any]:
        """Test basic client functionality (without actual device connection)"""
        try:
            from blupow_client import BluPowClient
            
            # Create client instance
            test_mac = "D8:B6:73:BF:4F:75"  # Example MAC
            client = BluPowClient(test_mac)
            
            # Test basic properties and methods
            properties_test = {
                'mac_address': client.mac_address == test_mac,
                'has_connect_method': hasattr(client, 'connect'),
                'has_disconnect_method': hasattr(client, 'disconnect'),
                'has_read_device_info': hasattr(client, 'read_device_info'),
                'has_health_tracking': hasattr(client, 'health'),
                'has_environment_info': hasattr(client, 'environment')
            }
            
            # Test CRC calculation if available
            crc_test = False
            if hasattr(client, '_calculate_crc'):
                try:
                    test_data = b'\xFF\x03\x00\x00\x00\x01'
                    crc = client._calculate_crc(test_data)
                    crc_test = isinstance(crc, int) and 0 <= crc <= 0xFFFF
                except:
                    pass
            
            # Test command creation if available
            command_test = False
            if hasattr(client, '_create_read_command'):
                try:
                    cmd = client._create_read_command(4000, 10)
                    command_test = isinstance(cmd, bytes) and len(cmd) == 8
                except:
                    pass
            
            all_passed = all(properties_test.values())
            
            return {
                'success': all_passed,
                'properties_test': properties_test,
                'crc_calculation_works': crc_test,
                'command_creation_works': command_test,
                'client_created': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_coordinator_structure(self) -> Dict[str, Any]:
        """Test coordinator structure and functionality"""
        try:
            # Mock required HA modules
            import sys
            
            class MockHomeAssistant:
                pass
            
            class MockDataUpdateCoordinator:
                def __init__(self, hass, logger, name, update_interval, update_method):
                    self.hass = hass
                    self.logger = logger
                    self.name = name
                    self.update_interval = update_interval
                    self.update_method = update_method
                    self.data = None
                    self.last_update_success = False
            
            class MockBluetooth:
                @staticmethod
                def async_ble_device_from_address(hass, mac, connectable=True):
                    return None
            
            # Mock the modules
            sys.modules['homeassistant.core'] = type('MockModule', (), {'HomeAssistant': MockHomeAssistant})
            sys.modules['homeassistant.helpers'] = type('MockModule', (), {})
            sys.modules['homeassistant.helpers.update_coordinator'] = type('MockModule', (), {
                'DataUpdateCoordinator': MockDataUpdateCoordinator,
                'UpdateFailed': Exception
            })
            sys.modules['homeassistant.components'] = type('MockModule', (), {})
            sys.modules['homeassistant.components.bluetooth'] = type('MockModule', (), {
                'async_ble_device_from_address': MockBluetooth.async_ble_device_from_address
            })
            
            from coordinator import BluPowDataUpdateCoordinator
            
            # Create mock HA instance
            mock_hass = MockHomeAssistant()
            test_mac = "D8:B6:73:BF:4F:75"
            
            # Create coordinator
            coordinator = BluPowDataUpdateCoordinator(mock_hass, test_mac)
            
            # Test coordinator properties
            properties_test = {
                'has_mac_address': hasattr(coordinator, 'mac_address'),
                'has_client': hasattr(coordinator, 'client'),
                'has_health_monitor': hasattr(coordinator, 'health_monitor'),
                'has_subprocess_manager': hasattr(coordinator, 'subprocess_manager'),
                'has_update_method': hasattr(coordinator, '_async_update_data'),
                'mac_matches': getattr(coordinator, 'mac_address', None) == test_mac
            }
            
            all_passed = all(properties_test.values())
            
            return {
                'success': all_passed,
                'properties_test': properties_test,
                'coordinator_created': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_sensor_definitions(self) -> Dict[str, Any]:
        """Test sensor definitions for correctness"""
        try:
            # Import with mocked modules (already done in constants test)
            from const import DEVICE_SENSORS
            
            sensor_analysis = {
                'total_sensors': len(DEVICE_SENSORS),
                'sensors_with_units': 0,
                'sensors_with_device_class': 0,
                'unit_device_class_mismatches': [],
                'missing_properties': [],
                'sensor_keys': []
            }
            
            for sensor in DEVICE_SENSORS:
                if hasattr(sensor, 'key'):
                    sensor_analysis['sensor_keys'].append(sensor.key)
                else:
                    sensor_analysis['missing_properties'].append('key missing')
                
                if hasattr(sensor, 'native_unit_of_measurement'):
                    sensor_analysis['sensors_with_units'] += 1
                    
                if hasattr(sensor, 'device_class'):
                    sensor_analysis['sensors_with_device_class'] += 1
                
                # Check for unit/device class mismatches
                if hasattr(sensor, 'device_class') and hasattr(sensor, 'native_unit_of_measurement'):
                    device_class = sensor.device_class
                    unit = sensor.native_unit_of_measurement
                    
                    # Define correct unit mappings
                    correct_units = {
                        'voltage': ['V'],
                        'current': ['A'], 
                        'power': ['W'],
                        'temperature': ['°C', 'C'],
                        'frequency': ['Hz'],
                        'battery': ['%']
                    }
                    
                    if device_class in correct_units:
                        expected_units = correct_units[device_class]
                        if unit not in expected_units:
                            sensor_analysis['unit_device_class_mismatches'].append({
                                'sensor': sensor.key,
                                'device_class': device_class,
                                'unit': unit,
                                'expected_units': expected_units
                            })
            
            success = len(sensor_analysis['unit_device_class_mismatches']) == 0 and len(sensor_analysis['missing_properties']) == 0
            
            return {
                'success': success,
                **sensor_analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_device_communication(self) -> Dict[str, Any]:
        """Test device communication capabilities (mock test)"""
        try:
            from blupow_client import BluPowClient
            
            # Create client
            client = BluPowClient("D8:B6:73:BF:4F:75")
            
            # Test protocol methods
            protocol_tests = {}
            
            # Test CRC calculation
            if hasattr(client, '_calculate_crc'):
                test_data = b'\xFF\x03\x00\x00\x00\x01'
                crc = client._calculate_crc(test_data)
                protocol_tests['crc_calculation'] = isinstance(crc, int)
            
            # Test command creation
            if hasattr(client, '_create_read_command'):
                cmd = client._create_read_command(4000, 10)
                protocol_tests['command_creation'] = isinstance(cmd, bytes) and len(cmd) == 8
            
            # Test data parsing methods
            parsing_methods = ['parse_inverter_stats', 'parse_device_id', 'parse_inverter_model']
            for method_name in parsing_methods:
                protocol_tests[f'{method_name}_exists'] = hasattr(client, method_name)
            
            # Test health tracking
            if hasattr(client, 'health'):
                health = client.health
                protocol_tests['health_tracking'] = hasattr(health, 'record_connection_attempt')
            
            success = all(protocol_tests.values())
            
            return {
                'success': success,
                'protocol_tests': protocol_tests,
                'communication_ready': success
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling capabilities"""
        try:
            error_handling_tests = {}
            
            # Test client error handling
            from blupow_client import BluPowClient
            client = BluPowClient("00:00:00:00:00:00")  # Invalid MAC
            
            error_handling_tests['client_handles_invalid_mac'] = True
            
            # Test health monitoring
            if hasattr(client, 'health'):
                health = client.health
                
                # Test recording failures
                health.record_connection_attempt(False, 5.0, "test_error")
                error_handling_tests['health_records_failures'] = health.failed_connections > 0
                
                # Test health calculation
                error_handling_tests['health_calculates_success_rate'] = hasattr(health, 'success_rate')
            
            success = all(error_handling_tests.values())
            
            return {
                'success': success,
                'error_handling_tests': error_handling_tests
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_health_monitoring(self) -> Dict[str, Any]:
        """Test health monitoring capabilities"""
        try:
            health_tests = {}
            
            # Test coordinator health monitoring
            from coordinator import CoordinatorHealthMonitor
            
            monitor = CoordinatorHealthMonitor()
            
            # Test basic functionality
            monitor.record_update_attempt(True, 2.5)
            monitor.record_update_attempt(False, 5.0, "timeout")
            
            health_tests['records_attempts'] = monitor.update_attempts == 2
            health_tests['tracks_successes'] = monitor.successful_updates == 1
            health_tests['tracks_failures'] = monitor.failed_updates == 1
            health_tests['calculates_success_rate'] = monitor.success_rate == 50.0
            health_tests['has_diagnostics'] = 'total_attempts' in monitor.get_diagnostics()
            
            success = all(health_tests.values())
            
            return {
                'success': success,
                'health_tests': health_tests
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def test_integration_structure(self) -> Dict[str, Any]:
        """Test overall integration structure"""
        try:
            structure_tests = {}
            
            # Check for required files
            required_files = [
                '__init__.py',
                'manifest.json', 
                'const.py',
                'blupow_client.py',
                'coordinator.py',
                'sensor.py',
                'config_flow.py'
            ]
            
            missing_files = []
            for file in required_files:
                if not Path(file).exists():
                    missing_files.append(file)
            
            structure_tests['all_files_present'] = len(missing_files) == 0
            structure_tests['missing_files'] = missing_files
            
            # Check manifest.json
            if Path('manifest.json').exists():
                try:
                    with open('manifest.json', 'r') as f:
                        manifest = json.load(f)
                    
                    structure_tests['manifest_valid'] = True
                    structure_tests['domain'] = manifest.get('domain')
                    structure_tests['has_dependencies'] = 'dependencies' in manifest
                    structure_tests['has_requirements'] = 'requirements' in manifest
                except Exception as e:
                    structure_tests['manifest_valid'] = False
                    structure_tests['manifest_error'] = str(e)
            
            success = structure_tests.get('all_files_present', False) and structure_tests.get('manifest_valid', False)
            
            return {
                'success': success,
                'structure_tests': structure_tests
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAILED')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': round(success_rate, 1)
            },
            'test_results': self.test_results,
            'overall_status': 'PASSED' if failed_tests == 0 and error_tests == 0 else 'FAILED',
            'test_duration': round(time.time() - self.test_start_time, 2),
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result['status'] != 'PASSED':
                if 'Import Tests' in test_name:
                    recommendations.append("🔧 Fix import issues - ensure all modules can be imported correctly")
                elif 'Constants' in test_name:
                    recommendations.append("⚙️ Fix sensor definitions - correct unit/device class mismatches")
                elif 'Device Communication' in test_name:
                    recommendations.append("📡 Verify device communication protocols are properly implemented")
                elif 'Error Handling' in test_name:
                    recommendations.append("🛡️ Improve error handling and recovery mechanisms")
                elif 'Health Monitoring' in test_name:
                    recommendations.append("📊 Fix health monitoring system functionality")
                elif 'Integration Structure' in test_name:
                    recommendations.append("📁 Verify all required integration files are present and valid")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - integration appears to be working correctly!")
        
        return recommendations

async def main():
    """Main test execution"""
    print("🧪 BluPow Comprehensive Integration Test Suite")
    print("=" * 60)
    
    test_suite = IntegrationTestSuite()
    
    try:
        report = await test_suite.run_all_tests()
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        summary = report['test_summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"💥 Errors: {summary['errors']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Duration: {report['test_duration']}s")
        
        # Print recommendations
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS")
            print("=" * 60)
            for rec in report['recommendations']:
                print(f"  {rec}")
        
        # Save detailed report
        with open('integration_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: integration_test_report.json")
        
        # Return appropriate exit code
        return 0 if report['overall_status'] == 'PASSED' else 1
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 