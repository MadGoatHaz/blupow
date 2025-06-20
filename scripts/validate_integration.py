#!/usr/bin/env python3
"""
BluPow Integration Validation Script

Comprehensive end-to-end validation of the BluPow integration to ensure
everything is working correctly before deployment to Home Assistant.
"""

import asyncio
import logging
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

class IntegrationValidator:
    """Comprehensive integration validation"""
    
    def __init__(self):
        self.test_results = {}
        self.validation_start = time.time()
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete integration validation"""
        _LOGGER.info("🚀 Starting BluPow Integration Validation")
        _LOGGER.info("=" * 60)
        
        validation_steps = [
            ("Component Import Validation", self.validate_imports),
            ("Configuration Validation", self.validate_configuration),
            ("Client Functionality Test", self.validate_client),
            ("Coordinator Structure Test", self.validate_coordinator),
            ("Sensor Definitions Test", self.validate_sensors),
            ("Error Handling Test", self.validate_error_handling),
            ("Health Monitoring Test", self.validate_health_monitoring),
            ("Data Processing Test", self.validate_data_processing),
            ("Integration Simulation", self.simulate_integration),
        ]
        
        all_passed = True
        
        for step_name, step_func in validation_steps:
            _LOGGER.info(f"\n🔍 {step_name}")
            _LOGGER.info("-" * 40)
            
            try:
                result = await step_func()
                self.test_results[step_name] = result
                
                if result['success']:
                    _LOGGER.info(f"✅ {step_name}: PASSED")
                    if 'details' in result:
                        for key, value in result['details'].items():
                            _LOGGER.info(f"   {key}: {value}")
                else:
                    _LOGGER.error(f"❌ {step_name}: FAILED")
                    if 'error' in result:
                        _LOGGER.error(f"   Error: {result['error']}")
                    all_passed = False
                    
            except Exception as e:
                _LOGGER.error(f"💥 {step_name}: EXCEPTION - {str(e)}")
                self.test_results[step_name] = {
                    'success': False,
                    'error': f"Exception: {str(e)}"
                }
                all_passed = False
        
        return self._generate_validation_report(all_passed)
    
    async def validate_imports(self) -> Dict[str, Any]:
        """Validate all component imports work correctly"""
        import_tests = {}
        
        # Test individual components
        components = {
            'blupow_client': 'BluPowClient',
            'coordinator': 'BluPowDataUpdateCoordinator', 
            'sensor': 'BluPowSensor',
            'const': 'DEVICE_SENSORS'
        }
        
        for module_name, class_name in components.items():
            try:
                # Mock Home Assistant modules for testing
                self._setup_ha_mocks()
                
                module = __import__(module_name)
                if hasattr(module, class_name):
                    import_tests[f"{module_name}.{class_name}"] = True
                else:
                    import_tests[f"{module_name}.{class_name}"] = False
                    
            except Exception as e:
                import_tests[f"{module_name}.{class_name}"] = False
                _LOGGER.warning(f"Import failed for {module_name}: {e}")
        
        success = all(import_tests.values())
        
        return {
            'success': success,
            'details': import_tests,
            'summary': f"{sum(import_tests.values())}/{len(import_tests)} imports successful"
        }
    
    def _setup_ha_mocks(self):
        """Setup minimal Home Assistant mocks for testing"""
        import sys
        
        # Mock classes
        class MockSensorDeviceClass:
            VOLTAGE = 'voltage'
            CURRENT = 'current'
            POWER = 'power'
            BATTERY = 'battery'
            TEMPERATURE = 'temperature'
            FREQUENCY = 'frequency'
        
        class MockSensorStateClass:
            MEASUREMENT = 'measurement'
        
        class MockUnits:
            VOLT = 'V'
            AMPERE = 'A'
            WATT = 'W'
            CELSIUS = '°C'
            HERTZ = 'Hz'
        
        # Mock modules
        mock_modules = {
            'homeassistant': type('MockModule', (), {}),
            'homeassistant.core': type('MockModule', (), {'HomeAssistant': type('MockHA', (), {})}),
            'homeassistant.components': type('MockModule', (), {}),
            'homeassistant.components.sensor': type('MockModule', (), {
                'SensorDeviceClass': MockSensorDeviceClass,
                'SensorEntityDescription': type('MockSensorEntityDescription', (), {}),
                'SensorStateClass': MockSensorStateClass,
                'SensorEntity': type('MockSensorEntity', (), {})
            }),
            'homeassistant.const': type('MockModule', (), {
                'PERCENTAGE': '%',
                'UnitOfElectricCurrent': MockUnits,
                'UnitOfElectricPotential': MockUnits,
                'UnitOfPower': MockUnits,
                'UnitOfTemperature': MockUnits,
                'UnitOfFrequency': MockUnits,
                'CONF_ADDRESS': 'address'
            }),
            'homeassistant.config_entries': type('MockModule', (), {
                'ConfigEntry': type('MockConfigEntry', (), {})
            }),
            'homeassistant.helpers': type('MockModule', (), {}),
            'homeassistant.helpers.entity': type('MockModule', (), {
                'DeviceInfo': type('MockDeviceInfo', (), {})
            }),
            'homeassistant.helpers.entity_platform': type('MockModule', (), {
                'AddEntitiesCallback': type('MockAddEntitiesCallback', (), {})
            }),
            'homeassistant.helpers.update_coordinator': type('MockModule', (), {
                'DataUpdateCoordinator': type('MockDataUpdateCoordinator', (), {}),
                'CoordinatorEntity': type('MockCoordinatorEntity', (), {}),
                'UpdateFailed': Exception
            }),
            'homeassistant.components.bluetooth': type('MockModule', (), {
                'async_ble_device_from_address': lambda hass, mac, connectable=True: None
            })
        }
        
        for name, module in mock_modules.items():
            sys.modules[name] = module
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration files and structure"""
        config_tests = {}
        
        # Check manifest.json
        try:
            with open('manifest.json', 'r') as f:
                manifest = json.load(f)
            
            required_fields = ['domain', 'name', 'version', 'dependencies', 'requirements']
            config_tests['manifest_complete'] = all(field in manifest for field in required_fields)
            config_tests['has_bluetooth_dependency'] = 'bluetooth' in manifest.get('dependencies', [])
            config_tests['has_bleak_requirement'] = any('bleak' in req for req in manifest.get('requirements', []))
            
        except Exception as e:
            config_tests['manifest_error'] = str(e)
        
        # Check required files
        required_files = ['__init__.py', 'const.py', 'blupow_client.py', 'coordinator.py', 'sensor.py']
        config_tests['all_files_present'] = all(Path(f).exists() for f in required_files)
        
        success = all(test for test in config_tests.values() if isinstance(test, bool))
        
        return {
            'success': success,
            'details': config_tests
        }
    
    async def validate_client(self) -> Dict[str, Any]:
        """Validate BluPow client functionality"""
        try:
            from blupow_client import BluPowClient, ConnectionHealth
            
            # Create client instance
            client = BluPowClient("D8:B6:73:BF:4F:75")
            
            client_tests = {
                'client_created': True,
                'has_mac_address': client.mac_address == "D8:B6:73:BF:4F:75",
                'has_health_tracking': hasattr(client, 'health'),
                'has_environment_info': hasattr(client, 'environment'),
                'has_connect_method': hasattr(client, 'connect'),
                'has_disconnect_method': hasattr(client, 'disconnect'),
                'has_read_device_info': hasattr(client, 'read_device_info'),
                'has_get_data_method': hasattr(client, 'get_data'),
                'has_get_test_data_method': hasattr(client, 'get_test_data')
            }
            
            # Test data methods
            offline_data = client.get_data()
            test_data = client.get_test_data()
            
            client_tests['offline_data_valid'] = isinstance(offline_data, dict) and len(offline_data) > 0
            client_tests['test_data_valid'] = isinstance(test_data, dict) and len(test_data) > 0
            
            # Test health tracking
            if hasattr(client, 'health'):
                health = client.health
                health.record_connection_attempt(True, 2.5)
                client_tests['health_tracking_works'] = health.total_attempts == 1
            
            success = all(client_tests.values())
            
            return {
                'success': success,
                'details': client_tests,
                'offline_data_keys': len(offline_data) if 'offline_data' in locals() else 0,
                'test_data_keys': len(test_data) if 'test_data' in locals() else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_coordinator(self) -> Dict[str, Any]:
        """Validate coordinator functionality"""
        try:
            from coordinator import BluPowDataUpdateCoordinator, CoordinatorHealthMonitor
            
            # Test health monitor
            health_monitor = CoordinatorHealthMonitor()
            health_monitor.record_update_attempt(True, 2.0)
            health_monitor.record_update_attempt(False, 5.0, "timeout")
            
            coordinator_tests = {
                'health_monitor_created': True,
                'tracks_attempts': health_monitor.update_attempts == 2,
                'tracks_successes': health_monitor.successful_updates == 1,
                'tracks_failures': health_monitor.failed_updates == 1,
                'calculates_success_rate': health_monitor.success_rate == 50.0,
                'has_diagnostics': 'total_attempts' in health_monitor.get_diagnostics()
            }
            
            success = all(coordinator_tests.values())
            
            return {
                'success': success,
                'details': coordinator_tests,
                'health_score': health_monitor.get_diagnostics().get('success_rate', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_sensors(self) -> Dict[str, Any]:
        """Validate sensor definitions"""
        try:
            from const import DEVICE_SENSORS
            
            sensor_tests = {
                'sensors_defined': len(DEVICE_SENSORS) > 0,
                'all_have_keys': all(hasattr(sensor, 'key') for sensor in DEVICE_SENSORS),
                'all_have_names': all(hasattr(sensor, 'name') for sensor in DEVICE_SENSORS),
                'no_duplicate_keys': len(set(sensor.key for sensor in DEVICE_SENSORS)) == len(DEVICE_SENSORS)
            }
            
            # Check for unit/device class consistency
            unit_issues = []
            for sensor in DEVICE_SENSORS:
                if hasattr(sensor, 'device_class') and hasattr(sensor, 'native_unit_of_measurement'):
                    device_class = getattr(sensor, 'device_class', None)
                    unit = getattr(sensor, 'native_unit_of_measurement', None)
                    
                    # Check for known problematic combinations
                    if (device_class == 'power' and unit in ['A', 'V', '%', '°C']) or \
                       (device_class == 'current' and unit != 'A') or \
                       (device_class == 'voltage' and unit != 'V'):
                        unit_issues.append(f"{sensor.key}: {device_class}/{unit}")
            
            sensor_tests['no_unit_issues'] = len(unit_issues) == 0
            
            success = all(sensor_tests.values())
            
            return {
                'success': success,
                'details': sensor_tests,
                'sensor_count': len(DEVICE_SENSORS),
                'unit_issues': unit_issues
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling and recovery"""
        try:
            from blupow_client import BluPowClient
            
            client = BluPowClient("00:00:00:00:00:00")  # Invalid MAC
            
            error_tests = {
                'handles_invalid_mac': True,  # Should not crash
                'returns_offline_data': isinstance(client.get_data(), dict),
                'has_fallback_data': len(client.get_data()) > 0
            }
            
            # Test health tracking with errors
            if hasattr(client, 'health'):
                health = client.health
                health.record_connection_attempt(False, 10.0, "connection_failed")
                error_tests['tracks_failures'] = health.failed_connections > 0
                error_tests['calculates_health'] = hasattr(health, 'is_healthy')
            
            success = all(error_tests.values())
            
            return {
                'success': success,
                'details': error_tests
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_health_monitoring(self) -> Dict[str, Any]:
        """Validate health monitoring system"""
        try:
            from coordinator import CoordinatorHealthMonitor
            from blupow_client import ConnectionHealth
            
            # Test coordinator health
            coord_health = CoordinatorHealthMonitor()
            coord_health.record_update_attempt(True, 2.0)
            coord_health.record_update_attempt(False, 8.0, "timeout")
            coord_health.record_update_attempt(True, 3.0)
            
            # Test client health
            client_health = ConnectionHealth()
            client_health.record_connection_attempt(True, 1.5)
            client_health.record_data_retrieval(True)
            client_health.record_connection_attempt(False, 15.0, "BleakError")
            
            health_tests = {
                'coordinator_health_works': coord_health.update_attempts == 3,
                'coordinator_calculates_rate': coord_health.success_rate > 0,
                'coordinator_has_diagnostics': 'is_healthy' in coord_health.get_diagnostics(),
                'client_health_works': client_health.total_attempts == 2,
                'client_tracks_data': client_health.data_retrieval_success == 1,
                'client_has_health_report': 'success_rate' in client_health.get_health_report()
            }
            
            success = all(health_tests.values())
            
            return {
                'success': success,
                'details': health_tests,
                'coordinator_health': coord_health.success_rate,
                'client_health': client_health.success_rate
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_data_processing(self) -> Dict[str, Any]:
        """Validate data processing and sensor value handling"""
        try:
            from blupow_client import BluPowClient
            
            client = BluPowClient("D8:B6:73:BF:4F:75")
            
            # Test different data scenarios
            test_data = client.get_test_data()
            offline_data = client.get_data()
            
            data_tests = {
                'test_data_has_values': any(v is not None for v in test_data.values()),
                'test_data_has_model': 'model' in test_data,
                'test_data_has_voltages': any('voltage' in k for k in test_data.keys()),
                'test_data_has_currents': any('current' in k for k in test_data.keys()),
                'offline_data_structure': isinstance(offline_data, dict),
                'offline_data_has_status': 'connection_status' in offline_data
            }
            
            # Validate test data values are reasonable
            if 'battery_voltage' in test_data:
                voltage = test_data['battery_voltage']
                data_tests['reasonable_voltage'] = 10 <= voltage <= 20 if voltage else True
            
            if 'battery_percentage' in test_data:
                percentage = test_data['battery_percentage']
                data_tests['reasonable_percentage'] = 0 <= percentage <= 100 if percentage else True
            
            success = all(data_tests.values())
            
            return {
                'success': success,
                'details': data_tests,
                'test_data_fields': len(test_data),
                'offline_data_fields': len(offline_data)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def simulate_integration(self) -> Dict[str, Any]:
        """Simulate integration lifecycle"""
        try:
            from blupow_client import BluPowClient
            from coordinator import CoordinatorHealthMonitor
            
            # Simulate integration startup
            client = BluPowClient("D8:B6:73:BF:4F:75")
            health_monitor = CoordinatorHealthMonitor()
            
            simulation_tests = {}
            
            # Simulate multiple update cycles
            for cycle in range(5):
                # Simulate update attempt
                success = cycle % 3 != 2  # Fail every 3rd attempt
                response_time = 2.0 + (cycle * 0.5)  # Gradually slower
                
                health_monitor.record_update_attempt(success, response_time, 
                                                   None if success else "timeout")
                
                # Get data based on success/failure
                if success:
                    data = client.get_test_data()
                else:
                    data = client.get_data()  # Offline data
                
                simulation_tests[f'cycle_{cycle}_data'] = isinstance(data, dict) and len(data) > 0
            
            # Check final health state
            final_diagnostics = health_monitor.get_diagnostics()
            simulation_tests['maintains_health_tracking'] = final_diagnostics['total_attempts'] == 5
            simulation_tests['calculates_success_rate'] = final_diagnostics['success_rate'] > 0
            simulation_tests['detects_degradation'] = final_diagnostics['average_update_time'] > 2.0
            
            success = all(simulation_tests.values())
            
            return {
                'success': success,
                'details': simulation_tests,
                'final_success_rate': final_diagnostics['success_rate'],
                'final_health_status': final_diagnostics['is_healthy']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_validation_report(self, all_passed: bool) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        failed_tests = total_tests - passed_tests
        
        validation_duration = time.time() - self.validation_start
        
        report = {
            'validation_summary': {
                'overall_success': all_passed,
                'total_test_categories': total_tests,
                'passed_categories': passed_tests,
                'failed_categories': failed_tests,
                'success_rate': round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0,
                'validation_duration': round(validation_duration, 2)
            },
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'integration_status': 'READY' if all_passed else 'NEEDS_ATTENTION',
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if not result.get('success', False):
                if 'Import' in test_name:
                    recommendations.append("🔧 Fix component import issues")
                elif 'Configuration' in test_name:
                    recommendations.append("⚙️ Verify configuration files and structure")
                elif 'Client' in test_name:
                    recommendations.append("📡 Fix BluPow client functionality")
                elif 'Coordinator' in test_name:
                    recommendations.append("🔄 Fix coordinator and health monitoring")
                elif 'Sensor' in test_name:
                    recommendations.append("📊 Fix sensor definitions and units")
                elif 'Error Handling' in test_name:
                    recommendations.append("🛡️ Improve error handling and recovery")
                elif 'Health Monitoring' in test_name:
                    recommendations.append("📈 Fix health monitoring system")
        
        if not recommendations:
            recommendations.append("✅ Integration validation passed - ready for deployment!")
        
        return recommendations

async def main():
    """Main validation execution"""
    print("🔍 BluPow Integration Validation")
    print("=" * 60)
    
    validator = IntegrationValidator()
    
    try:
        report = await validator.run_full_validation()
        
        # Print summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 60)
        summary = report['validation_summary']
        print(f"Overall Status: {'✅ PASSED' if summary['overall_success'] else '❌ FAILED'}")
        print(f"Test Categories: {summary['passed_categories']}/{summary['total_test_categories']} passed")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Duration: {summary['validation_duration']}s")
        print(f"Integration Status: {report['integration_status']}")
        
        # Print recommendations
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS")
            print("=" * 60)
            for rec in report['recommendations']:
                print(f"  {rec}")
        
        # Save detailed report
        with open('integration_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: integration_validation_report.json")
        
        return 0 if summary['overall_success'] else 1
        
    except Exception as e:
        print(f"💥 Validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 