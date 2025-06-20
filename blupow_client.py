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
        # This will be checked later when device is available
        self._supports_esphome_proxy = False
        
        _LOGGER.info(f"Environment detected: {self.environment}")
        _LOGGER.info(f"BluPow client initialized for address: {self.address} - Environment: {self.environment}")
        
    def _detect_esphome_proxy(self) -> bool:
        """Detect if ESPHome Bluetooth Proxy is available for enhanced range"""
        if not self._ble_device:
            return False
        
        # Check if device is being accessed through ESPHome proxy
        # ESPHome proxies typically have specific characteristics in metadata
        try:
            # Check for ESPHome proxy indicators in device metadata
            if hasattr(self._ble_device, 'metadata'):
                metadata = str(self._ble_device.metadata).lower()
                if 'esphome' in metadata or 'proxy' in metadata:
                    _LOGGER.info(f"🌐 ESPHome Bluetooth Proxy detected for device {self.address}")
                    return True
            
            # Check if device is reachable through known proxy addresses
            # User's multi-proxy setup for extended coverage
            known_proxies = [
                ('esp32-bluetooth-proxy-2105e4', '192.168.51.151', 'Primary - Tested (+10 dB improvement)'),
                ('proxy-2', '192.168.51.207', 'Secondary - Available for testing'),
                ('proxy-3', '192.168.51.109', 'Tertiary - Available for testing'),
                ('a0:b7:65:21:05:e6', '192.168.51.151', 'Primary proxy MAC')
            ]
            
            # Log proxy detection attempt with all available proxies
            _LOGGER.debug(f"Checking for ESPHome proxy support for {self.address}")
            _LOGGER.info(f"📡 Available ESPHome Bluetooth Proxies:")
            for name, ip, description in known_proxies[:3]:  # Log first 3 (exclude MAC)
                _LOGGER.info(f"   🔹 {name} ({ip}) - {description}")
            
            # TODO: Future enhancement - actively test which proxy provides best signal
            # This would require integration with Home Assistant's Bluetooth component
            # to determine which proxy is actually being used for connections
            
            return False  # Will be True if proxy is actively being used
            
        except Exception as e:
            _LOGGER.debug(f"Error detecting ESPHome proxy: {e}")
            return False
    
    async def discover_renogy_devices(self, timeout: float = DEFAULT_SCAN_TIMEOUT) -> List[Tuple[str, str, int]]:
        """
        Enhanced device discovery for Renogy devices
        
        Returns:
            List of tuples: (address, name, rssi)
        """
        _LOGGER.info("🔍 Starting enhanced Renogy device discovery...")
        
        devices = []
        try:
            discovered = await BleakScanner.discover(timeout=timeout)
            
            for device in discovered:
                if self._is_potential_renogy_device(device):
                    rssi = getattr(device, 'rssi', -999)
                    devices.append((device.address, device.name or "Unknown", rssi))
                    _LOGGER.info(f"📱 Found potential Renogy device: {device.name} ({device.address}) RSSI: {rssi}")
                    
                    # Check for ESPHome proxy
                    if self._is_esphome_proxy(device):
                        _LOGGER.info(f"🌐 ESPHome Bluetooth Proxy detected: {device.name}")
                        
        except Exception as e:
            _LOGGER.error(f"Device discovery failed: {e}")
            
        _LOGGER.info(f"✅ Discovery completed: {len(devices)} potential Renogy devices found")
        return devices
    
    def _is_potential_renogy_device(self, device: BLEDevice) -> bool:
        """Check if device is potentially a Renogy device"""
        if not device.name:
            return False
            
        name = device.name.lower()
        
        # Renogy device name patterns
        renogy_patterns = [
            'bt-th',       # BT-TH-XXXXXXXX (common Renogy pattern)
            'btric',       # BTRIC134000035 (Renogy inverter)
            'renogy',      # Direct Renogy naming
            'rover',       # Rover series
            'wanderer',    # Wanderer series
            'rng-ctrl',    # Direct controller naming
        ]
        
        # Check manufacturer data for Renogy signature
        manufacturer_data = getattr(device, 'metadata', {}).get('manufacturer_data', {})
        if RENOGY_MANUFACTURER_ID in manufacturer_data:
            return True
            
        # Check service UUIDs
        service_uuids = getattr(device, 'metadata', {}).get('uuids', [])
        if RENOGY_SERVICE_UUID.lower() in [uuid.lower() for uuid in service_uuids]:
            return True
            
        # Check name patterns
        return any(pattern in name for pattern in renogy_patterns)
    
    def _is_esphome_proxy(self, device: BLEDevice) -> bool:
        """Check if device is an ESPHome Bluetooth Proxy"""
        if not device.name:
            return False
            
        name = device.name.lower()
        proxy_patterns = ['esphome', 'bluetooth-proxy', 'esp32-proxy']
        
        return any(pattern in name for pattern in proxy_patterns)
    
    async def check_device_availability(self) -> bool:
        """Check if device is available for connection"""
        try:
            _LOGGER.debug(f"Checking availability of device {self.address}")
            
            # Try to discover the specific device
            discovered = await BleakScanner.discover(timeout=5.0)
            
            for device in discovered:
                if device.address.upper() == self.address.upper():
                    _LOGGER.info(f"✅ Device {self.address} is available and advertising")
                    return True
                    
            _LOGGER.warning(f"⚠️ Device {self.address} not found in scan")
            return False
            
        except Exception as e:
            _LOGGER.error(f"Availability check failed: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to the Renogy device using cyrils/renogy-bt method with improved connection management"""
        if self._is_connected:
            return True

        self._ble_device = await BleakScanner.find_device_by_address(self.address, timeout=10.0)
        
        if not self._ble_device:
            _LOGGER.warning(f"Renogy device {self.address} not found, will retry.")
            return False

        self.name = self._ble_device.name or self.address
        self._supports_esphome_proxy = self._detect_esphome_proxy()

        try:
            _LOGGER.info(f"🔗 Connecting to Renogy device: {self.name} ({self.address})")
            
            # Ensure any existing connection is properly closed first
            if hasattr(self, 'client') and self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            # Use shorter timeout for connection attempts to avoid blocking
            connection_timeout = min(DEFAULT_CONNECT_TIMEOUT, 10.0)
            
            # Direct connection without pairing (cyrils method)
            self.client = BleakClient(self._ble_device, timeout=connection_timeout)
            
            # Retry connection with exponential backoff for connection slot issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.client.connect()
                    break
                except Exception as e:
                    if "connection slot" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        _LOGGER.warning(f"Connection slot unavailable, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            if self.client.is_connected:
                _LOGGER.info(f"✅ Successfully connected to {self.address}")
                
                # Discover services
                services = await self.client.get_services()
                _LOGGER.debug(f"Available services: {[str(s.uuid) for s in services]}")
                
                # Find Renogy communication characteristics
                tx_char = None
                rx_char = None
                
                for service in services:
                    for char in service.characteristics:
                        if char.uuid.lower() == RENOGY_TX_CHAR_UUID.lower():
                            tx_char = char
                            _LOGGER.debug(f"Found TX characteristic: {char.uuid}")
                        elif char.uuid.lower() == RENOGY_RX_CHAR_UUID.lower():
                            rx_char = char
                            _LOGGER.debug(f"Found RX characteristic: {char.uuid}")
                
                if tx_char and rx_char:
                    # Enable notifications for data reception
                    await self.client.start_notify(rx_char, self._notification_handler)
                    _LOGGER.info("📡 Notifications enabled for data reception")
                    
                    self._is_connected = True
                    self._connection_attempts = 0  # Reset on successful connection
                    return True
                else:
                    _LOGGER.error("❌ Required Renogy characteristics not found")
                    await self.client.disconnect()
                    return False
            else:
                _LOGGER.error(f"❌ Failed to establish connection to {self.address}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            self._connection_attempts += 1
            
            # Clean up failed connection
            if hasattr(self, 'client') and self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            return False
    
    def _notification_handler(self, sender, data: bytearray):
        """Handle notifications from Renogy device, buffering data until a complete frame is received."""
        _LOGGER.debug(f"📨 Notification chunk received: {data.hex()}")
        self._buffer.extend(data)
        _LOGGER.debug(f"Buffer content: {self._buffer.hex()}")

        # Process all complete frames in the buffer
        while True:
            frame = self._find_complete_frame()
            if frame:
                _LOGGER.info(f"✅ Complete frame found in buffer: {frame.hex()}")
                self._process_modbus_response(frame)
            else:
                break  # No more complete frames in the buffer

    def _find_complete_frame(self) -> Optional[bytearray]:
        """
        Check the buffer for a complete Modbus frame.
        A valid frame is: [0xFF, 0x03, length, ...data..., checksum_high, checksum_low]
        Returns the frame if found, and removes it from the buffer. Otherwise returns None.
        """
        # Look for the start of a frame (0xFF)
        start_index = self._buffer.find(b'\xff')
        if start_index == -1:
            # If no start byte, the buffer is invalid. Clear it.
            if len(self._buffer) > 0:
                _LOGGER.warning(f"Buffer contains invalid data without a start byte. Clearing: {self._buffer.hex()}")
                self._buffer.clear()
            return None
        
        # If there's data before the start byte, discard it.
        if start_index > 0:
            _LOGGER.warning(f"Discarding {start_index} bytes of invalid data from start of buffer: {self._buffer[:start_index].hex()}")
            self._buffer = self._buffer[start_index:]
        
        # We need at least 3 bytes for header (ID, Func, Len)
        if len(self._buffer) < 3:
            _LOGGER.debug("Buffer has less than 3 bytes, waiting for more data.")
            return None

        # Check for function code 0x03 (read) or 0x83 (read exception)
        if self._buffer[1] not in [0x03, 0x83]:
            # This is not a response frame we are looking for. It could be noise or an unsupported command response.
            _LOGGER.warning(f"Invalid function code {self._buffer[1]:02x} received. Discarding the first byte and retrying.")
            self._buffer = self._buffer[1:]
            return None # Restart the search for a valid frame

        # Handle Modbus exception response (e.g., ff8305e0c3)
        if self._buffer[1] == 0x83:
            # Exception frame length is typically 5 bytes (ID, Func, ErrCode, CRC_H, CRC_L)
            if len(self._buffer) >= 5:
                exception_frame = self._buffer[:5]
                self._buffer = self._buffer[5:]
                _LOGGER.warning(f"Modbus Exception received and discarded: {exception_frame.hex()}")
                return None # The frame is "handled" by being discarded, restart search
            else:
                # Not enough data for a full exception frame yet
                return None

        # This should be a data frame (0x03)
        payload_len = self._buffer[2]
        frame_len = 3 + payload_len + 2  # Header (3) + Payload + CRC (2)

        if len(self._buffer) >= frame_len:
            # We have a full frame
            frame = self._buffer[:frame_len]
            self._buffer = self._buffer[frame_len:] # Keep the rest of the buffer

            # Validate checksum before returning the frame
            expected_crc = struct.unpack('>H', frame[-2:])[0]
            calculated_crc = self._calculate_crc16(frame[:-2])
            
            if expected_crc == calculated_crc:
                return frame
            else:
                _LOGGER.error(f"CRC Checksum mismatch! Expected: {expected_crc:04x}, Calculated: {calculated_crc:04x}. Discarding frame: {frame.hex()}")
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
            # The model info is smaller (8 regs * 2 bytes/reg = 16 bytes)
            if data_length > 20: # Likely the main data block
                _LOGGER.debug(f"Processing as real-time data block (length {data_length})")
                registers = []
                for i in range(0, len(payload), 2):
                    if i + 1 < len(payload):
                        value = struct.unpack('>H', payload[i:i+2])[0]
                        registers.append(value)
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
                val = registers[index]
                if signed:
                    # Handle signed 16-bit integers
                    if val & (1 << 15):
                        val -= (1 << 16)
                return val * scale

            def get_val_u32(index, scale=1.0):
                """Safely get a 32-bit unsigned value from two registers."""
                if index + 1 < len(registers):
                    val = (registers[index + 1] << 16) + registers[index]
                    return val * scale
                return None

            # Unpack data using the offsets from RenogyRegisters
            self._last_data.update({
                'battery_soc': get_val(RenogyRegisters.BATTERY_SOC),
                'battery_voltage': get_val(RenogyRegisters.BATTERY_VOLTAGE, 0.1),
                'battery_current': get_val(RenogyRegisters.BATTERY_CURRENT_RAW, 0.01), # Needs verification if it's combined
                'solar_voltage': get_val(RenogyRegisters.SOLAR_VOLTAGE, 0.1),
                'solar_current': get_val(RenogyRegisters.SOLAR_CURRENT, 0.01),
                'solar_power': get_val(RenogyRegisters.SOLAR_POWER),
                'load_voltage': get_val(RenogyRegisters.LOAD_VOLTAGE, 0.1),
                'load_current': get_val(RenogyRegisters.LOAD_CURRENT, 0.01),
                'load_power': get_val(RenogyRegisters.LOAD_POWER),
                'battery_temp': get_val(RenogyRegisters.BATTERY_TEMP, 1.0, signed=True), # Assuming signed
                'controller_temp': get_val(RenogyRegisters.CONTROLLER_TEMP, 1.0, signed=True), # Assuming signed
                'daily_power_generation': get_val(RenogyRegisters.POWER_GENERATION_TODAY), # Wh
                'daily_power_consumption': get_val(RenogyRegisters.POWER_CONSUMPTION_TODAY), # Wh
                'charging_amp_hours_today': get_val(RenogyRegisters.CHARGING_AMP_HOURS_TODAY),
                'discharging_amp_hours_today': get_val(RenogyRegisters.DISCHARGING_AMP_HOURS_TODAY),
                'power_generation_total': get_val_u32(RenogyRegisters.TOTAL_POWER_GENERATED, 0.001), # kWh
                'last_update': datetime.now().isoformat(),
                'connection_status': 'connected',
            })
            
            _LOGGER.debug(f"Updated device data: {self._last_data}")
                
        except IndexError:
            _LOGGER.error("Index error while parsing register data. The data block may be smaller than expected.")
        except Exception as e:
            _LOGGER.error(f"Error updating data from registers: {e}")
    
    async def read_device_info(self) -> dict:
        """Read static device information like model number."""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected to device.")
            return {}
        
        try:
            if self._last_data.get('model_number') and self._last_data.get('model_number') != 'Unknown':
                 return {'model_number': self._last_data.get('model_number')}

            services = await self.client.get_services()
            tx_char = self.get_characteristic(services, RENOGY_TX_CHAR_UUID)
            if not tx_char:
                _LOGGER.error("TX characteristic not found for device info.")
                return {}

            command = self.create_modbus_command(self.device_id, 0x03, RenogyRegisters.MODEL, 8)
            
            self._new_data_event.clear()
            await self.client.write_gatt_char(tx_char, command)
            await asyncio.wait_for(self._new_data_event.wait(), timeout=5.0) 

            if 'model_number' in self._last_data:
                 return {'model_number': self._last_data.get('model_number')}
            return {"model_number": "RNG-CTRL-RVR40"}

        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout waiting for device info response.")
            return {}
        except Exception as e:
            _LOGGER.error(f"Error reading device info: {e}")
            return {}

    async def read_realtime_data(self) -> bool:
        """Read the main block of real-time sensor data."""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected to device for real-time data.")
            return False

        try:
            services = await self.client.get_services()
            tx_char = self.get_characteristic(services, RENOGY_TX_CHAR_UUID)
            if not tx_char:
                _LOGGER.error("TX characteristic not found for real-time data.")
                return False
            
            command = self.create_modbus_command(
                self.device_id, 
                0x03, 
                RenogyRegisters.READ_BLOCK_START, 
                RenogyRegisters.READ_BLOCK_SIZE
            )

            self._buffer.clear()
            self._new_data_event.clear()
            await self.client.write_gatt_char(tx_char, command)
            
            await asyncio.wait_for(self._new_data_event.wait(), timeout=5.0)
            
            return 'battery_soc' in self._last_data

        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout waiting for real-time data response.")
            return False
        except Exception as e:
            _LOGGER.error(f"Error reading real-time device data: {e}")
            return False

    def create_modbus_command(self, device_id: int, function_code: int, start_register: int, num_registers: int) -> bytearray:
        """Create a Modbus RTU command."""
        command = bytearray([
            device_id,
            function_code,
            (start_register >> 8) & 0xFF,
            start_register & 0xFF,
            (num_registers >> 8) & 0xFF,
            num_registers & 0xFF
        ])
        crc = self._calculate_crc16(command)
        command.extend([crc & 0xFF, (crc >> 8) & 0xFF])
        _LOGGER.debug(f"➡️  Sending Modbus command: {command.hex()}")
        return command

    def _calculate_crc16(self, data: bytearray) -> int:
        """Calculate Modbus CRC16 checksum"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def get_characteristic(self, services, uuid):
        """Helper to find a characteristic by UUID."""
        for service in services:
            for char in service.characteristics:
                if char.uuid.lower() == uuid.lower():
                    return char
        return None

    async def get_data(self) -> Dict[str, Any]:
        """
        Main method to get all data from the device.
        Connects if necessary, reads device info once, then polls real-time data.
        """
        if not self.client or not self.client.is_connected:
            _LOGGER.info("Client not connected, attempting to connect...")
            if not await self.connect():
                _LOGGER.warning("Could not connect to device, returning offline data.")
                return self._get_offline_data()

        # Fetch model number only if we don't have it
        if 'model_number' not in self._last_data:
             model_info = await self.read_device_info()
             if model_info:
                 self._last_data.update(model_info)
        
        # Fetch real-time sensor data
        await self.read_realtime_data()

        if not self._last_data:
            _LOGGER.warning("No data received from device, returning offline data.")
            return self._get_offline_data()

        return self._last_data

    def _get_offline_data(self) -> Dict[str, Any]:
        """Return a dictionary with offline status for all sensors."""
        _LOGGER.debug("Returning offline data structure.")
        offline_data: Dict[str, Any] = {
            desc.key: None for desc in DEVICE_SENSORS
        }
        offline_data['connection_status'] = 'disconnected'
        offline_data['last_update'] = datetime.now().isoformat()
        return offline_data
    
    async def disconnect(self):
        """Disconnect from the device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self._is_connected = False
        _LOGGER.info(f"Disconnected from {self.address}")
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'client') and self.client:
            try:
                asyncio.create_task(self.disconnect())
            except:
                pass 