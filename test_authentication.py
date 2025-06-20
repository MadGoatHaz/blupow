#!/usr/bin/env python3
"""
BluPow Authentication Test Script
Based on research from cyrils/renogy-bt and Renogy BT-2 protocol analysis

This script tests different authentication approaches to resolve the 
"Insufficient authorization (8)" error that's blocking data reading.
"""

import asyncio
import logging
import sys
import struct
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Renogy BT-2 Protocol Constants (from research)
SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
TX_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"  # Write to device
RX_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # Read from device (notifications)

# Alternative service found in logs
ALT_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

# Device info
DEVICE_MAC = "D8:B6:73:BF:4F:75"
DEVICE_NAME = "BTRIC134000035"

class RenogyAuthTester:
    """Test different authentication approaches for Renogy BT-2 devices"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client: BleakClient | None = None
        self.tx_char = None
        self.rx_char = None
        self.response_data = bytearray()
        self.response_received = False
        
    async def scan_for_device(self) -> bool:
        """Scan for the target device"""
        _LOGGER.info(f"Scanning for device {self.mac_address}...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            _LOGGER.debug(f"Found device: {device.name} ({device.address})")
            if device.address.upper() == self.mac_address.upper():
                _LOGGER.info(f"✅ Target device found: {device.name} ({device.address})")
                return True
                
        _LOGGER.error(f"❌ Device {self.mac_address} not found in scan")
        return False

    async def connect_and_discover(self) -> bool:
        """Connect to device and discover services"""
        try:
            _LOGGER.info(f"Connecting to {self.mac_address}...")
            self.client = BleakClient(self.mac_address)
            
            await self.client.connect()
            _LOGGER.info("✅ Connection established")
            
            # Discover services
            await self._discover_services()
            return True
            
        except Exception as e:
            _LOGGER.error(f"❌ Connection failed: {e}")
            return False

    async def _discover_services(self):
        """Comprehensive service and characteristic discovery"""
        _LOGGER.info("🔍 Discovering services and characteristics...")
        
        if not self.client:
            return
        services = await self.client.get_services()
        
        for service in services:
            _LOGGER.info(f"Service: {service.uuid}")
            
            for char in service.characteristics:
                _LOGGER.info(f"  Characteristic: {char.uuid}")
                _LOGGER.info(f"    Properties: {char.properties}")
                _LOGGER.info(f"    Handle: {char.handle}")
                
                # Look for our target characteristics
                if char.uuid.lower() == TX_CHAR_UUID.lower():
                    self.tx_char = char
                    _LOGGER.info("    ✅ Found TX characteristic (write)")
                elif char.uuid.lower() == RX_CHAR_UUID.lower():
                    self.rx_char = char
                    _LOGGER.info("    ✅ Found RX characteristic (notify)")
                
                # Check descriptors
                for desc in char.descriptors:
                    _LOGGER.info(f"      Descriptor: {desc.uuid} (handle: {desc.handle})")

    async def test_authentication_methods(self):
        """Test different authentication approaches"""
        
        # Method 1: Try to read characteristics without authentication
        await self._test_direct_access()
        
        # Method 2: Try explicit pairing
        await self._test_pairing()
        
        # Method 3: Try service-based authentication
        await self._test_service_auth()
        
        # Method 4: Try Renogy-specific handshake
        await self._test_renogy_handshake()

    async def _test_direct_access(self):
        """Test direct characteristic access"""
        _LOGGER.info("\n🧪 Test 1: Direct characteristic access")
        
        if not self.tx_char or not self.rx_char:
            _LOGGER.error("❌ Required characteristics not found")
            return
            
        try:
            if not self.client:
                return
            # Try to enable notifications
            await self.client.start_notify(self.rx_char, self._notification_handler)
            _LOGGER.info("✅ Notifications enabled successfully")
            
            # Try to write a simple command
            test_command = bytes([0xFF, 0x03, 0x01, 0x00, 0x00, 0x07, 0x10, 0x2A])
            await self.client.write_gatt_char(self.tx_char, test_command)
            _LOGGER.info("✅ Write command successful")
            
            # Wait for response
            await asyncio.sleep(2)
            
        except Exception as e:
            _LOGGER.error(f"❌ Direct access failed: {e}")

    async def _test_pairing(self):
        """Test explicit Bluetooth pairing"""
        _LOGGER.info("\n🧪 Test 2: Explicit pairing")
        
        try:
            if not self.client:
                return
            # Try to pair with the device
            await self.client.pair()
            _LOGGER.info("✅ Pairing successful")
            
            # Retry characteristic access after pairing
            await self._test_direct_access()
            
        except Exception as e:
            _LOGGER.error(f"❌ Pairing failed: {e}")

    async def _test_service_auth(self):
        """Test service-level authentication"""
        _LOGGER.info("\n🧪 Test 3: Service-level authentication")
        
        try:
            if not self.client:
                return
            # Get service and check if it requires authentication
            service = None
            services = await self.client.get_services()
            
            for svc in services:
                if svc.uuid.lower() == SERVICE_UUID.lower():
                    service = svc
                    break
                    
            if service:
                _LOGGER.info(f"Found target service: {service.uuid}")
                # Try to access service properties
                _LOGGER.info(f"Service characteristics: {len(service.characteristics)}")
            else:
                _LOGGER.error("❌ Target service not found")
                
        except Exception as e:
            _LOGGER.error(f"❌ Service authentication failed: {e}")

    async def _test_renogy_handshake(self):
        """Test Renogy-specific authentication handshake"""
        _LOGGER.info("\n🧪 Test 4: Renogy authentication handshake")
        
        if not self.tx_char or not self.rx_char:
            _LOGGER.error("❌ Required characteristics not found")
            return
            
        try:
            if not self.client:
                return
            # Based on cyrils/renogy-bt research:
            # 1. Enable notifications first
            await self.client.start_notify(self.rx_char, self._notification_handler)
            _LOGGER.info("✅ Notifications enabled")
            
            # 2. Send device info request (from research)
            # Command format: [0xFF, 0x03, start_reg_high, start_reg_low, count_high, count_low, crc_high, crc_low]
            device_info_cmd = bytes([0xFF, 0x03, 0x01, 0x00, 0x00, 0x07, 0x10, 0x2A])
            
            _LOGGER.info(f"Sending device info command: {device_info_cmd.hex()}")
            await self.client.write_gatt_char(self.tx_char, device_info_cmd)
            
            # 3. Wait for response
            await asyncio.sleep(3)
            
            # 4. Send ACK if response received (based on research)
            if self.response_received:
                ack_message = b"main recv data[ff] ["
                _LOGGER.info(f"Sending ACK: {ack_message}")
                await self.client.write_gatt_char(self.tx_char, ack_message)
                
        except Exception as e:
            _LOGGER.error(f"❌ Renogy handshake failed: {e}")

    async def _notification_handler(self, sender, data):
        """Handle notifications from the device"""
        _LOGGER.info(f"📨 Notification received from {sender}: {data.hex()}")
        self.response_data.extend(data)
        self.response_received = True
        
        # Parse the response
        if len(data) > 2:
            if data[0] == 0xFF and data[1] == 0x03:
                _LOGGER.info("✅ Valid Renogy response received!")
                data_len = data[2] if len(data) > 2 else 0
                _LOGGER.info(f"Response data length: {data_len}")
                
                if len(data) >= 3 + data_len:
                    payload = data[3:3+data_len]
                    _LOGGER.info(f"Payload: {payload.hex()}")

    async def test_characteristic_security(self):
        """Test characteristic security requirements"""
        _LOGGER.info("\n🔐 Testing characteristic security requirements")
        
        if not self.client or not self.client.is_connected:
            _LOGGER.error("❌ Not connected to device")
            return
            
        services = await self.client.get_services()
        
        for service in services:
            for char in service.characteristics:
                _LOGGER.info(f"\n📋 Characteristic: {char.uuid}")
                _LOGGER.info(f"   Properties: {char.properties}")
                _LOGGER.info(f"   Handle: {char.handle}")
                
                # Test read permission
                if "read" in char.properties and self.client:
                    try:
                        value = await self.client.read_gatt_char(char)
                        _LOGGER.info(f"   ✅ Read successful: {value.hex()}")
                    except Exception as e:
                        _LOGGER.info(f"   ❌ Read failed: {e}")
                
                # Test write permission
                if ("write" in char.properties or "write-without-response" in char.properties) and self.client:
                    try:
                        test_data = bytes([0x00])
                        await self.client.write_gatt_char(char, test_data)
                        _LOGGER.info(f"   ✅ Write test successful")
                    except Exception as e:
                        _LOGGER.info(f"   ❌ Write test failed: {e}")

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            _LOGGER.info("🔌 Disconnected from device")

async def main():
    """Main test function"""
    _LOGGER.info("🚀 Starting BluPow Authentication Test")
    _LOGGER.info(f"Target device: {DEVICE_NAME} ({DEVICE_MAC})")
    
    tester = RenogyAuthTester(DEVICE_MAC)
    
    try:
        # Step 1: Scan for device
        if not await tester.scan_for_device():
            _LOGGER.error("❌ Device not found. Make sure it's powered on and nearby.")
            return 1
        
        # Step 2: Connect and discover
        if not await tester.connect_and_discover():
            _LOGGER.error("❌ Failed to connect to device")
            return 1
        
        # Step 3: Test characteristic security
        await tester.test_characteristic_security()
        
        # Step 4: Test authentication methods
        await tester.test_authentication_methods()
        
        _LOGGER.info("\n📊 Authentication test completed")
        
    except KeyboardInterrupt:
        _LOGGER.info("⏹️ Test interrupted by user")
    except Exception as e:
        _LOGGER.error(f"💥 Test failed with error: {e}")
        return 1
    finally:
        await tester.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 