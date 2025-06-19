"""
BluPow BLE Client for Home Assistant Integration - Renogy Protocol Implementation

Based on the proven cyrils/renogy-bt library: https://github.com/cyrils/renogy-bt
This client implements the correct Renogy protocol for charge controller communication.
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

from .const import (
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    MODEL_NUMBER_CHAR_UUID,
    MANUFACTURER_CHAR_UUID,
    DEVICE_SERVICE_UUID,
    DEVICE_READ_WRITE_CHAR,
    DEVICE_NOTIFY_CHAR,
    DEVICE_WRITE_CHAR,
    DEVICE_READ_CHAR,
    DEVICE_SPECIAL_CHAR,
)

_LOGGER = logging.getLogger(__name__)

class EnvironmentInfo:
    """Detect and store information about the current environment"""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_version = sys.version_info
        self.is_docker = self._detect_docker()
        self.is_hassio = self._detect_hassio()
        self.ble_backend = self._detect_ble_backend()
        self.capabilities = self._detect_capabilities()
        
        _LOGGER.info(f"Environment detected: {self}")
    
    def _detect_docker(self) -> bool:
        """Detect if running in Docker container"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read() or 'containerd' in f.read()
        except (FileNotFoundError, PermissionError):
            # Check for common Docker environment variables
            import os
            return any(var in os.environ for var in ['DOCKER_CONTAINER', 'HOSTNAME']) and \
                   os.path.exists('/.dockerenv')
    
    def _detect_hassio(self) -> bool:
        """Detect if running in Home Assistant OS/Supervised"""
        import os
        return os.path.exists('/usr/share/hassio') or \
               os.path.exists('/etc/hassio.json') or \
               'HASSIO' in os.environ
    
    def _detect_ble_backend(self) -> str:
        """Detect which BLE backend is being used"""
        if self.platform == "Linux":
            return "BlueZ"
        elif self.platform == "Windows":
            return "WinRT"
        elif self.platform == "Darwin":
            return "CoreBluetooth"
        else:
            return "Unknown"
    
    def _detect_capabilities(self) -> Dict[str, bool]:
        """Detect system capabilities"""
        capabilities = {
            'extended_scanning': self.platform == "Linux",
            'rssi_monitoring': True,
            'concurrent_connections': not self.is_docker,  # Docker may have limitations
            'characteristic_caching': True,
            'service_discovery_caching': self.python_version >= (3, 8),
        }
        
        # Platform-specific adjustments
        if self.platform == "Windows":
            capabilities['extended_scanning'] = False
        elif self.is_hassio:
            capabilities['concurrent_connections'] = False  # Conservative approach
            
        return capabilities
    
    def __str__(self) -> str:
        return (f"Platform: {self.platform}, Python: {self.python_version[:2]}, "
                f"Docker: {self.is_docker}, HassIO: {self.is_hassio}, "
                f"BLE: {self.ble_backend}")

