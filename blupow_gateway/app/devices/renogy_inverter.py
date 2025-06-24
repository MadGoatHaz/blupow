import asyncio
import logging
import struct
from typing import Any, Dict, Optional, List

from bleak.exc import BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak import BleakClient

from .base import BaseDevice

_LOGGER = logging.getLogger(__name__)

# Constants
RENOGY_INVERTER_SENSORS = [
    {'id': 'input_voltage', 'name': 'AC Input Voltage', 'metadata': {'unit_of_measurement': 'V', 'device_class': 'voltage'}},
    {'id': 'input_current', 'name': 'AC Input Current', 'metadata': {'unit_of_measurement': 'A', 'device_class': 'current'}},
    {'id': 'output_voltage', 'name': 'AC Output Voltage', 'metadata': {'unit_of_measurement': 'V', 'device_class': 'voltage'}},
    {'id': 'output_current', 'name': 'AC Output Current', 'metadata': {'unit_of_measurement': 'A', 'device_class': 'current'}},
    {'id': 'output_frequency', 'name': 'AC Frequency', 'metadata': {'unit_of_measurement': 'Hz', 'device_class': 'frequency'}},
    {'id': 'battery_voltage', 'name': 'Battery Voltage', 'metadata': {'unit_of_measurement': 'V', 'device_class': 'voltage'}},
    {'id': 'battery_percentage', 'name': 'Battery SOC', 'metadata': {'unit_of_measurement': '%', 'device_class': 'battery'}},
    {'id': 'temperature', 'name': 'Inverter Temperature', 'metadata': {'unit_of_measurement': '°C', 'device_class': 'temperature'}},
    {'id': 'load_active_power', 'name': 'AC Load Power', 'metadata': {'unit_of_measurement': 'W', 'device_class': 'power', 'state_class': 'measurement'}},
    {'id': 'load_apparent_power', 'name': 'AC Apparent Power', 'metadata': {'unit_of_measurement': 'VA'}},
    {'id': 'load_percentage', 'name': 'Load Percentage', 'metadata': {'unit_of_measurement': '%'}},
    {'id': 'charging_current', 'name': 'Charging Current', 'metadata': {'unit_of_measurement': 'A', 'device_class': 'current'}},
    {'id': 'charging_status', 'name': 'Charging Status'},
    {'id': 'solar_voltage', 'name': 'Solar Input Voltage', 'metadata': {'unit_of_measurement': 'V', 'device_class': 'voltage'}},
    {'id': 'solar_current', 'name': 'Solar Input Current', 'metadata': {'unit_of_measurement': 'A', 'device_class': 'current'}},
    {'id': 'solar_power', 'name': 'Solar Input Power', 'metadata': {'unit_of_measurement': 'W', 'device_class': 'power', 'state_class': 'measurement'}},
    {'id': 'model', 'name': 'Inverter Model'},
    {'id': 'device_id', 'name': 'Device ID'}
]

