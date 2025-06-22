import asyncio
import logging
from typing import Any, Dict, Optional, List
from functools import partial

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from .base import BaseDevice
from ..utils import _calculate_crc, _bytes_to_int

_LOGGER = logging.getLogger(__name__)

# --- Constants ---
CONNECTION_TIMEOUT = 20.0
READ_TIMEOUT = 15.0

class GenericModbusDevice(BaseDevice):
    """
    A generic driver for Modbus-over-BLE devices, configured via JSON.
    This driver expects a 'config' block in the device's configuration.
    """

    def __init__(self, address: str, device_type: str, config: Dict[str, Any]):
        super().__init__(address, device_type)
        
        # Validate and store configuration
        if not self._validate_config(config):
            raise ValueError("Invalid configuration provided for GenericModbusDevice.")
            
        self.config = config
        self.device_id = self.config.get("device_id", 1)
        self.notify_uuid = self.config["notify_uuid"]
        self.write_uuid = self.config["write_uuid"]
        self._data_buffer: Dict[str, Any] = {}
        self._notification_event = asyncio.Event()

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Basic validation of the device's JSON configuration."""
        if not all(k in config for k in ["notify_uuid", "write_uuid", "sensors"]):
            _LOGGER.error(f"[{self.mac_address}] Config missing required keys: notify_uuid, write_uuid, sensors")
            return False
        if not isinstance(config["sensors"], list) or not config["sensors"]:
            _LOGGER.error(f"[{self.mac_address}] 'sensors' must be a non-empty list.")
            return False
        return True

    def get_sensor_definitions(self) -> List[Dict[str, Any]]:
        """Return the sensor definitions from the JSON configuration."""
        # The 'sensors' list in the config already matches the required format.
        return self.config.get("sensors", [])

    async def get_data(self) -> Optional[Dict[str, Any]]:
        _LOGGER.debug(f"[{self.mac_address}] Starting generic data fetch process.")
        client = None
        try:
            device = await BleakScanner.find_device_by_address(self.mac_address, timeout=10.0)
            if not device:
                _LOGGER.warning(f"[{self.mac_address}] Device not found during scan.")
                return None

            client = BleakClient(device, timeout=CONNECTION_TIMEOUT)
            await client.connect()
            
            self._data_buffer.clear()
            # For this generic driver, we read one register at a time per sensor definition
            for sensor in self.get_sensor_definitions():
                try:
                    reg = sensor['register']
                    words = sensor.get('words', 1) # Default to reading 1 word (2 bytes)
                    
                    # Create a specific handler for this sensor request
                    handler = partial(self._notification_handler, sensor_def=sensor)
                    await client.start_notify(self.notify_uuid, handler)

                    command = self._build_modbus_command(reg, words)
                    self._notification_event.clear()
                    await client.write_gatt_char(self.write_uuid, command, response=False)
                    await asyncio.wait_for(self._notification_event.wait(), timeout=READ_TIMEOUT)
                    
                    await client.stop_notify(self.notify_uuid)
                    
                except (KeyError, TypeError):
                    _LOGGER.warning(f"[{self.mac_address}] Skipping malformed sensor definition: {sensor}")
                    continue
                except asyncio.TimeoutError:
                     _LOGGER.warning(f"[{self.mac_address}] Timeout waiting for notification for register {reg}.")
                     continue # Try the next sensor

            return self._data_buffer

        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.error(f"[{self.mac_address}] Connection or Bleak-level error: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"[{self.mac_address}] An unexpected error occurred: {e}", exc_info=True)
            return None
        finally:
            if client and client.is_connected:
                await client.disconnect()

    def _notification_handler(self, sender, data: bytearray, sensor_def: Dict[str, Any]):
        """Handle incoming notifications and parse them based on a specific sensor definition."""
        _LOGGER.debug(f"[{self.mac_address}] Received notification for {sensor_def['key']}: {data.hex()}")
        
        response_words = (len(data) - 5) // 2
        expected_words = sensor_def.get('words', 1)

        if response_words != expected_words:
            _LOGGER.warning(f"[{self.mac_address}] Received data of unexpected length ({len(data)}) for sensor {sensor_def['key']}.")
        else:
            try:
                value = _bytes_to_int(bytes(data), 3, response_words * 2, 
                                      signed=sensor_def.get('signed', False), 
                                      scale=sensor_def.get('scale', 1.0))
                self._data_buffer[sensor_def['key']] = value
            except (KeyError, TypeError) as e:
                _LOGGER.warning(f"[{self.mac_address}] Error parsing sensor {sensor_def.get('key')}: {e}")

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