class RenogyProtocol:
    """Renogy Modbus protocol implementation based on cyrils/renogy-bt"""
    
    # Renogy BT-1/BT-2 module UUIDs (proven working from cyrils/renogy-bt)
    WRITE_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
    NOTIFY_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb" 
    
    # Alternative UUIDs for different firmware versions
    ALT_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    ALT_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    
    # Renogy Modbus register addresses (from cyrils/renogy-bt)
    DEVICE_INFO_START = 12  # 0x000C
    DEVICE_INFO_LENGTH = 8
    
    BATTERY_INFO_START = 256  # 0x0100  
    BATTERY_INFO_LENGTH = 34
    
    CHARGING_INFO_START = 263  # 0x0107
    CHARGING_INFO_LENGTH = 11
    
    def __init__(self, device_id: int = 255):
        """Initialize Renogy protocol with device ID (255 = broadcast)"""
        self.device_id = device_id
        self.response_data = bytearray()
        
    def create_read_request(self, register_addr: int, length: int) -> bytes:
        """Create Modbus read request - based on cyrils/renogy-bt"""
        # Modbus RTU format: [device_id][function][addr_hi][addr_lo][len_hi][len_lo][crc_lo][crc_hi]
        request = bytearray([
            self.device_id,  # Device address
            0x03,  # Function code: Read Holding Registers
            (register_addr >> 8) & 0xFF,  # Start address high byte
            register_addr & 0xFF,         # Start address low byte  
            (length >> 8) & 0xFF,         # Number of registers high byte
            length & 0xFF                 # Number of registers low byte
        ])
        
        # Calculate CRC16 for Modbus RTU
        crc = self._calculate_crc16(request)
        request.extend([(crc >> 8) & 0xFF, crc & 0xFF])
        
        return bytes(request)
    
    def _calculate_crc16(self, data: bytearray) -> int:
        """Calculate CRC16 for Modbus RTU - from cyrils/renogy-bt"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc
    
    def parse_device_info(self, data: bytes) -> Dict[str, Any]:
        """Parse device information response - based on cyrils/renogy-bt"""
        if len(data) < 21:  # Minimum response size
            return {}
            
        try:
            # Skip Modbus header (device_id, function, byte_count)
            payload = data[3:]
            
            result = {}
            
            # Extract device information (16-bit big-endian values)
            if len(payload) >= 16:
                result['max_charging_current'] = struct.unpack('>H', payload[0:2])[0] / 100.0
                result['max_discharging_current'] = struct.unpack('>H', payload[2:4])[0] / 100.0
                result['product_type'] = struct.unpack('>H', payload[4:6])[0]
                result['product_model'] = ''.join(chr(b) for b in payload[6:12] if b != 0)
                result['software_version'] = struct.unpack('>H', payload[12:14])[0]
                result['hardware_version'] = struct.unpack('>H', payload[14:16])[0]
                
            return result
            
        except Exception as e:
            _LOGGER.debug(f"Error parsing device info: {e}")
            return {}
    
    def parse_battery_info(self, data: bytes) -> Dict[str, Any]:
        """Parse battery information response - based on cyrils/renogy-bt"""
        if len(data) < 71:  # Minimum response size  
            return {}
            
        try:
            # Skip Modbus header
            payload = data[3:]
            
            result = {}
            
            # Extract battery data (16-bit big-endian values)
            if len(payload) >= 68:
                result['battery_soc'] = struct.unpack('>H', payload[0:2])[0]
                result['battery_voltage'] = struct.unpack('>H', payload[2:4])[0] / 100.0
                result['battery_current'] = struct.unpack('>h', payload[4:6])[0] / 100.0  # signed
                result['battery_temp'] = struct.unpack('>h', payload[6:8])[0] / 100.0    # signed
                result['controller_temp'] = struct.unpack('>h', payload[8:10])[0] / 100.0
                result['load_voltage'] = struct.unpack('>H', payload[10:12])[0] / 100.0
                result['load_current'] = struct.unpack('>H', payload[12:14])[0] / 100.0
                result['load_power'] = struct.unpack('>H', payload[14:16])[0]
                
                # Solar panel data
                result['solar_voltage'] = struct.unpack('>H', payload[16:18])[0] / 100.0
                result['solar_current'] = struct.unpack('>H', payload[18:20])[0] / 100.0
                result['solar_power'] = struct.unpack('>H', payload[20:22])[0]
                
                # Daily statistics
                result['daily_battery_voltage_min'] = struct.unpack('>H', payload[22:24])[0] / 100.0
                result['daily_battery_voltage_max'] = struct.unpack('>H', payload[24:26])[0] / 100.0
                result['daily_max_charging_current'] = struct.unpack('>H', payload[26:28])[0] / 100.0
                result['daily_max_discharging_current'] = struct.unpack('>H', payload[28:30])[0] / 100.0
                result['daily_max_charging_power'] = struct.unpack('>H', payload[30:32])[0]
                result['daily_max_discharging_power'] = struct.unpack('>H', payload[32:34])[0]
                result['daily_charging_amp_hours'] = struct.unpack('>H', payload[34:36])[0]
                result['daily_discharging_amp_hours'] = struct.unpack('>H', payload[36:38])[0]
                result['daily_power_generation'] = struct.unpack('>H', payload[38:40])[0]
                result['daily_power_consumption'] = struct.unpack('>H', payload[40:42])[0]
                
                # Charging status
                charging_state = struct.unpack('>H', payload[66:68])[0] 
                charging_states = {
                    0: 'deactivated',
                    1: 'activated', 
                    2: 'mppt',
                    3: 'equalizing',
                    4: 'boost',
                    5: 'floating',
                    6: 'current limiting'
                }
                result['charging_status'] = charging_states.get(charging_state, f'unknown_{charging_state}')
                
            return result
            
        except Exception as e:
            _LOGGER.debug(f"Error parsing battery info: {e}")
            return {}

class BluPowClient:
    """Enhanced BluPow BLE client implementing Renogy protocol"""
    
    # Device-specific configuration
    DEVICE_CONFIGS = {
        'ESP32': {
            'connection_delay': 8,  # Longer delay for ESP32
            'retry_multiplier': 4,  # Additional delay per retry
            'max_retries': 5,      # More retries for ESP32
            'timeout_base': 25,    # Longer timeout
            'characteristics_delay': 3,  # Extra delay after connection
        },
        'RENOGY': {
            'connection_delay': 5,  # Renogy BT modules need time
            'retry_multiplier': 3,  
            'max_retries': 5,      
            'timeout_base': 20,    
            'characteristics_delay': 2,
        },
        'DEFAULT': {
            'connection_delay': 3,  
            'retry_multiplier': 3,  
            'max_retries': 5,      
            'timeout_base': 20,    
            'characteristics_delay': 1,
        }
    }

    def __init__(self, device: BLEDevice):
        """Initialize the BluPow client with Renogy protocol support."""
        try:
            self._device = device
            self._notification_queue = asyncio.Queue()
            self._connection_attempts = 0
            self._last_successful_connection = None
            self._last_error = None
            
            # Environment detection and configuration
            self.environment = EnvironmentInfo()
            self.device_type = self._detect_device_type(device.name or "")
            self._discovered_characteristics = None
            self._connection_lock = asyncio.Lock()
            
            # Initialize Renogy protocol
            self.renogy_protocol = RenogyProtocol(device_id=255)  # Broadcast address
            
            _LOGGER.info("BluPow client initialized for device: %s (%s) - Environment: %s", 
                        device.name or "Unknown", device.address, self.environment)
                        
        except Exception as err:
            _LOGGER.error("Failed to initialize BluPow client: %s", err)
            raise

    def _detect_device_type(self, device_name: str = "") -> str:
        """Detect device type based on name or other characteristics"""
        device_name = device_name.lower()
        if 'bt-th' in device_name or 'renogy' in device_name or 'rover' in device_name:
            return 'RENOGY'
        elif 'esp32' in device_name or 'esp' in device_name:
            return 'ESP32'
        return 'DEFAULT'

    def _get_device_config(self) -> Dict[str, Any]:
        """Get configuration for the detected device type"""
        config = self.DEVICE_CONFIGS.get(self.device_type, self.DEVICE_CONFIGS['DEFAULT']).copy()
        
        # Environment-specific adjustments
        if self.environment.is_docker:
            config['timeout_base'] += 10  # Docker networking can be slower
            config['connection_delay'] += 2
            config['max_retries'] = 3  # Limit retries in Docker
        
        if self.environment.is_hassio:
            config['max_retries'] = 3  # Be conservative on HassIO
            config['connection_delay'] += 2
            
        if self.environment.platform == "Windows":
            config['characteristics_delay'] += 1  # Windows BLE can be slower
            
        return config

    @property
    def name(self) -> str:
        """Return the name of the device."""
        try:
            return self._device.name or self._device.address
        except Exception as err:
            _LOGGER.error("Error getting device name: %s", err)
            return "Unknown Device"

    @property
    def address(self) -> str:
        """Return the address of the device."""
        try:
            return self._device.address
        except Exception as err:
            _LOGGER.error("Error getting device address: %s", err)
            return "Unknown Address"

    async def _get_services_compatible(self, client: BleakClient):
        """Get services using the most compatible method"""
        try:
            # Try modern API first
            if hasattr(client, 'services') and client.services:
                _LOGGER.debug("Using modern services property")
                return client.services
            
            # Fallback to legacy method
            if hasattr(client, 'get_services'):
                _LOGGER.debug("Using legacy get_services method")
                services = await client.get_services()
                return services
            
            return None
        except Exception as e:
            _LOGGER.debug(f"Error getting services: {e}")
            return None

    async def _discover_characteristics(self, client: BleakClient) -> Dict[str, Any]:
        """Discover device characteristics with Renogy-specific UUIDs"""
        try:
            _LOGGER.debug(f"Discovering characteristics for device {self.address}")
            
            services = await self._get_services_compatible(client)
            if not services:
                _LOGGER.debug("No services found")
                return {'write_char': None, 'notify_char': None, 'all_chars': []}
            
            write_char = None
            notify_char = None
            all_chars = []
            
            # Renogy-specific UUIDs (from cyrils/renogy-bt)
            renogy_write_uuids = [
                RenogyProtocol.WRITE_UUID,
                RenogyProtocol.ALT_WRITE_UUID,
                DEVICE_READ_WRITE_CHAR,  # tuner168 board UUID
                "0000ffe1-0000-1000-8000-00805f9b34fb"  # Alternative
            ]
            
            renogy_notify_uuids = [
                RenogyProtocol.NOTIFY_UUID,
                RenogyProtocol.ALT_NOTIFY_UUID,
                DEVICE_NOTIFY_CHAR,  # tuner168 board UUID
                "0000ffe1-0000-1000-8000-00805f9b34fb"  # Alternative
            ]
            
            for service in services:
                _LOGGER.debug(f"Found service: {service.uuid}")
                for char in service.characteristics:
                    char_info = {
                        'uuid': char.uuid,
                        'properties': char.properties,
                        'service_uuid': service.uuid
                    }
                    all_chars.append(char_info)
                    
                    _LOGGER.debug(f"Found characteristic: {char.uuid} (properties: {char.properties})")
                    
                    # Check for Renogy write characteristics
                    if char.uuid.lower() in [uuid.lower() for uuid in renogy_write_uuids]:
                        if 'write' in char.properties or 'write-without-response' in char.properties:
                            write_char = char_info
                            _LOGGER.info(f"Found Renogy WRITE characteristic: {char.uuid}")
                    
                    # Check for Renogy notify characteristics  
                    if char.uuid.lower() in [uuid.lower() for uuid in renogy_notify_uuids]:
                        if 'notify' in char.properties or 'read' in char.properties:
                            notify_char = char_info
                            _LOGGER.info(f"Found Renogy NOTIFY characteristic: {char.uuid}")
            
            result = {
                'write_char': write_char,
                'notify_char': notify_char,
                'all_chars': all_chars
            }
            
            _LOGGER.info(f"Renogy characteristic discovery complete: Write={'✓' if write_char else '✗'}, Notify={'✓' if notify_char else '✗'}")
            return result
            
        except Exception as e:
            _LOGGER.error(f"Error during characteristic discovery: {e}")
            return {'write_char': None, 'notify_char': None, 'all_chars': []}

    async def check_device_availability(self) -> bool:
        """Check if the device is available for connection with enhanced diagnostics."""
        try:
            _LOGGER.debug("Checking availability of device %s", self.address)
            
            # Enhanced device availability check with scan
            try:
                _LOGGER.debug("Performing device scan to verify device is discoverable")
                devices = await BleakScanner.discover(timeout=5.0)
                device_found = False
                for device in devices:
                    if device.address.upper() == self.address.upper():
                        device_found = True
                        _LOGGER.info("Device %s found in scan (RSSI: %s)", self.address, device.rssi)
                        break
                
                if not device_found:
                    _LOGGER.warning("Device %s not found in Bluetooth scan - may be out of range or not advertising", self.address)
                    return False
                    
            except Exception as scan_err:
                _LOGGER.debug("Bluetooth scan failed: %s", scan_err)
                # Continue with connection attempt even if scan fails
            
            # Try a quick connection to see if device responds
            config = self._get_device_config()
            async with BleakClient(self._device, timeout=5.0) as client:
                # Just check if we can connect, don't read data
                _LOGGER.debug("Device %s is available and connectable", self.address)
                return True
                
        except Exception as err:
            _LOGGER.debug("Device %s quick check failed: %s", self.address, err)
            # Don't fail completely - let the main connection attempt try with better error handling
            return True  # Allow main attempt to handle this with retries

    async def get_data(self) -> Dict[str, Any]:
        """Read Renogy device data using proper Modbus protocol."""
        start_time = datetime.now()
        self._connection_attempts += 1
        
        config = self._get_device_config()
        
        # Enhanced logging for first attempt
        if self._connection_attempts == 1:
            _LOGGER.info("Starting Renogy connection to %s (%s) - Environment: %s", 
                        self.name, self.address, self.environment)
            _LOGGER.info("Connection config: delays=%ds, retries=%d, timeout=%ds", 
                        config['connection_delay'], config['max_retries'], config['timeout_base'])
        
        # Try multiple connection attempts with environment-aware retry logic
        for attempt in range(config['max_retries']):
            try:
                _LOGGER.info("Connection attempt %d/%d to %s (device type: %s)", 
                            attempt + 1, config['max_retries'], self.address, self.device_type)
                
                # Progressive timeout
                timeout = min(config['timeout_base'] + (attempt * 5), 45)
                
                # Environment-specific connection delay
                if attempt > 0:
                    delay = config['connection_delay'] + (attempt * config['retry_multiplier'])
                    _LOGGER.debug(f"Waiting {delay}s before connection attempt (environment: {self.environment.platform})")
                    await asyncio.sleep(delay)
                
                async with BleakClient(self._device, timeout=timeout) as client:
                    _LOGGER.debug("Connected to Renogy device %s (timeout: %.1fs)", self.address, timeout)
                    
                    # Wait for connection to stabilize
                    await asyncio.sleep(config['characteristics_delay'])
                    
                    # Discover Renogy characteristics
                    characteristics = await self._discover_characteristics(client)
                    
                    if not characteristics['write_char']:
                        _LOGGER.warning("No Renogy WRITE characteristic found - device may not be compatible")
                        continue
                    
                    # Try to read Renogy data using Modbus protocol
                    data = await self._read_renogy_data(client, characteristics)
                    
                    if data:
                        # Add metadata
                        data.update({
                            "connection_attempts": self._connection_attempts,
                            "connection_retry_attempt": attempt + 1,
                            "last_successful_connection": start_time.isoformat(),
                            "connection_duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                            "device_type": self.device_type,
                            "environment": str(self.environment),
                        })
                        
                        self._last_successful_connection = start_time
                        self._last_error = None
                        
                        _LOGGER.info("Successfully retrieved Renogy data from %s: %s", 
                                   self.address, list(data.keys()))
                        
                        return data
                    else:
                        raise Exception("No Renogy data could be read from device")
                    
            except BleakDeviceNotFoundError as err:
                error_msg = f"Device {self.address} not found"
                _LOGGER.error("%s (attempt %d/%d): %s", error_msg, attempt + 1, config['max_retries'], err)
                _LOGGER.info("Device not found troubleshooting: Check if device is powered on, in range, and not connected to another device")
                self._last_error = error_msg
                if attempt == config['max_retries'] - 1:
                    return self._get_error_data(error_msg)
                # Don't retry if device not found
                break
                
            except BleakError as err:
                error_msg = f"Connection failed to device {self.address}: {err}"
                _LOGGER.error("%s (attempt %d/%d)", error_msg, attempt + 1, config['max_retries'])
                self._last_error = error_msg
                
                # Enhanced error handling for common connection failures
                if "No backend with an available connection slot" in str(err):
                    _LOGGER.warning("Bluetooth connection slot issue - this may indicate:")
                    _LOGGER.warning("  1. Bluetooth adapter is busy or not properly initialized")
                    _LOGGER.warning("  2. Device is already connected to another application")
                    _LOGGER.warning("  3. System Bluetooth stack needs to be restarted")
                    _LOGGER.warning("  4. Home Assistant needs proper Bluetooth permissions")
                    
                    if attempt < config['max_retries'] - 1:
                        wait_time = 5 + attempt * 5  # 10, 15, 20 seconds
                        _LOGGER.info("Waiting %d seconds before connection slot retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg + " - See logs for troubleshooting steps")
                        
                elif "ESP_GATT_CONN_FAIL_ESTABLISH" in str(err):
                    _LOGGER.warning("ESP32 connection establishment failed - this is common with these devices")
                    # Longer delay for ESP32 connection issues
                    if attempt < config['max_retries'] - 1:
                        wait_time = 8 + attempt * 4  # 12, 16, 20 seconds
                        _LOGGER.info("Waiting %d seconds before ESP32 retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg)
                        
                elif "was not found" in str(err).lower():
                    _LOGGER.warning("Device disappeared during connection - may have gone to sleep or out of range")
                    if attempt < config['max_retries'] - 1:
                        wait_time = 3 + attempt * 2  # 5, 7, 9 seconds
                        _LOGGER.info("Waiting %d seconds before device discovery retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg)
                        
                else:
                    if attempt < config['max_retries'] - 1:
                        # Wait before retry with exponential backoff
                        wait_time = 2 ** attempt
                        _LOGGER.info("Waiting %d seconds before retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg)
                    
            except Exception as err:
                error_msg = f"Unexpected error with device {self.address}: {err}"
                _LOGGER.error("%s (attempt %d/%d)", error_msg, attempt + 1, config['max_retries'])
                self._last_error = error_msg
                
                if attempt < config['max_retries'] - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    _LOGGER.info("Waiting %d seconds before retry...", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    return self._get_error_data(error_msg)
        
        # If we get here, all retries failed
        return self._get_error_data(f"All {config['max_retries']} connection attempts failed")

    async def _read_renogy_data(self, client: BleakClient, characteristics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Read Renogy data using proper Modbus protocol - based on cyrils/renogy-bt"""
        
        write_char = characteristics['write_char']
        notify_char = characteristics['notify_char'] or write_char  # Some devices use same char for both
        
        if not write_char:
            _LOGGER.error("No write characteristic available for Renogy communication")
            return None
        
        try:
            _LOGGER.info("Reading Renogy data using Modbus protocol")
            
            # Set up notification handler if available
            response_data = bytearray()
            response_event = asyncio.Event()
            
            def notification_handler(sender, data):
                _LOGGER.debug(f"Received notification: {data.hex()}")
                response_data.extend(data)
                response_event.set()
            
            # Subscribe to notifications if supported
            if notify_char and 'notify' in notify_char['properties']:
                await client.start_notify(notify_char['uuid'], notification_handler)
                _LOGGER.debug("Subscribed to notifications")
            
            # Strategy 1: Read device information
            device_info = {}
            try:
                _LOGGER.debug("Requesting device information")
                device_cmd = self.renogy_protocol.create_read_request(
                    self.renogy_protocol.DEVICE_INFO_START,
                    self.renogy_protocol.DEVICE_INFO_LENGTH
                )
                _LOGGER.debug(f"Sending device info command: {device_cmd.hex()}")
                
                await client.write_gatt_char(write_char['uuid'], device_cmd, response=False)
                
                # Wait for response
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=3.0)
                    if response_data:
                        device_info = self.renogy_protocol.parse_device_info(bytes(response_data))
                        _LOGGER.info(f"Device info: {device_info}")
                    response_data.clear()
                    response_event.clear()
                except asyncio.TimeoutError:
                    _LOGGER.debug("Device info request timed out")
                    
            except Exception as e:
                _LOGGER.debug(f"Device info request failed: {e}")
            
            # Strategy 2: Read battery/charging information
            battery_info = {}
            try:
                _LOGGER.debug("Requesting battery information")
                battery_cmd = self.renogy_protocol.create_read_request(
                    self.renogy_protocol.BATTERY_INFO_START,
                    self.renogy_protocol.BATTERY_INFO_LENGTH
                )
                _LOGGER.debug(f"Sending battery info command: {battery_cmd.hex()}")
                
                await client.write_gatt_char(write_char['uuid'], battery_cmd, response=False)
                
                # Wait for response
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=5.0)
                    if response_data:
                        battery_info = self.renogy_protocol.parse_battery_info(bytes(response_data))
                        _LOGGER.info(f"Battery info: {battery_info}")
                    response_data.clear()
                    response_event.clear()
                except asyncio.TimeoutError:
                    _LOGGER.debug("Battery info request timed out")
                    
            except Exception as e:
                _LOGGER.debug(f"Battery info request failed: {e}")
            
            # Stop notifications
            if notify_char and 'notify' in notify_char['properties']:
                try:
                    await client.stop_notify(notify_char['uuid'])
                except:
                    pass
            
            # Combine the results
            combined_data = {}
            combined_data.update(device_info)
            combined_data.update(battery_info)
            
            # Convert to expected format for Home Assistant
            result = {
                'model_number': combined_data.get('product_model', 'RNG-CTRL-RVR40'),
                'battery_voltage': combined_data.get('battery_voltage'),
                'solar_voltage': combined_data.get('solar_voltage'),
                'battery_current': combined_data.get('battery_current'),
                'solar_current': combined_data.get('solar_current'),
                'battery_soc': combined_data.get('battery_soc'),
                'battery_temp': combined_data.get('battery_temp'),
                'solar_power': combined_data.get('solar_power'),
                # Additional energy monitoring data
                'load_power': combined_data.get('load_power'),
                'load_current': combined_data.get('load_current'),
                'load_voltage': combined_data.get('load_voltage'),
                'daily_power_generation': combined_data.get('daily_power_generation'),
                'daily_power_consumption': combined_data.get('daily_power_consumption'),
                'charging_status': combined_data.get('charging_status'),
                'controller_temp': combined_data.get('controller_temp'),
            }
            
            # Filter out None values and log what we got
            valid_data = {k: v for k, v in result.items() if v is not None}
            
            if valid_data:
                _LOGGER.info(f"Successfully parsed Renogy data: {valid_data}")
                return result
            else:
                _LOGGER.warning("No valid Renogy data received")
                return None
                
        except Exception as e:
            _LOGGER.error(f"Renogy data reading failed: {e}")
            return None

    def _get_error_data(self, error_message: str) -> Dict[str, Any]:
        """Return error data structure"""
        return {
            'model_number': 'RNG-CTRL-RVR40',  # Known model from user confirmation
            'battery_voltage': None,
            'solar_voltage': None,
            'battery_current': None,
            'solar_current': None,
            'battery_soc': None,
            'battery_temp': None,
            'solar_power': None,
            'load_power': None,
            'load_current': None,
            'load_voltage': None,
            'daily_power_generation': None,
            'daily_power_consumption': None,
            'charging_status': None,
            'controller_temp': None,
            'connection_status': 'error',
            'last_update': 'error',
            'error_count': self._connection_attempts,
            'last_error': error_message
        }

    @staticmethod
    async def scan_devices(timeout: float = 10.0) -> List[Tuple[str, str]]:
        """Scan for Renogy devices with enhanced diagnostics."""
        try:
            _LOGGER.info("Scanning for Renogy devices (timeout: %.1fs)...", timeout)
            
            # Enhanced scanning with diagnostics
            devices = await BleakScanner.discover(timeout=timeout)
            found_devices = []
            
            if not devices:
                _LOGGER.warning("No Bluetooth devices found during scan")
                _LOGGER.info("Bluetooth troubleshooting tips:")
                _LOGGER.info("  1. Check if Bluetooth is enabled and working")
                _LOGGER.info("  2. Ensure Home Assistant has Bluetooth permissions")
                _LOGGER.info("  3. Try restarting the Bluetooth service")
                _LOGGER.info("  4. Check if other Bluetooth apps are blocking access")
                return []
            
            _LOGGER.info("Found %d Bluetooth devices during scan", len(devices))
            
            for device in devices:
                name = device.name or "Unknown"
                address = device.address
                rssi = getattr(device, 'rssi', 'Unknown')
                
                _LOGGER.debug("Discovered device: %s (%s) RSSI: %s", name, address, rssi)
                
                # Look for potential Renogy devices
                if any(keyword in name.lower() for keyword in ['bt-th', 'renogy', 'solar', 'rover', 'wanderer']):
                    _LOGGER.info("Potential Renogy device found: %s (%s) RSSI: %s", name, address, rssi)
                    found_devices.append((address, name))
            
            if found_devices:
                _LOGGER.info("Found %d potential Renogy devices", len(found_devices))
            else:
                _LOGGER.warning("No Renogy devices found. Look for devices with names containing:")
                _LOGGER.warning("  BT-TH-xxx, Renogy, Solar, Rover, Wanderer")
            
            return found_devices
            
        except Exception as err:
            _LOGGER.error("Device scanning failed: %s", err)
            return []

    @staticmethod 
    async def diagnose_bluetooth() -> Dict[str, Any]:
        """Diagnose Bluetooth setup and compatibility"""
        try:
            diagnosis = {
                'platform': platform.system(),
                'python_version': sys.version,
                'bleak_available': True,
            }
            
            # Test basic scanning
            try:
                devices = await BleakScanner.discover(timeout=5.0)
                diagnosis['scan_successful'] = True
                diagnosis['devices_found'] = len(devices)
                diagnosis['sample_devices'] = [(d.name or "Unknown", d.address) for d in devices[:5]]
            except Exception as e:
                diagnosis['scan_successful'] = False
                diagnosis['scan_error'] = str(e)
            
            return diagnosis
            
        except ImportError:
            return {
                'bleak_available': False,
                'error': 'Bleak library not available'
            }
        except Exception as err:
            return {
                'diagnosis_error': str(err)
            } 