def crc16(data: bytes) -> bytes:
    """
    Calculates the CRC-16-MODBUS checksum for the given data.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')


class RenogyInverter(BaseDevice):
    """
    Driver for Renogy inverters.
    This is a placeholder implementation.
    """

    def __init__(self, address: str, device_type: str):
        super().__init__(address, device_type)
        # Inverter-specific UUIDs and details would go here
        self.notify_uuid = "0000ffd2-0000-1000-8000-00805f9b34fb"
        self.write_uuid = "0000ffd1-0000-1000-8000-00805f9b34fb"
        self.device_id = 1 # Per common Modbus standard

    def get_sensor_definitions(self) -> List[Dict[str, Any]]:
        """Return the sensor definitions for the Renogy Inverter."""
        return RENOGY_INVERTER_SENSORS

    def _parse_inverter_stats(self, data: bytes) -> Dict[str, Any]:
        """Parse data from register 4000 (Inverter Stats). 10 words."""
        try:
            # Unpack 10 words (10x 16-bit unsigned integers, big-endian)
            unpacked_data = struct.unpack('>HHHHHHHHHH', data)
            return {
                'input_voltage': unpacked_data[0] / 10.0,
                'input_current': unpacked_data[1] / 100.0,
                'output_voltage': unpacked_data[2] / 10.0,
                'output_current': unpacked_data[3] / 100.0,
                'output_frequency': unpacked_data[4] / 100.0,
                'load_apparent_power': unpacked_data[5], # VA
                'load_active_power': unpacked_data[6], # W
                'temperature': unpacked_data[9], # Assuming this is Celsius
            }
        except struct.error:
            _LOGGER.warning("Failed to parse inverter stats, data length mismatch.")
            return {}

    def _parse_device_id(self, data: bytes) -> Dict[str, Any]:
        """Parse data from register 4109 (Device ID). 1 word."""
        try:
            return {'device_id': struct.unpack('>H', data)[0]}
        except struct.error:
            _LOGGER.warning("Failed to parse device ID, data length mismatch.")
            return {}

    def _parse_model_info(self, data: bytes) -> Dict[str, Any]:
        """Parse data from register 4311 (Model Info). 8 words."""
        try:
            # Attempt to decode as ASCII, ignoring errors
            return {'model': data.decode('ascii', errors='ignore').strip('\x00')}
        except Exception as e:
            _LOGGER.warning(f"Failed to parse model info: {e}")
            return {}

    def _parse_charging_info(self, data: bytes) -> Dict[str, Any]:
        """Parse data from register 4327 (Charging Info). 7 words."""
        try:
            unpacked_data = struct.unpack('>HHHHHHH', data)
            return {
                'battery_voltage': unpacked_data[0] / 10.0,
                'charging_current': unpacked_data[1] / 100.0,
                'battery_percentage': unpacked_data[2], # SOC
                'solar_voltage': unpacked_data[4] / 10.0,
                'solar_current': unpacked_data[5] / 100.0,
                'solar_power': unpacked_data[4] * unpacked_data[5] / 1000.0, # Simple power calc
            }
        except struct.error:
            _LOGGER.warning("Failed to parse charging info, data length mismatch.")
            return {}
    
    def _parse_load_info(self, data: bytes) -> Dict[str, Any]:
        """Parse data from register 4408 (Load Info). 6 words."""
        try:
            unpacked_data = struct.unpack('>HHHHHH', data)
            return {
                'load_percentage': unpacked_data[3],
                # Other load info can be extracted if mapping is known
            }
        except struct.error:
            _LOGGER.warning("Failed to parse load info, data length mismatch.")
            return {}

    async def poll(self) -> Optional[Dict[str, Any]]:
        """
        Connects to the inverter, reads multiple registers, parses the data,
        and returns the combined state.
        """
        all_data = {}
        try:
            client = await self._get_bleak_client()
            
            notification_future: asyncio.Future[bytearray] = asyncio.Future()

            def notification_handler(sender: BleakGATTCharacteristic, data: bytearray):
                if not notification_future.done():
                    notification_future.set_result(data)

            await client.start_notify(self.notify_uuid, notification_handler)

            async def read_register(register: int, words: int) -> Optional[bytes]:
                nonlocal notification_future
                # Frame: Device ID (1) + Func Code (1) + Register (2) + Words (2)
                command = struct.pack('>BBHH', self.device_id, 3, register, words)
                command_with_crc = command + crc16(command)
                
                notification_future = asyncio.Future()
                _LOGGER.debug(f"Sending command to {self.mac_address}: {command_with_crc.hex()}")
                await client.write_gatt_char(self.write_uuid, command_with_crc)
                
                try:
                    # Wait for the notification with a timeout
                    response = await asyncio.wait_for(notification_future, timeout=5.0)
                    _LOGGER.debug(f"Received response from {self.mac_address}: {response.hex()}")
                    
                    # Basic validation: Device ID, func code, and CRC
                    if len(response) < 5: return None
                    if response[0] != self.device_id or response[1] != 3: return None
                    
                    payload = response[:-2]
                    received_crc = response[-2:]
                    if crc16(bytes(payload)) != received_crc:
                        _LOGGER.warning("CRC mismatch on received data")
                        return None
                    
                    return bytes(payload[3:]) # Return just the data part

                except asyncio.TimeoutError:
                    _LOGGER.warning(f"Timeout waiting for response from register {register}")
                    return None

            # Read all required registers
            stats_data = await read_register(4000, 10)
            if stats_data: all_data.update(self._parse_inverter_stats(stats_data))
            
            id_data = await read_register(4109, 1)
            if id_data: all_data.update(self._parse_device_id(id_data))
            
            model_data = await read_register(4311, 8)
            if model_data: all_data.update(self._parse_model_info(model_data))
            
            charging_data = await read_register(4327, 7)
            if charging_data: all_data.update(self._parse_charging_info(charging_data))
            
            load_data = await read_register(4408, 6)
            if load_data: all_data.update(self._parse_load_info(load_data))

            await client.stop_notify(self.notify_uuid)
            
        except BleakError as e:
            _LOGGER.error(f"Bluetooth error while polling {self.mac_address}: {e}")
            await self._disconnect() # Force disconnect on bleak error
            return None
        except Exception as e:
            _LOGGER.exception(f"An unexpected error occurred while polling {self.mac_address}: {e}")
            return None
            
        return all_data 

    async def test_connection(self) -> bool:
        """Test the BLE connection to the inverter."""
        _LOGGER.info(f"Testing connection to Renogy Inverter at {self.mac_address}")
        try:
            async with BleakClient(self.mac_address, timeout=10.0) as client:
                is_connected = await client.is_connected()
                _LOGGER.info(f"Connection test result for {self.mac_address}: {is_connected}")
                return is_connected
        except BleakError as e:
            _LOGGER.error(f"Connection test failed for {self.mac_address}: {e}")
            return False 