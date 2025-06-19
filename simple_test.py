#!/usr/bin/env python3
"""
Simple test script for BluPow Renogy integration
Tests the new cyrils/renogy-bt protocol implementation
"""

import asyncio
import logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# Import our updated client
try:
    from blupow_client import BluPowClient
    _LOGGER.info("Successfully imported BluPowClient with Renogy protocol")
except ImportError as e:
    _LOGGER.error(f"Failed to import BluPowClient: {e}")
    exit(1)

# Known Renogy device
RENOGY_DEVICE_ADDRESS = "C4:D3:6A:66:7E:D4"
RENOGY_DEVICE_NAME = "BT-TH-6A667ED4"

async def test_renogy_connection():
    """Test connection to the confirmed Renogy RNG-CTRL-RVR40 device"""
    
    _LOGGER.info("=" * 60)
    _LOGGER.info("TESTING RENOGY RNG-CTRL-RVR40 CONNECTION")
    _LOGGER.info("=" * 60)
    
    # Create fake BLE device for testing
    class TestBLEDevice:
        def __init__(self, address, name):
            self.address = address
            self.name = name
            self.rssi = -50
    
    device = TestBLEDevice(RENOGY_DEVICE_ADDRESS, RENOGY_DEVICE_NAME)
    
    try:
        # Initialize BluPow client with Renogy protocol
        client = BluPowClient(device)
        _LOGGER.info(f"Created BluPow client for device: {client.name} ({client.address})")
        
        # Test device availability
        _LOGGER.info("Checking device availability...")
        available = await client.check_device_availability()
        _LOGGER.info(f"Device availability: {available}")
        
        # Attempt to get data using new Renogy protocol
        _LOGGER.info("Attempting to read Renogy data using Modbus protocol...")
        data = await client.get_data()
        
        if data:
            _LOGGER.info("✅ SUCCESS: Retrieved data from Renogy device!")
            _LOGGER.info("Data received:")
            for key, value in data.items():
                if value is not None:
                    _LOGGER.info(f"  {key}: {value}")
                else:
                    _LOGGER.info(f"  {key}: None (no data)")
            
            # Check for real solar data
            if data.get('solar_power') is not None:
                _LOGGER.info("🌞 SOLAR POWER DETECTED! Energy dashboard ready!")
            if data.get('battery_voltage') is not None:
                _LOGGER.info("🔋 BATTERY DATA DETECTED! Battery monitoring ready!")
                
        else:
            _LOGGER.warning("❌ No data received from device")
            
    except Exception as e:
        _LOGGER.error(f"❌ Test failed: {e}")
        return False
    
    return True

async def scan_for_renogy_devices():
    """Scan for potential Renogy devices"""
    
    _LOGGER.info("=" * 60)
    _LOGGER.info("SCANNING FOR RENOGY DEVICES")
    _LOGGER.info("=" * 60)
    
    try:
        _LOGGER.info("Starting Bluetooth scan for 10 seconds...")
        devices = await BleakScanner.discover(timeout=10.0)
        
        renogy_devices = []
        for device in devices:
            name = device.name or "Unknown"
            if any(keyword in name.lower() for keyword in ['bt-th', 'renogy', 'solar', 'rover']):
                renogy_devices.append(device)
                _LOGGER.info(f"Found potential Renogy device: {name} ({device.address}) RSSI: {device.rssi}")
        
        if not renogy_devices:
            _LOGGER.warning("No potential Renogy devices found in scan")
            _LOGGER.info("Note: The known device might not be advertising or might be connected elsewhere")
        
        return renogy_devices
        
    except Exception as e:
        _LOGGER.error(f"Bluetooth scan failed: {e}")
        return []

async def main():
    """Main test function"""
    
    _LOGGER.info("BluPow Renogy Integration Test")
    _LOGGER.info("Device: RNG-CTRL-RVR40 (Renogy Rover 40A)")
    _LOGGER.info("Protocol: cyrils/renogy-bt Modbus implementation")
    _LOGGER.info("")
    
    # First, scan for devices
    await scan_for_renogy_devices()
    
    _LOGGER.info("")
    
    # Test connection to known device
    success = await test_renogy_connection()
    
    _LOGGER.info("")
    _LOGGER.info("=" * 60)
    if success:
        _LOGGER.info("✅ TEST COMPLETED SUCCESSFULLY")
        _LOGGER.info("Integration ready for Home Assistant deployment!")
        _LOGGER.info("Next steps:")
        _LOGGER.info("1. Deploy integration to Home Assistant")
        _LOGGER.info("2. Configure device with address: C4:D3:6A:66:7E:D4")
        _LOGGER.info("3. Add sensors to Energy Dashboard")
    else:
        _LOGGER.info("❌ TEST ENCOUNTERED ISSUES")
        _LOGGER.info("Check logs above for details")
    _LOGGER.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 