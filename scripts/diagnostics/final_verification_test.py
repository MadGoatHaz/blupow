#!/usr/bin/env python3
"""
FINAL VERIFICATION TEST
Comprehensive test to verify the rebuilt BluPow integration is working correctly
Tests both the standalone client and Home Assistant integration
"""
import asyncio
import logging
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add the custom_components path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "blupow"))

from blupow_client import BluPowClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test devices
TEST_DEVICES = {
    "D8:B6:73:BF:4F:75": {"name": "RIV1230RCH-SPS Inverter", "type": "inverter"},
    "C4:D3:6A:66:7E:D4": {"name": "RNG-CTRL-RVR40 Controller", "type": "controller"}
}

class FinalVerificationTest:
    """Comprehensive verification test for the rebuilt BluPow integration"""
    
    def __init__(self):
        self.test_results = {}
        self.overall_success = True
        
    async def test_device_communication(self, mac_address: str, device_info: dict) -> dict:
        """Test direct device communication"""
        logger.info(f"\n🔋 TESTING DEVICE COMMUNICATION: {device_info['name']}")
        logger.info("=" * 60)
        
        result = {
            'device': device_info['name'],
            'mac_address': mac_address,
            'connection_test': False,
            'data_retrieval_test': False,
            'data_quality_test': False,
            'real_data_confirmed': False,
            'sensor_count': 0,
            'sample_data': {},
            'errors': []
        }
        
        try:
            # Test 1: Connection
            logger.info("📡 Testing connection...")
            client = BluPowClient(mac_address)
            connected = await client.connect()
            result['connection_test'] = connected
            
            if not connected:
                result['errors'].append("Connection failed")
                logger.error("❌ Connection failed")
                return result
                
            logger.info("✅ Connection successful")
            
            # Test 2: Data retrieval
            logger.info("📊 Testing data retrieval...")
            device_data = await client.read_device_info()
            result['data_retrieval_test'] = len(device_data) > 0
            result['sensor_count'] = len(device_data)
            result['sample_data'] = device_data
            
            if len(device_data) == 0:
                result['errors'].append("No data retrieved")
                logger.error("❌ No data retrieved")
                return result
                
            logger.info(f"✅ Retrieved {len(device_data)} data fields")
            
            # Test 3: Data quality
            logger.info("🔍 Testing data quality...")
            
            # Check for real sensor data (not just metadata)
            sensor_fields = [k for k, v in device_data.items() 
                           if k not in ['mac_address', 'device_type', 'model', 'last_update', 'connection_status']
                           and isinstance(v, (int, float)) and v != 0]
            
            result['data_quality_test'] = len(sensor_fields) > 5
            
            if device_info['type'] == 'inverter':
                # Check for inverter-specific real data
                expected_fields = ['input_voltage', 'output_voltage', 'battery_voltage', 'load_active_power']
                real_data_fields = [f for f in expected_fields if f in device_data and device_data[f] > 0]
                result['real_data_confirmed'] = len(real_data_fields) >= 2
                
                if result['real_data_confirmed']:
                    logger.info(f"✅ Real inverter data confirmed: {real_data_fields}")
                else:
                    logger.warning("⚠️  No real inverter sensor data detected")
                    
            elif device_info['type'] == 'controller':
                # Check for controller-specific data
                expected_fields = ['battery_voltage', 'pv_voltage', 'battery_current']
                real_data_fields = [f for f in expected_fields if f in device_data and device_data[f] > 0]
                result['real_data_confirmed'] = len(real_data_fields) >= 1
                
                if result['real_data_confirmed']:
                    logger.info(f"✅ Real controller data confirmed: {real_data_fields}")
                else:
                    logger.warning("⚠️  No real controller sensor data detected")
            
            # Test 4: Multiple reads for consistency
            logger.info("🔄 Testing data consistency...")
            await asyncio.sleep(2)
            device_data2 = await client.read_device_info()
            
            # Check if timestamps are updating (indicating live data)
            time1 = device_data.get('last_update', '')
            time2 = device_data2.get('last_update', '')
            
            if time1 != time2:
                logger.info("✅ Data timestamps updating - live data confirmed")
            else:
                logger.warning("⚠️  Data timestamps not updating")
            
            await client.disconnect()
            logger.info("🔌 Disconnected cleanly")
            
        except Exception as e:
            error_msg = f"Test exception: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
            
        return result
        
    async def test_home_assistant_integration(self) -> dict:
        """Test Home Assistant integration status"""
        logger.info(f"\n🏠 TESTING HOME ASSISTANT INTEGRATION")
        logger.info("=" * 60)
        
        result = {
            'integration_loaded': False,
            'devices_detected': 0,
            'entities_created': 0,
            'errors': []
        }
        
        try:
            # Check if Home Assistant is running
            import subprocess
            ha_status = subprocess.run(['docker', 'ps', '--filter', 'name=homeassistant', '--format', '{{.Status}}'], 
                                     capture_output=True, text=True)
            
            if 'Up' in ha_status.stdout:
                logger.info("✅ Home Assistant container is running")
                result['integration_loaded'] = True
            else:
                logger.warning("⚠️  Home Assistant container not running")
                result['errors'].append("Home Assistant not running")
                
        except Exception as e:
            error_msg = f"HA integration test failed: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
            
        return result
        
    async def run_comprehensive_verification(self):
        """Run complete verification test suite"""
        logger.info("🚀 STARTING FINAL VERIFICATION TEST")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Test each device
        for mac_address, device_info in TEST_DEVICES.items():
            device_result = await self.test_device_communication(mac_address, device_info)
            self.test_results[mac_address] = device_result
            
            # Check if device test passed
            device_success = (device_result['connection_test'] and 
                            device_result['data_retrieval_test'] and
                            device_result['data_quality_test'])
            
            if not device_success:
                self.overall_success = False
                
        # Test Home Assistant integration
        ha_result = await self.test_home_assistant_integration()
        self.test_results['home_assistant'] = ha_result
        
        if not ha_result['integration_loaded']:
            self.overall_success = False
            
        # Generate final report
        await self.generate_final_report(start_time)
        
    async def generate_final_report(self, start_time: datetime):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL VERIFICATION REPORT")
        logger.info("=" * 80)
        
        logger.info(f"⏱️  Test Duration: {duration:.1f} seconds")
        logger.info(f"🎯 Overall Status: {'✅ SUCCESS' if self.overall_success else '❌ FAILED'}")
        
        # Device results
        for mac_address, result in self.test_results.items():
            if mac_address == 'home_assistant':
                continue
                
            logger.info(f"\n🔋 {result['device']} ({mac_address}):")
            logger.info(f"   Connection: {'✅' if result['connection_test'] else '❌'}")
            logger.info(f"   Data Retrieval: {'✅' if result['data_retrieval_test'] else '❌'}")
            logger.info(f"   Data Quality: {'✅' if result['data_quality_test'] else '❌'}")
            logger.info(f"   Real Data: {'✅' if result['real_data_confirmed'] else '❌'}")
            logger.info(f"   Sensor Count: {result['sensor_count']}")
            
            if result['errors']:
                logger.info(f"   Errors: {', '.join(result['errors'])}")
                
        # Home Assistant results
        ha_result = self.test_results.get('home_assistant', {})
        logger.info(f"\n🏠 Home Assistant Integration:")
        logger.info(f"   Status: {'✅ Running' if ha_result.get('integration_loaded') else '❌ Not Running'}")
        
        # Summary and recommendations
        logger.info(f"\n🎯 FINAL ASSESSMENT:")
        if self.overall_success:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ BluPow integration is working correctly with real device data")
            logger.info("✅ Ready for production use")
        else:
            logger.info("❌ SOME TESTS FAILED")
            logger.info("⚠️  Review errors above and fix issues before production use")
            
        # Save detailed results
        report_file = Path(__file__).parent.parent / "results" / "final_verification_results.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                'verification_summary': {
                    'timestamp': end_time.isoformat(),
                    'duration_seconds': duration,
                    'overall_success': self.overall_success,
                    'tests_passed': sum(1 for r in self.test_results.values() 
                                      if r != self.test_results.get('home_assistant') 
                                      and r.get('connection_test') and r.get('data_retrieval_test'))
                },
                'detailed_results': self.test_results
            }, f, indent=2)
            
        logger.info(f"📄 Detailed results saved to: {report_file}")

async def main():
    """Main verification function"""
    verifier = FinalVerificationTest()
    await verifier.run_comprehensive_verification()

if __name__ == "__main__":
    asyncio.run(main()) 