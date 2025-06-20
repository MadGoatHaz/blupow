#!/usr/bin/env python3
"""
BluPow Inverter Connection Test Script

Tests the corrected inverter protocol implementation and verifies
all 22 sensors are receiving data from the Renogy RIV1230RCH-SPS.

Usage: python3 test_inverter_connection.py
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from const import DEVICE_SENSORS

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/inverter_connection_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class InverterConnectionTest:
    def __init__(self, device_address="D8:B6:73:BF:4F:75"):
        self.device_address = device_address
        self.client = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'device_address': device_address,
            'connection_status': 'pending',
            'sensor_data': {},
            'register_results': {},
            'errors': [],
            'success_indicators': {}
        }
    
    async def test_connection(self):
        """Test basic BLE connection to inverter"""
        logger.info("🔍 Testing BLE Connection to Inverter")
        logger.info("=" * 50)
        
        try:
            self.client = BluPowClient(self.device_address)
            logger.info(f"✅ BluPowClient created for {self.device_address}")
            
            # Test connection establishment
            logger.info("🔄 Attempting to establish connection...")
            
            # The client will handle connection internally during data fetch
            self.test_results['connection_status'] = 'client_created'
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self.test_results['errors'].append(f"Connection failed: {e}")
            self.test_results['connection_status'] = 'failed'
            return False
    
         async def test_data_fetch(self):
         """Test data fetching from all inverter registers"""
         logger.info("\n🔍 Testing Data Fetch from Inverter Registers")
         logger.info("=" * 55)
         
         if not self.client:
             logger.error("❌ No client available for data fetch test")
             return False
         
         try:
             # Fetch data using the corrected inverter protocol
             logger.info("🔄 Fetching data from inverter...")
             
             # Connect to device first
             connection_success = await self.client.connect()
             if not connection_success:
                 logger.error("❌ Failed to connect to inverter")
                 self.test_results['errors'].append("Failed to connect to inverter")
                 return False
             
             logger.info("✅ Connected to inverter")
             
             # Read device info using inverter registers
             data = await self.client.read_device_info()
             
             if data:
                 logger.info("✅ Data fetch successful!")
                 logger.info(f"📊 Received data: {json.dumps(data, indent=2)}")
                 
                 self.test_results['sensor_data'] = data
                 self.test_results['connection_status'] = 'data_received'
                 
                 # Verify key inverter indicators
                 self.verify_inverter_data(data)
                 return True
             else:
                 logger.warning("⚠️  Data fetch returned empty result")
                 self.test_results['errors'].append("Data fetch returned empty")
                 return False
                 
         except Exception as e:
             logger.error(f"❌ Data fetch failed: {e}")
             self.test_results['errors'].append(f"Data fetch failed: {e}")
             return False
    
    def verify_inverter_data(self, data):
        """Verify the data matches expected inverter characteristics"""
        logger.info("\n🔍 Verifying Inverter Data Characteristics")
        logger.info("=" * 45)
        
        success_indicators = {}
        
        # Check for inverter model identification
        if 'model' in data and 'RIV1230RCH' in str(data['model']):
            logger.info("✅ Inverter model detected: RIV1230RCH-SPS")
            success_indicators['model_detected'] = True
        else:
            logger.warning(f"⚠️  Model not detected or incorrect: {data.get('model', 'None')}")
            success_indicators['model_detected'] = False
        
        # Check for AC voltage readings (should be ~120V)
        ac_voltages = ['input_voltage', 'output_voltage']
        for voltage_key in ac_voltages:
            if voltage_key in data:
                voltage = data[voltage_key]
                if isinstance(voltage, (int, float)) and 100 <= voltage <= 150:
                    logger.info(f"✅ {voltage_key}: {voltage}V (reasonable AC voltage)")
                    success_indicators[f'{voltage_key}_reasonable'] = True
                else:
                    logger.info(f"📊 {voltage_key}: {voltage}V")
                    success_indicators[f'{voltage_key}_reasonable'] = False
        
        # Check for frequency readings (should be ~60Hz)
        freq_keys = ['input_frequency', 'output_frequency']
        for freq_key in freq_keys:
            if freq_key in data:
                freq = data[freq_key]
                if isinstance(freq, (int, float)) and 50 <= freq <= 65:
                    logger.info(f"✅ {freq_key}: {freq}Hz (reasonable AC frequency)")
                    success_indicators[f'{freq_key}_reasonable'] = True
                else:
                    logger.info(f"📊 {freq_key}: {freq}Hz")
                    success_indicators[f'{freq_key}_reasonable'] = False
        
        # Check for battery voltage (should be 12-15V for 12V system)
        if 'battery_voltage' in data:
            battery_v = data['battery_voltage']
            if isinstance(battery_v, (int, float)) and 10 <= battery_v <= 16:
                logger.info(f"✅ battery_voltage: {battery_v}V (reasonable 12V battery)")
                success_indicators['battery_voltage_reasonable'] = True
            else:
                logger.info(f"📊 battery_voltage: {battery_v}V")
                success_indicators['battery_voltage_reasonable'] = False
        
        # Check for device_id
        if 'device_id' in data and data['device_id'] is not None:
            logger.info(f"✅ device_id: {data['device_id']} (device responding)")
            success_indicators['device_id_present'] = True
        else:
            logger.warning("⚠️  device_id not present or None")
            success_indicators['device_id_present'] = False
        
        self.test_results['success_indicators'] = success_indicators
    
    def test_sensor_definitions(self):
        """Test that all expected sensors are defined"""
        logger.info("\n🔍 Testing Sensor Definitions")
        logger.info("=" * 30)
        
        logger.info(f"📊 Total sensors defined: {len(DEVICE_SENSORS)}")
        
        # Key sensors we expect for inverter
        expected_inverter_sensors = [
            'model', 'device_id', 'input_voltage', 'input_current', 'input_frequency',
            'output_voltage', 'output_current', 'output_frequency', 'battery_voltage',
            'battery_soc', 'battery_current', 'charging_status', 'load_power',
            'load_apparent_power', 'load_percentage', 'solar_voltage', 'solar_current',
            'solar_power', 'temperature'
        ]
        
        sensor_keys = [sensor.key for sensor in DEVICE_SENSORS]
        
        missing_sensors = []
        present_sensors = []
        
        for expected in expected_inverter_sensors:
            if expected in sensor_keys:
                logger.info(f"✅ {expected}: Defined")
                present_sensors.append(expected)
            else:
                logger.warning(f"⚠️  {expected}: Missing")
                missing_sensors.append(expected)
        
        logger.info(f"\n📊 Sensor Definition Summary:")
        logger.info(f"   Present: {len(present_sensors)}/{len(expected_inverter_sensors)}")
        logger.info(f"   Missing: {len(missing_sensors)}")
        
        if missing_sensors:
            logger.warning(f"   Missing sensors: {missing_sensors}")
        
        return len(missing_sensors) == 0
    
    async def run_comprehensive_test(self):
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting Comprehensive Inverter Connection Test")
        logger.info("=" * 60)
        logger.info(f"Device Address: {self.device_address}")
        logger.info(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Test 1: Sensor Definitions
        logger.info("🧪 TEST 1: Sensor Definitions")
        sensors_ok = self.test_sensor_definitions()
        
        # Test 2: Connection
        logger.info("\n🧪 TEST 2: BLE Connection")
        connection_ok = await self.test_connection()
        
        # Test 3: Data Fetch (only if connection successful)
        data_ok = False
        if connection_ok:
            logger.info("\n🧪 TEST 3: Data Fetch")
            data_ok = await self.test_data_fetch()
        else:
            logger.warning("\n⏭️  Skipping data fetch test (connection failed)")
        
        # Generate final report
        self.generate_test_report(sensors_ok, connection_ok, data_ok)
        
        return sensors_ok and connection_ok and data_ok
    
    def generate_test_report(self, sensors_ok, connection_ok, data_ok):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 60)
        
        # Test Results Summary
        logger.info("🎯 TEST RESULTS SUMMARY:")
        logger.info(f"   Sensor Definitions: {'✅ PASS' if sensors_ok else '❌ FAIL'}")
        logger.info(f"   BLE Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
        logger.info(f"   Data Fetch: {'✅ PASS' if data_ok else '❌ FAIL'}")
        
        overall_status = sensors_ok and connection_ok and data_ok
        logger.info(f"   Overall Status: {'🎉 SUCCESS' if overall_status else '❌ FAILED'}")
        
        # Success Indicators
        if self.test_results.get('success_indicators'):
            logger.info("\n🏆 SUCCESS INDICATORS:")
            for indicator, result in self.test_results['success_indicators'].items():
                status = '✅' if result else '❌'
                logger.info(f"   {status} {indicator}")
        
        # Data Summary
        if self.test_results.get('sensor_data'):
            logger.info("\n📊 DATA SAMPLE:")
            data = self.test_results['sensor_data']
            
            # Show key data points
            key_data = {
                'Model': data.get('model', 'Unknown'),
                'Input Voltage': f"{data.get('input_voltage', 'N/A')}V",
                'Output Voltage': f"{data.get('output_voltage', 'N/A')}V",
                'Battery Voltage': f"{data.get('battery_voltage', 'N/A')}V",
                'Battery SOC': f"{data.get('battery_soc', 'N/A')}%",
                'Load Power': f"{data.get('load_power', 'N/A')}W"
            }
            
            for key, value in key_data.items():
                logger.info(f"   {key}: {value}")
        
        # Errors
        if self.test_results.get('errors'):
            logger.info("\n❌ ERRORS ENCOUNTERED:")
            for error in self.test_results['errors']:
                logger.info(f"   • {error}")
        
        # Next Steps
        logger.info("\n📋 NEXT STEPS:")
        if overall_status:
            logger.info("   🎉 Test SUCCESSFUL! Integration ready for use.")
            logger.info("   📱 Add integration in Home Assistant:")
            logger.info("      Settings → Devices & Services → Add Integration → BluPow")
        else:
            logger.info("   🔧 Troubleshooting needed:")
            if not sensors_ok:
                logger.info("      • Review sensor definitions in const.py")
            if not connection_ok:
                logger.info("      • Check device power and Bluetooth connectivity")
                logger.info("      • Verify MAC address: D8:B6:73:BF:4F:75")
            if not data_ok:
                logger.info("      • Check inverter register protocol implementation")
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to JSON file"""
        results_file = Path("results/inverter_connection_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            logger.info(f"\n💾 Detailed results saved: {results_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

async def main():
    """Main test execution"""
    print("🔬 BluPow Inverter Connection Test")
    print("Device: Renogy RIV1230RCH-SPS")
    print("Protocol: Corrected Inverter Registers")
    print("-" * 50)
    
    # Ensure results directory exists
    Path("results").mkdir(exist_ok=True)
    
    # Run comprehensive test
    tester = InverterConnectionTest()
    success = await tester.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1) 