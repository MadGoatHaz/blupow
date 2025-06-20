#!/usr/bin/env python3
"""
Standalone Renogy Inverter Connection Test
==========================================

This script performs a definitive test of Bluetooth connectivity and data retrieval
from the Renogy RIV1230RCH-SPS inverter without any Home Assistant dependencies.

Usage: python3 scripts/standalone_inverter_test.py
"""

import asyncio
import logging
import struct
import sys
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from bleak import BleakClient
    from bleak.exc import BleakError
except ImportError:
    print("ERROR: bleak library not installed. Install with: pip install bleak")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Device constants
DEVICE_MAC = "D8:B6:73:BF:4F:75"
DEVICE_NAME = "BTRIC134000035"

# Bluetooth UUIDs (from Renogy protocol)
SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
TX_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"  # Write to device
RX_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # Notifications from device

class StandaloneInverterClient:
    """Standalone client for testing Renogy inverter communication"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self._client: Optional[BleakClient] = None
        self._response_data = bytearray()
        self._response_received = False
        
        # Inverter register sections (from cyrils/renogy-bt research)
        self.register_sections = [
            {'register': 4000, 'words': 10, 'name': 'Inverter Stats'},
            {'register': 4109, 'words': 1, 'name': 'Device ID'},
            {'register': 4311, 'words': 8, 'name': 'Model Info'},
            {'register': 4327, 'words': 7, 'name': 'Charging Info'},
            {'register': 4408, 'words': 6, 'name': 'Load Info'}
        ]
        
        # Charging status mapping
        self._charging_status_map = {
            0: 'deactivated',
            1: 'constant current',
            2: 'constant voltage', 
            4: 'floating',
            6: 'battery activation',
            7: 'battery disconnecting'
        }

    def _calculate_crc(self, data: bytes) -> int:
        """Calculate Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _create_read_command(self, start_register: int, num_registers: int) -> bytes:
        """Create Modbus read command for Renogy protocol"""
        command = bytearray([
            0xFF,  # Device ID (broadcast)
            0x03,  # Function code (read holding registers)
            (start_register >> 8) & 0xFF,  # Start register high byte
            start_register & 0xFF,          # Start register low byte
            (num_registers >> 8) & 0xFF,    # Number of registers high byte
            num_registers & 0xFF             # Number of registers low byte
        ])
        
        # Calculate and append CRC
        crc = self._calculate_crc(bytes(command))
        command.append(crc & 0xFF)         # CRC low byte
        command.append((crc >> 8) & 0xFF)  # CRC high byte
        
        return bytes(command)

    async def _notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications from device"""
        logger.info(f"📨 Received notification: {data.hex()}")
        self._response_data.extend(data)
        
        # Check for complete response
        if len(self._response_data) >= 3:
            if self._response_data[0] == 0xFF and self._response_data[1] == 0x03:
                expected_length = self._response_data[2] + 5  # Data + header + CRC
                if len(self._response_data) >= expected_length:
                    logger.info(f"✅ Complete response: {self._response_data[:expected_length].hex()}")
                    self._response_received = True
                    
                    # Send ACK (Renogy protocol requirement)
                    await self._send_ack(self._response_data[0])

    async def _send_ack(self, first_byte: int):
        """Send ACK message after receiving data"""
        try:
            if self._client and self._client.is_connected:
                ack_message = f"main recv data[{first_byte:02x}] [".encode()
                await self._client.write_gatt_char(TX_CHAR_UUID, ack_message)
                logger.debug(f"📤 ACK sent: {ack_message}")
        except Exception as e:
            logger.warning(f"Failed to send ACK: {e}")

    def _parse_inverter_stats(self, payload: bytes) -> Dict[str, Any]:
        """Parse inverter statistics (register 4000, 10 words)"""
        data = {}
        if len(payload) >= 23:  # 3 header + 20 data + 2 CRC = 25 bytes minimum
            # Data starts at byte 3 (after device_id, function_code, data_length)
            data_start = 3
            data['input_voltage'] = struct.unpack('>H', payload[data_start:data_start+2])[0] / 10.0
            data['input_current'] = struct.unpack('>H', payload[data_start+2:data_start+4])[0] / 100.0
            data['output_voltage'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0] / 10.0
            data['output_current'] = struct.unpack('>H', payload[data_start+6:data_start+8])[0] / 100.0
            data['output_frequency'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0] / 100.0
            data['battery_voltage'] = struct.unpack('>H', payload[data_start+10:data_start+12])[0] / 10.0
            data['temperature'] = struct.unpack('>H', payload[data_start+12:data_start+14])[0] / 10.0
            data['input_frequency'] = struct.unpack('>H', payload[data_start+16:data_start+18])[0] / 100.0
        return data

    def _parse_device_id(self, payload: bytes) -> Dict[str, Any]:
        """Parse device ID (register 4109, 1 word)"""
        data = {}
        if len(payload) >= 7:  # 3 header + 2 data + 2 CRC
            data_start = 3
            data['device_id'] = struct.unpack('>H', payload[data_start:data_start+2])[0]
        return data

    def _parse_model_info(self, payload: bytes) -> Dict[str, Any]:
        """Parse model information (register 4311, 8 words)"""
        data = {}
        if len(payload) >= 21:  # 3 header + 16 data + 2 CRC
            data_start = 3
            model_bytes = payload[data_start:data_start+16]
            data['model'] = model_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
        return data

    def _parse_charging_info(self, payload: bytes) -> Dict[str, Any]:
        """Parse charging information (register 4327, 7 words)"""
        data = {}
        if len(payload) >= 19:  # 3 header + 14 data + 2 CRC
            data_start = 3
            data['battery_percentage'] = struct.unpack('>H', payload[data_start:data_start+2])[0]
            data['charging_current'] = struct.unpack('>h', payload[data_start+2:data_start+4])[0] / 10.0  # signed
            data['solar_voltage'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0] / 10.0
            data['solar_current'] = struct.unpack('>H', payload[data_start+6:data_start+8])[0] / 10.0
            data['solar_power'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0]
            charging_status_code = struct.unpack('>H', payload[data_start+10:data_start+12])[0]
            data['charging_status'] = self._charging_status_map.get(charging_status_code, 'unknown')
            data['charging_power'] = struct.unpack('>H', payload[data_start+12:data_start+14])[0]
        return data

    def _parse_load_info(self, payload: bytes) -> Dict[str, Any]:
        """Parse load information (register 4408, 6 words)"""
        data = {}
        if len(payload) >= 17:  # 3 header + 12 data + 2 CRC
            data_start = 3
            data['load_current'] = struct.unpack('>H', payload[data_start:data_start+2])[0] / 10.0
            data['load_active_power'] = struct.unpack('>H', payload[data_start+2:data_start+4])[0]
            data['load_apparent_power'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0]
            data['line_charging_current'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0] / 10.0
            data['load_percentage'] = struct.unpack('>H', payload[data_start+10:data_start+12])[0]
        return data

    async def connect(self) -> bool:
        """Connect to the inverter"""
        try:
            print(f"🔗 Connecting to {DEVICE_NAME} ({self.mac_address})...")
            
            # Try to create client with more detailed error handling
            try:
                self._client = BleakClient(self.mac_address)
                print("📱 BleakClient created successfully")
            except Exception as e:
                print(f"❌ Failed to create BleakClient: {e}")
                return False
            
            # Attempt connection with timeout
            print("🔄 Attempting BLE connection...")
            try:
                await asyncio.wait_for(self._client.connect(), timeout=15.0)
            except asyncio.TimeoutError:
                print("❌ Connection timeout after 15 seconds")
                return False
            except Exception as e:
                print(f"❌ Connection exception: {type(e).__name__}: {e}")
                return False
            
            if not self._client.is_connected:
                print("❌ Failed to establish connection (is_connected = False)")
                return False
                
            print("✅ Connection successful!")
            
            # Check available services
            try:
                print("🔍 Discovering services...")
                services = await self._client.get_services()
                print(f"📋 Found {len(services.services)} services:")
                for service in services.services:
                    print(f"   - {service.uuid}")
                    if service.uuid.lower() == SERVICE_UUID.lower():
                        print(f"     ✅ Found target service: {SERVICE_UUID}")
                        for char in service.characteristics:
                            print(f"       - Characteristic: {char.uuid}")
                            if char.uuid.lower() == RX_CHAR_UUID.lower():
                                print(f"         ✅ Found RX characteristic: {RX_CHAR_UUID}")
            except Exception as e:
                print(f"⚠️  Service discovery failed: {e}")
            
            # Start notifications
            try:
                print(f"📡 Starting notifications on {RX_CHAR_UUID}...")
                await self._client.start_notify(RX_CHAR_UUID, self._notification_handler)
                print("✅ Notification handler started successfully")
            except Exception as e:
                print(f"❌ Failed to start notifications: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Unexpected connection error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def read_all_data(self) -> Dict[str, Any]:
        """Read all inverter data from all register sections"""
        if not self._client or not self._client.is_connected:
            print("❌ Device not connected")
            return {}
            
        print("\n📋 Reading all inverter data...")
        combined_data = {}
        
        parsers = [
            self._parse_inverter_stats,
            self._parse_device_id,
            self._parse_model_info,
            self._parse_charging_info,
            self._parse_load_info
        ]
        
        for i, section in enumerate(self.register_sections):
            register = section['register']
            words = section['words']
            name = section['name']
            parser = parsers[i]
            
            print(f"📤 Reading {name} (register {register}, {words} words)...")
            
            # Clear previous response
            self._response_data.clear()
            self._response_received = False
            
            # Send command
            command = self._create_read_command(register, words)
            await self._client.write_gatt_char(TX_CHAR_UUID, command)
            
            # Wait for response
            timeout_count = 0
            while not self._response_received and timeout_count < 20:  # 2 second timeout
                await asyncio.sleep(0.1)
                timeout_count += 1
            
            if self._response_received and len(self._response_data) > 0:
                section_data = parser(bytes(self._response_data))
                combined_data.update(section_data)
                print(f"✅ {name}: {len(section_data)} fields retrieved")
            else:
                print(f"⏰ {name}: No response (timeout)")
            
            # Small delay between reads
            await asyncio.sleep(0.5)
        
        combined_data['connection_status'] = 'connected'
        combined_data['last_update'] = datetime.now().isoformat()
        
        return combined_data

    async def disconnect(self):
        """Disconnect from device"""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            print("🔌 Disconnected")

async def main():
    """Main test function"""
    print("🚀 Standalone Renogy Inverter Connection Test")
    print("=" * 50)
    print(f"Target Device: {DEVICE_NAME}")
    print(f"MAC Address:   {DEVICE_MAC}")
    print(f"Test Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    client = StandaloneInverterClient(DEVICE_MAC)
    
    try:
        # Attempt connection
        if not await client.connect():
            print("\n❌ CONNECTION FAILED")
            print("Troubleshooting steps:")
            print("1. Ensure the inverter is powered on")
            print("2. Check that no other devices are connected to it")
            print("3. Try power cycling the inverter (off 60s, on, wait 2min)")
            print("4. Verify Bluetooth is enabled on this machine")
            return False
        
        # Read all data
        data = await client.read_all_data()
        
        if not data or len(data) < 5:
            print("\n❌ DATA RETRIEVAL FAILED")
            print("Connected successfully but could not read inverter data")
            return False
        
        # Display results
        print(f"\n🎉 SUCCESS! Retrieved {len(data)} data points")
        print("\n📊 INVERTER DATA:")
        print("-" * 40)
        
        # Key data points
        key_fields = [
            ('Model', 'model'),
            ('Device ID', 'device_id'), 
            ('Input Voltage', 'input_voltage', 'V'),
            ('Output Voltage', 'output_voltage', 'V'),
            ('Input Frequency', 'input_frequency', 'Hz'),
            ('Output Frequency', 'output_frequency', 'Hz'),
            ('Battery Voltage', 'battery_voltage', 'V'),
            ('Battery SOC', 'battery_percentage', '%'),
            ('Load Power', 'load_active_power', 'W'),
            ('Temperature', 'temperature', '°C'),
            ('Solar Voltage', 'solar_voltage', 'V'),
            ('Solar Current', 'solar_current', 'A'),
            ('Charging Status', 'charging_status')
        ]
        
        for field_info in key_fields:
            name = field_info[0]
            key = field_info[1]
            unit = field_info[2] if len(field_info) > 2 else ''
            
            if key in data:
                value = data[key]
                if isinstance(value, (int, float)) and unit:
                    print(f"{name+':':<18} {value}{unit}")
                else:
                    print(f"{name+':':<18} {value}")
        
        print("-" * 40)
        print("✅ INTEGRATION READY!")
        print("The inverter is responding correctly.")
        print("You can now add the BluPow integration to Home Assistant.")
        
        return True
        
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        logger.exception("Test failed with exception:")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
        sys.exit(1) 