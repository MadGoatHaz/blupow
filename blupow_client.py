"""
BluPow BLE Client for Home Assistant Integration - Enhanced Renogy Protocol

Based on cyrils/renogy-bt: Direct connection without pairing, enhanced device discovery
Supports ESPHome Bluetooth Proxy for extended range
"""

import asyncio
import logging
import platform
import sys
import struct
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError
from bleak.backends.device import BLEDevice
from homeassistant.core import HomeAssistant
from bleak_esphome.backend.device import ESPHomeBLEDevice

from .const import (
    RENOGY_SERVICE_UUID,
    RENOGY_TX_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_MANUFACTURER_ID,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
    DEVICE_SENSORS,
    RenogyRegisters,
)

_LOGGER = logging.getLogger(__name__)

class EnvironmentInfo:
    """Detect Home Assistant environment details"""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_version = sys.version_info
        self.is_docker = self._detect_docker()
        self.is_hassio = self._detect_hassio()
        self.ble_backend = self._detect_ble_backend()
        
    def _detect_docker(self) -> bool:
        """Detect if running in Docker"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except:
            return False
            
    def _detect_hassio(self) -> bool:
        """Detect if running in Home Assistant OS"""
        try:
            import os
            return os.path.exists('/usr/bin/hassio')
        except:
            return False
            
    def _detect_ble_backend(self) -> str:
        """Detect BLE backend in use"""
        if self.platform == "Linux":
            return "BlueZ"
        elif self.platform == "Windows":
            return "WinRT"
        elif self.platform == "Darwin":
            return "CoreBluetooth"
        else:
            return "Unknown"
    
    def __str__(self) -> str:
        return f"Platform: {self.platform}, Python: {self.python_version[:2]}, Docker: {self.is_docker}, HassIO: {self.is_hassio}, BLE: {self.ble_backend}"

class BluPowClient:
    """Enhanced BluPow client with proper Renogy protocol implementation"""
    
    def __init__(self, address: str, hass: HomeAssistant):
        self.address = address
        self.hass = hass
        self.name = address  # Default to address until device is found
        self.client: Optional[BleakClient] = None
        self.environment = EnvironmentInfo()
        self._connection_attempts = 0
        self._last_data = {}
        self._is_connected = False
        self._ble_device: Optional[BLEDevice] = None
        self._buffer = bytearray()
        self.device_id = 1 # Default device ID
        self._new_data_event = asyncio.Event()

        # ESPHome Bluetooth Proxy support
        self._proxy_client: Optional[BleakClient] = None
        self._is_proxy_connected = False
        
        _LOGGER.info(f"Environment detected: {self.environment}")
        _LOGGER.info(f"BluPow client initialized for address: {self.address} - Environment: {self.environment}")
        
    @property
    def is_connected(self) -> bool:
        return self._is_connected or self._is_proxy_connected
    
    async def connect(self, ble_device: BLEDevice) -> bool:
        """Connect to the BLE device."""
        self._ble_device = ble_device
        _LOGGER.info(f"🔗 Connecting to Renogy device: {self._ble_device.name} ({self._ble_device.address})")

        if isinstance(self._ble_device, ESPHomeBLEDevice):
            _LOGGER.info("ESPHome device detected, using proxy connection.")
            self._proxy_client = BleakClient(self._ble_device)
            try:
                await self._proxy_client.connect()
                self._is_proxy_connected = self._proxy_client.is_connected
                _LOGGER.info(f"Proxy connection status: {self._is_proxy_connected}")
            except Exception as e:
                _LOGGER.error(f"Failed to connect via ESPHome proxy: {e}")
                self._is_proxy_connected = False
        else:
            _LOGGER.info("No ESPHome proxy, using standard BleakClient.")
            self.client = BleakClient(self._ble_device)
            try:
                await self.client.connect()
                self._is_connected = self.client.is_connected
                _LOGGER.info(f"Standard connection status: {self._is_connected}")
            except Exception as e:
                _LOGGER.error(f"Failed to connect via standard client: {e}")
                self._is_connected = False
        
        if not self.is_connected:
            _LOGGER.error("Failed to establish any connection to the device.")
            return False

        _LOGGER.info("Connection successful. Starting notification handler.")
        await self.start_notifications()
        return True

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if self._proxy_client and self._is_proxy_connected:
            _LOGGER.info("Disconnecting from ESPHome proxy.")
            await self._proxy_client.disconnect()
            self._is_proxy_connected = False
        if self.client and self._is_connected:
            _LOGGER.info("Disconnecting from standard client.")
            await self.client.disconnect()
            self._is_connected = False
        self._last_data['connection_status'] = 'disconnected'

    async def start_notifications(self) -> None:
        """Start receiving notifications from the device."""
        client = self._proxy_client if self._is_proxy_connected else self.client
        if not client:
            _LOGGER.error("Cannot start notifications, no client available.")
            return
        _LOGGER.info(f"Starting notifications on {RENOGY_SERVICE_UUID}")
        await client.start_notify(RENOGY_RX_CHAR_UUID, self.notification_handler)

    def notification_handler(self, sender, data: bytearray):
        """Handle notifications from Renogy device, buffering data until a complete frame is received."""
        _LOGGER.debug(f"📨 Notification chunk received: {data.hex()}")
        self._buffer.extend(data)
        _LOGGER.debug(f"Buffer content: {self._buffer.hex()}")

        # Process the buffer to find and handle complete frames
        while True:
            frame = self._find_complete_frame()
            if frame is None:
                break
            self._process_modbus_response(frame)

    def _find_complete_frame(self) -> Optional[bytearray]:
        """
        Check the buffer for a complete Modbus frame.
        A valid frame is: [0xFF, 0x03, length, ...data..., checksum_high, checksum_low]
        Returns the frame if found, and removes it from the buffer. Otherwise returns None.
        """
        # Minimum frame length: Address(1) + Function(1) + Length(1) + CRC(2) = 5
        if len(self._buffer) < 5:
            return None

        # Look for start byte (device ID)
        if self._buffer[0] != self.device_id:
            # If the first byte is not the device ID, we have a synchronization issue.
            # This can happen if there's leftover data from a previous connection.
            # We'll try to find the start of a valid frame.
            
            start_index = -1
            for i in range(1, len(self._buffer)):
                if self._buffer[i] == self.device_id:
                    start_index = i
                    break
            
            if start_index != -1:
                _LOGGER.warning(f"Invalid data at buffer start, discarding {start_index} bytes. Buffer: {self._buffer.hex()}")
                self._buffer = self._buffer[start_index:]
                # Restart the check after slicing the buffer
                return self._find_complete_frame()
            else:
                # If device ID is not found at all, the buffer is likely junk.
                _LOGGER.error(f"Could not find frame start (device ID {self.device_id}). Discarding buffer: {self._buffer.hex()}")
                self._buffer.clear()
                return None

        # At this point, buffer[0] is our device ID.
        # Now check function code. We only expect 0x03 (read holding registers).
        # A Modbus exception response would have the high bit set (e.g., 0x83).
        if self._buffer[1] not in [0x03, 0x83, 0x10]: # Allow read, exception, and write
            _LOGGER.error(f"Invalid function code {self._buffer[1]:02x}. Discarding buffer: {self._buffer.hex()}")
            self._buffer.clear()
            return None

        # If it's an exception, the frame length is fixed at 5 bytes
        if self._buffer[1] == 0x83:
            if len(self._buffer) >= 5:
                frame = self._buffer[:5]
                self._buffer = self._buffer[5:]
                # CRC check for exception frame
                if not self._validate_crc(frame):
                    _LOGGER.error(f"CRC check failed for exception frame: {frame.hex()}")
                    return None
                return frame
            else:
                return None # Not enough data for a full exception frame

        # For a normal response (func code 0x03), the 3rd byte is the data length
        data_len = self._buffer[2]
        frame_len = 3 + data_len + 2  # Header(3) + Data + CRC(2)

        if len(self._buffer) >= frame_len:
            frame = self._buffer[:frame_len]
            self._buffer = self._buffer[frame_len:]

            if self._validate_crc(frame):
                return frame
            else:
                _LOGGER.error(f"CRC check failed for frame: {frame.hex()}. Discarding.")
        # Frame is corrupt, discard and continue searching
                return None
        else:
            _LOGGER.debug(f"Incomplete frame. Need {frame_len} bytes, have {len(self._buffer)}. Waiting for more data.")
            return None

    def _process_modbus_response(self, data: bytearray):
        """Process a complete Modbus response frame from Renogy device"""
        try:
            _LOGGER.debug(f"Processing validated Modbus response: {data.hex()}")

            data_length = data[2]
            payload = data[3:3 + data_length]
            
            if len(payload) != data_length:
                _LOGGER.error(f"Payload length mismatch. Expected {data_length}, got {len(payload)}. Frame: {data.hex()}")
                return

            # Heuristic to differentiate between data block and info string response
            # The main data block is large (34 regs * 2 bytes/reg = 68 bytes)
            # The info block is smaller (8 regs * 2 bytes/reg = 16 bytes)
            if data_length > 20: # Likely the main data block
                _LOGGER.debug(f"Processing as numeric data block (length {data_length})")
                registers = [int.from_bytes(payload[i:i+2], 'big') for i in range(0, len(payload), 2)]
                self._update_data_from_registers(registers)
            else: # Likely a string response like model number
                _LOGGER.debug(f"Processing as string data block (length {data_length})")
                try:
                    # Attempt to decode as ASCII string, removing padding and null bytes
                    model_string = payload.decode('ascii').strip().replace('\x00', '')
                    self._last_data['model_number'] = model_string
                    _LOGGER.info(f"Parsed device model: {model_string}")
                except UnicodeDecodeError:
                    _LOGGER.warning(f"Could not decode payload as ASCII string: {payload.hex()}")
            
            self._new_data_event.set() # Signal that new data has been processed

        except Exception as e:
            _LOGGER.error(f"Error processing Modbus response: {e}")
    
    def _update_data_from_registers(self, registers: List[int]):
        """Update device data from a block of register values."""
        try:
            if not registers or len(registers) < RenogyRegisters.READ_BLOCK_SIZE:
                _LOGGER.warning(f"Not enough registers to parse data. Got {len(registers)}, expected at least {RenogyRegisters.READ_BLOCK_SIZE}.")
                return

            def get_val(index, scale=1.0, signed=False):
                """Safely get a value from the register list."""
                raw_val = registers[index]
                if signed and raw_val & 0x8000:  # Check for negative value
                    return -((~raw_val & 0xFFFF) + 1) * scale
                return raw_val * scale

            # Unpacking data using the offsets from RenogyRegisters
            self._last_data['battery_soc'] = get_val(RenogyRegisters.BATTERY_SOC)
            self._last_data['battery_voltage'] = get_val(RenogyRegisters.BATTERY_VOLTAGE, 0.1)
            
            # Combine two registers for battery current (32-bit value)
            raw_current = (registers[RenogyRegisters.BATTERY_CURRENT_RAW + 1] << 16) | registers[RenogyRegisters.BATTERY_CURRENT_RAW]
            self._last_data['battery_current'] = (raw_current / 100.0)
            
            self._last_data['battery_temp'] = get_val(RenogyRegisters.BATTERY_TEMP, signed=True)
            self._last_data['controller_temp'] = get_val(RenogyRegisters.CONTROLLER_TEMP, signed=True)
            self._last_data['load_voltage'] = get_val(RenogyRegisters.LOAD_VOLTAGE, 0.1)
            self._last_data['load_current'] = get_val(RenogyRegisters.LOAD_CURRENT, 0.01)
            self._last_data['load_power'] = get_val(RenogyRegisters.LOAD_POWER)
            self._last_data['solar_voltage'] = get_val(RenogyRegisters.SOLAR_VOLTAGE, 0.1)
            self._last_data['solar_current'] = get_val(RenogyRegisters.SOLAR_CURRENT, 0.01)
            self._last_data['solar_power'] = get_val(RenogyRegisters.SOLAR_POWER)
            
            # Daily Stats
            self._last_data['daily_power_generation'] = get_val(RenogyRegisters.DAILY_POWER_GENERATION)
            self._last_data['daily_power_consumption'] = get_val(RenogyRegisters.DAILY_POWER_CONSUMPTION)
            
            # Charging Status
            charging_status_code = get_val(RenogyRegisters.CHARGING_STATUS)
            self._last_data['charging_status'] = self._charging_status_map.get(charging_status_code, "Unknown")

            # Total Power Generation (kWh)
            total_gen_kwh = ((registers[RenogyRegisters.POWER_GENERATION_TOTAL_H] << 16) | registers[RenogyRegisters.POWER_GENERATION_TOTAL_L])
            self._last_data['power_generation_total'] = total_gen_kwh

            # Amp Hours
            self._last_data['charging_amp_hours_today'] = get_val(RenogyRegisters.CHARGING_AMP_HOURS_TODAY)
            self._last_data['discharging_amp_hours_today'] = get_val(RenogyRegisters.DISCHARGING_AMP_HOURS_TODAY)
            
            self._last_data['connection_status'] = 'connected'
            self._last_data['last_update'] = datetime.now().isoformat()
            
            _LOGGER.debug(f"Updated data: {self._last_data}")

        except IndexError as e:
            _LOGGER.error(f"Index error while parsing registers. This may be due to an incorrect READ_BLOCK_SIZE. {e}")
        except Exception as e:
            _LOGGER.error(f"Error updating data from registers: {e}")
    
    async def read_device_info(self) -> dict:
        """Read static device information like model number."""
        if not self.is_connected:
            _LOGGER.error("Not connected to device.")
            return {}
        
        try:
            if self._last_data.get('model_number') and self._last_data.get('model_number') != 'Unknown':
                 return {'model_number': self._last_data.get('model_number')}

            client = self._proxy_client if self._is_proxy_connected else self.client
            if not client:
                _LOGGER.error("No BLE client available for device info read.")
                return {}

            services = await client.get_services()
            tx_char = self.get_characteristic(services, RENOGY_TX_CHAR_UUID)
            if not tx_char:
                _LOGGER.error("TX characteristic not found for device info.")
                return {}

            # Reading the model number which is typically a string over several registers.
            # We'll need a specific parser for this response.
            read_info_command = self._create_modbus_command(0x03, RenogyRegisters.MODEL, 8)
            
            self._new_data_event.clear()
            await client.write_gatt_char(tx_char, read_info_command, response=True)
            
            try:
                await asyncio.wait_for(self._new_data_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for device info response.")

            return {"model_number": self._last_data.get("model_number", "Unknown")}

        except Exception as e:
            _LOGGER.error(f"Error reading device info: {e}")
            return {}

    async def read_realtime_data(self) -> bool:
        """Read real-time data from the device."""
        if not self.is_connected:
            _LOGGER.error("Not connected to device for realtime data.")
            return False

        try:
            client = self._proxy_client if self._is_proxy_connected else self.client
            if not client:
                _LOGGER.error("No BLE client available for realtime data read.")
                return False
                
            services = await client.get_services()
            tx_char = self.get_characteristic(services, RENOGY_TX_CHAR_UUID)
            if not tx_char:
                _LOGGER.error("TX characteristic not found for real-time data.")
                return False

            # Fetch the main data block
            read_data_command = self._create_modbus_command(0x03, RenogyRegisters.READ_BLOCK_START, RenogyRegisters.READ_BLOCK_SIZE)
            self._new_data_event.clear()
            await client.write_gatt_char(tx_char, read_data_command, response=True)

            try:
                await asyncio.wait_for(self._new_data_event.wait(), timeout=5.0)
                return True
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for real-time data response.")
                return False
        
        except Exception as e:
            _LOGGER.error(f"Error reading real-time data: {e}")
            return False

    def _get_offline_data(self) -> Dict[str, Any]:
        """
        Return a dictionary with default values for all sensors when the device is offline.
        This ensures that the entities are still created in Home Assistant but appear as 'Unavailable'.
        """
        offline_data = {
            key: None for key in DEVICE_SENSORS
        }
        offline_data['connection_status'] = 'disconnected'
        offline_data['last_update'] = datetime.now().isoformat()
        _LOGGER.debug("Returning offline data structure.")
        return offline_data

    def get_data(self) -> Dict[str, Any]:
        """Return the latest device data."""
        if not self.is_connected:
            return self._get_offline_data()
        return self._last_data

    @staticmethod
    def _create_modbus_command(function_code: int, start_address: int, number_of_registers: int) -> bytearray:
        """Create a Modbus RTU command."""
        command = bytearray()
        command.append(1)  # Device ID
        command.append(function_code)
        command.extend(start_address.to_bytes(2, 'big'))
        command.extend(number_of_registers.to_bytes(2, 'big'))
        
        crc = BluPowClient._calculate_crc(command)
        command.extend(crc.to_bytes(2, 'little'))
        
        return command

    @staticmethod
    def _calculate_crc(data: bytearray) -> int:
        """Calculate CRC16 for Modbus."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def _validate_crc(self, frame: bytearray) -> bool:
        """Validate the CRC of a received Modbus frame."""
        if len(frame) < 2:
            return False
        
        received_crc = int.from_bytes(frame[-2:], 'little')
        calculated_crc = self._calculate_crc(frame[:-2])
        
        is_valid = received_crc == calculated_crc
        if not is_valid:
            _LOGGER.error(f"CRC Mismatch! Received: {received_crc:04x}, Calculated: {calculated_crc:04x}, Frame: {frame.hex()}")
        return is_valid

    def get_characteristic(self, services, uuid):
        """Helper to find a characteristic by UUID."""
        for service in services:
            for char in service.characteristics:
                if char.uuid.lower() == uuid.lower():
                    return char
        return None

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'client') and self.client:
            try:
                asyncio.create_task(self.disconnect())
            except:
                pass 