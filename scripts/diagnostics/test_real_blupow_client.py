#!/usr/bin/env python3
"""
REAL-TIME BLUPOW CLIENT TEST
Test the new BluPow client implementation with actual devices
Verify it works before deploying to Home Assistant
"""
import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
import os
from bleak import BleakScanner

# Add the custom_components path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "blupow"))

from blupow_client import BluPowClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Use environment variables for target devices, or use a placeholder
TARGET_MACS_STR = os.environ.get("BLUPOW_TEST_MACS")

# --- Test Logic ---
async def main():
    if not TARGET_MACS_STR:
        print("❌ ERROR: Please set the BLUPOW_TEST_MACS environment variable.")
        print("   It should be a comma-separated list of MAC addresses.")
        print("   Example: export BLUPOW_TEST_MACS='AA:BB:CC:DD:EE:FF,11:22:33:44:55:66'")
        return

    target_devices = {mac.strip(): {} for mac in TARGET_MACS_STR.split(',')}
    # A simple way to assign types for testing, can be improved
    for mac in target_devices:
        target_devices[mac]['type'] = 'inverter' if len(mac) % 2 == 0 else 'controller'
        target_devices[mac]['name'] = f"Test Device {mac[-4:]}"


    print("--- Real BluPow Client Test ---")
    print(f"Testing {len(target_devices)} device(s)...")

    for mac, info in target_devices.items():
        tester = BluPowClientTester()
        await tester.test_device(mac, info)

class BluPowClientTester:
    """Comprehensive tester for the BluPow client"""
    
    def __init__(self):
        self.test_results = {}
        self.success_count = 0
        self.total_tests = 0
        
    async def test_device(self, mac_address: str, device_info: dict) -> dict:
        """Test a single device"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔋 TESTING: {device_info['name']} ({mac_address})")
        logger.info(f"{'='*60}")
        
        test_result = {
            'mac_address': mac_address,
            'device_name': device_info['name'],
            'device_type': device_info['type'],
            'timestamp': datetime.now().isoformat(),
            'connection_successful': False,
            'data_retrieved': False,
            'data_fields_count': 0,
            'data_sample': {},
            'errors': [],
            'success': False
        }
        
        try:
            # Initialize client
            logger.info(f"📱 Initializing BluPow client for {device_info['type']} device...")
            client = BluPowClient(mac_address)
            
            # Test connection
            logger.info(f"🔗 Attempting connection to {mac_address}...")
            connection_success = await client.connect()
            test_result['connection_successful'] = connection_success
            
            if not connection_success:
                test_result['errors'].append("Failed to establish connection")
                logger.error("❌ Connection failed")
                return test_result
                
            logger.info("✅ Connection successful!")
            
            # Test data retrieval
            logger.info("📊 Reading device data...")
            device_data = await client.read_device_info()
            
            if device_data and len(device_data) > 0:
                test_result['data_retrieved'] = True
                test_result['data_fields_count'] = len(device_data)
                test_result['data_sample'] = device_data
                test_result['success'] = True
                
                logger.info(f"🎉 SUCCESS! Retrieved {len(device_data)} data fields")
                logger.info("📋 Sample data fields:")
                for key, value in list(device_data.items())[:10]:  # Show first 10 fields
                    logger.info(f"   {key}: {value}")
                    
                if len(device_data) > 10:
                    logger.info(f"   ... and {len(device_data) - 10} more fields")
                    
            else:
                test_result['errors'].append("No data retrieved from device")
                logger.error("❌ No data retrieved")
                
            # Clean disconnect
            await client.disconnect()
            logger.info("🔌 Disconnected cleanly")
            
        except Exception as e:
            error_msg = f"Exception during test: {str(e)}"
            test_result['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
            
        return test_result
        
    async def run_comprehensive_test(self):
        """Run comprehensive test on all devices"""
        logger.info("🚀 STARTING COMPREHENSIVE BLUPOW CLIENT TEST")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        for mac_address, device_info in TARGET_DEVICES.items():
            self.total_tests += 1
            result = await self.test_device(mac_address, device_info)
            self.test_results[mac_address] = result
            
            if result['success']:
                self.success_count += 1
                
        # Generate comprehensive report
        await self.generate_test_report(start_time)
        
    async def generate_test_report(self, start_time: datetime):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 80)
        
        logger.info(f"⏱️  Test Duration: {duration:.1f} seconds")
        logger.info(f"📈 Success Rate: {self.success_count}/{self.total_tests} ({(self.success_count/self.total_tests*100):.1f}%)")
        
        # Device-specific results
        for mac_address, result in self.test_results.items():
            logger.info(f"\n🔋 {result['device_name']} ({mac_address}):")
            logger.info(f"   Connection: {'✅ Success' if result['connection_successful'] else '❌ Failed'}")
            logger.info(f"   Data Retrieved: {'✅ Yes' if result['data_retrieved'] else '❌ No'}")
            logger.info(f"   Data Fields: {result['data_fields_count']}")
            
            if result['errors']:
                logger.info(f"   Errors: {', '.join(result['errors'])}")
                
        # Overall assessment
        logger.info(f"\n🎯 OVERALL ASSESSMENT:")
        if self.success_count == self.total_tests:
            logger.info("🎉 ALL TESTS PASSED - Ready for Home Assistant deployment!")
        elif self.success_count > 0:
            logger.info(f"⚠️  PARTIAL SUCCESS - {self.success_count} of {self.total_tests} devices working")
        else:
            logger.info("❌ ALL TESTS FAILED - Need to investigate issues")
            
        # Save detailed results
        report_file = Path(__file__).parent.parent / "results" / "blupow_client_test_results.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                'test_summary': {
                    'timestamp': end_time.isoformat(),
                    'duration_seconds': duration,
                    'total_tests': self.total_tests,
                    'successful_tests': self.success_count,
                    'success_rate': self.success_count / self.total_tests * 100
                },
                'device_results': self.test_results
            }, f, indent=2)
            
        logger.info(f"📄 Detailed results saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main()) 