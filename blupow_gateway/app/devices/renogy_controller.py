import asyncio
import logging
from typing import Any, Dict, Optional, List

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

from .base import BaseDevice
from ..utils import _calculate_crc, _bytes_to_int, _parse_temperature

_LOGGER = logging.getLogger(__name__)

# --- Constants ---
CONNECTION_TIMEOUT = 20.0
READ_TIMEOUT = 15.0

class RenogyController(BaseDevice):
    """Driver for Renogy solar charge controllers."""

    def __init__(self, address: str, device_type: str, config: dict, ble_device: Optional[BLEDevice] = None):
        super().__init__(address, device_type, ble_device)
        self.device_id = 1  # Modbus ID for controllers
        self.notify_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"
        self.write_uuid = "0000ffd1-0000-1000-8000-00805f9b34fb"
        self.sections = [
            {'register': 12, 'words': 8, 'parser': self._parse_device_info},
            {'register': 256, 'words': 34, 'parser': self._parse_charging_info},
            {'register': 57348, 'words': 1, 'parser': self._parse_battery_type},
        ]
        self._data_buffer: Dict[str, Any] = {}
        self._notification_event = asyncio.Event()

    def get_sensor_definitions(self) -> List[Dict[str, Any]]:
        """Return the sensor definitions for the Renogy Controller."""
        return [
            # Battery
            {"key": "battery_soc", "name": "Battery SOC", "unit": "%", "icon": "mdi:battery", "device_class": "battery"},
            {"key": "battery_voltage", "name": "Battery Voltage", "unit": "V", "icon": "mdi:battery-high", "device_class": "voltage"},
            {"key": "battery_current", "name": "Battery Current", "unit": "A", "icon": "mdi:current-dc", "device_class": "current"},
            {"key": "battery_temperature", "name": "Battery Temperature", "unit": "°C", "icon": "mdi:thermometer", "device_class": "temperature"},
            {"key": "battery_type", "name": "Battery Type", "icon": "mdi:car-battery"},

            # Solar / PV
            {"key": "solar_voltage", "name": "Solar Voltage", "unit": "V", "icon": "mdi:solar-power", "device_class": "voltage"},
            {"key": "solar_current", "name": "Solar Current", "unit": "A", "icon": "mdi:solar-power", "device_class": "current"},
            {"key": "solar_power", "name": "Solar Power", "unit": "W", "icon": "mdi:solar-power", "device_class": "power"},
            {"key": "power_generation_today", "name": "Solar Energy Today", "unit": "kWh", "icon": "mdi:solar-power", "device_class": "energy", "state_class": "total_increasing"},
            {"key": "power_generation_total", "name": "Solar Energy Total", "unit": "kWh", "icon": "mdi:solar-power", "device_class": "energy", "state_class": "total_increasing"},

            # Load
            {"key": "load_status", "name": "Load Status", "icon": "mdi:power-plug"},
            {"key": "load_voltage", "name": "Load Voltage", "unit": "V", "icon": "mdi:power-plug", "device_class": "voltage"},
            {"key": "load_current", "name": "Load Current", "unit": "A", "icon": "mdi:power-plug", "device_class": "current"},
            {"key": "load_power", "name": "Load Power", "unit": "W", "icon": "mdi:power-plug", "device_class": "power"},
            {"key": "power_consumption_today", "name": "Load Energy Today", "unit": "kWh", "icon": "mdi:power-plug", "device_class": "energy", "state_class": "total_increasing"},

            # Controller
            {"key": "controller_temperature", "name": "Controller Temperature", "unit": "°C", "icon": "mdi:thermometer", "device_class": "temperature"},
            {"key": "charging_status", "name": "Charging Status", "icon": "mdi:power-plug-battery"},
        ]

    async def poll(self) -> Optional[Dict[str, Any]]:
        _LOGGER.debug(f"[{self.mac_address}] Starting data fetch process.")
        
        try:
            if not self.is_connected:
                _LOGGER.info(f"[{self.mac_address}] Not connected, establishing connection.")
                if not await self.connect():
                    _LOGGER.error(f"Could not connect to {self.mac_address} for polling.")
                    return None
            
            assert self._client is not None # Should be connected here

            # Ensure notifications are enabled
            await self._client.start_notify(self.notify_uuid, self._notification_handler)

            self._data_buffer.clear()
            all_data = {}
            for section in self.sections:
                try:
                    command = self._build_modbus_command(section['register'], section['words'])
                    self._notification_event.clear()
                    await self._client.write_gatt_char(self.write_uuid, command, response=False)
                    await asyncio.wait_for(self._notification_event.wait(), timeout=READ_TIMEOUT)
                    # Data from the handler is placed in _data_buffer, let's merge it
                    all_data.update(self._data_buffer)
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"[{self.mac_address}] Timeout polling register {section['register']}. Skipping.")
                    continue # Try the next section
            
            # Stop notifications to save battery, but keep the connection alive.
            await self._client.stop_notify(self.notify_uuid)

            return all_data if all_data else None

        except BleakError as e:
            _LOGGER.error(f"[{self.mac_address}] BleakError during poll: {e}. Disconnecting.")
            await self.disconnect() # Force disconnect on BleakError
            return None
        except Exception as e:
            _LOGGER.error(f"[{self.mac_address}] An unexpected error occurred during poll: {e}", exc_info=True)
            await self.disconnect()
            return None

    def _notification_handler(self, sender, data: bytearray):
        _LOGGER.debug(f"[{self.mac_address}] Received notification: {data.hex()}")
        # We don't know which request this response is for, so we try all parsers
        # This is less efficient but more robust if responses arrive out of order.
        parser_found = False
        for section in self.sections:
            # A simple length check is a good first-pass filter
            if len(data) >= 5: # Minimum length of a modbus frame
                try:
                    # Pass immutable bytes to parsers
                    parsed_data = section['parser'](bytes(data))
                    if parsed_data: # If parser returns data, we assume it was the right one
                        self._data_buffer.clear() # Clear previous partial data
                        self._data_buffer.update(parsed_data)
                        parser_found = True
                        break
                except Exception:
                    # This parser didn't work, try the next one
                    continue
        
        if not parser_found:
            _LOGGER.warning(f"[{self.mac_address}] Could not parse received data: {data.hex()}")

        self._notification_event.set()

    def _build_modbus_command(self, start_register: int, count: int) -> bytes:
        command = bytearray([
            self.device_id, 0x03,
            (start_register >> 8) & 0xFF, start_register & 0xFF,
            (count >> 8) & 0xFF, count & 0xFF
        ])
        crc = _calculate_crc(bytes(command))
        command.extend(crc)
        return bytes(command)

    # --- Parsers ---
    def _parse_device_info(self, bs: bytes) -> Dict[str, Any]:
        return {'model': (bs[3:19]).decode('utf-8', 'ignore').strip().rstrip('\x00')}

    def _parse_charging_info(self, bs: bytes) -> Dict[str, Any]:
        # Basic validation: Check function code (0x03) and byte count
        if len(bs) < 5 or bs[1] != 0x03 or bs[2] != 68: # 34 words * 2 = 68 bytes
            return {}
        charging_state_map = {0: 'deactivated', 1: 'activated', 2: 'mppt', 3: 'equalizing', 4: 'boost', 5: 'floating', 6: 'current limiting'}
        load_state_map = {0: 'off', 1: 'on'}
        return {
            'battery_soc': _bytes_to_int(bs, 3, 2),
            'battery_voltage': _bytes_to_int(bs, 5, 2, scale=0.1),
            'battery_current': _bytes_to_int(bs, 7, 2, scale=0.01),
            'battery_temperature': _parse_temperature(int(_bytes_to_int(bs, 10, 1))),
            'controller_temperature': _parse_temperature(int(_bytes_to_int(bs, 9, 1))),
            'load_status': load_state_map.get(int(_bytes_to_int(bs, 67, 1)) >> 7, 'unknown'),
            'load_voltage': _bytes_to_int(bs, 11, 2, scale=0.1),
            'load_current': _bytes_to_int(bs, 13, 2, scale=0.01),
            'load_power': _bytes_to_int(bs, 15, 2),
            'solar_voltage': _bytes_to_int(bs, 17, 2, scale=0.1),
            'solar_current': _bytes_to_int(bs, 19, 2, scale=0.01),
            'solar_power': _bytes_to_int(bs, 21, 2),
            'charging_amp_hours_today': _bytes_to_int(bs, 37, 2),
            'discharging_amp_hours_today': _bytes_to_int(bs, 39, 2),
            'power_generation_today': _bytes_to_int(bs, 41, 2, scale=0.001), # Wh -> kWh
            'power_consumption_today': _bytes_to_int(bs, 43, 2, scale=0.001), # Wh -> kWh
            'power_generation_total': _bytes_to_int(bs, 59, 4, scale=0.001), # Wh -> kWh
            'charging_status': charging_state_map.get(int(_bytes_to_int(bs, 68, 1)), 'unknown'),
        }

    def _parse_battery_type(self, bs: bytes) -> Dict[str, Any]:
        # Basic validation: Check function code (0x03) and byte count
        if len(bs) < 5 or bs[1] != 0x03 or bs[2] != 2: # 1 word * 2 = 2 bytes
            return {}
        battery_type_map = {1: 'open', 2: 'sealed', 3: 'gel', 4: 'lithium', 5: 'custom'}
        return {'battery_type': battery_type_map.get(int(_bytes_to_int(bs, 3, 2)), 'unknown')}

    async def test_connection(self) -> bool:
        """Test the BLE connection to the controller."""
        _LOGGER.info(f"Testing connection to Renogy Controller at {self.mac_address}")
        is_connected = await self.connect()
        if is_connected:
            await self.disconnect()
        return is_connected 