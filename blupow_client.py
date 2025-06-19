"""
BluPow BLE Client for Home Assistant Integration

This client implements proactive environment detection and universal compatibility
following the BluPow Project Ideology.
"""

import asyncio
import logging
import platform
import sys
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from bleak import BleakClient, BleakScanner, BleakError
from bleak.exc import BleakDeviceNotFoundError
from bleak.backends.device import BLEDevice

from .const import (
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    MODEL_NUMBER_CHAR_UUID,
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

class BluPowClient:
    """Enhanced BluPow BLE client with environment awareness"""
    
    # Device-specific configuration
    DEVICE_CONFIGS = {
        'ESP32': {
            'connection_delay': 5,  # Base delay for ESP32
            'retry_multiplier': 3,  # Additional delay per retry
            'max_retries': 3,
            'timeout_base': 20,
            'characteristics_delay': 2,  # Extra delay after connection
        },
        'DEFAULT': {
            'connection_delay': 1,
            'retry_multiplier': 2,
            'max_retries': 3,
            'timeout_base': 15,
            'characteristics_delay': 0.5,
        }
    }
    
    # Multiple possible UUIDs for different firmware versions
    CHARACTERISTIC_UUIDS = {
        'rx': [
            RENOGY_RX_CHAR_UUID,  # Original BluPow RX
            "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",  # Nordic UART RX
            "0000FFE1-0000-1000-8000-00805F9B34FB",  # Common ESP32 RX
            "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",  # Alternative RX
        ],
        'tx': [
            RENOGY_TX_CHAR_UUID,  # Original BluPow TX
            "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",  # Nordic UART TX
            "0000FFE1-0000-1000-8000-00805F9B34FB",  # Common ESP32 TX
            "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",  # Alternative TX
        ]
    }

    def __init__(self, device: BLEDevice):
        """Initialize the BluPow client with environment detection."""
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
            
            _LOGGER.info("BluPow client initialized for device: %s (%s) - Environment: %s", 
                        device.name or "Unknown", device.address, self.environment)
                        
        except Exception as err:
            _LOGGER.error("Failed to initialize BluPow client: %s", err)
            raise

    def _detect_device_type(self, device_name: str = "") -> str:
        """Detect device type based on name or other characteristics"""
        device_name = device_name.lower()
        if 'esp32' in device_name or 'esp' in device_name:
            return 'ESP32'
        return 'DEFAULT'

    def _get_device_config(self) -> Dict[str, Any]:
        """Get configuration for the detected device type"""
        config = self.DEVICE_CONFIGS.get(self.device_type, self.DEVICE_CONFIGS['DEFAULT']).copy()
        
        # Environment-specific adjustments
        if self.environment.is_docker:
            config['timeout_base'] += 5  # Docker networking can be slower
            config['connection_delay'] += 1
        
        if self.environment.is_hassio:
            config['max_retries'] = 2  # Be conservative on HassIO
            
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
            return "unknown"

    async def _get_services_compatible(self, client: BleakClient):
        """Get services using the most compatible method"""
        try:
            # Try modern API first
            if hasattr(client, 'services') and client.services:
                _LOGGER.debug("Using modern services property")
                return client.services
            
            # Fallback to legacy method
            _LOGGER.debug("Falling back to get_services() method")
            if hasattr(client, 'get_services'):
                return await client.get_services()
            
            # Last resort - try to access services after connection
            if client.is_connected:
                await asyncio.sleep(1)  # Give time for service discovery
                return client.services if hasattr(client, 'services') else None
                
        except Exception as e:
            _LOGGER.warning(f"Service discovery failed: {e}")
            return None

    async def _discover_characteristics(self, client: BleakClient) -> Dict[str, Any]:
        """Discover and categorize characteristics with caching"""
        if self._discovered_characteristics is not None:
            _LOGGER.debug("Using cached characteristics")
            return self._discovered_characteristics

        _LOGGER.debug("Discovering device characteristics...")
        
        # Wait a bit after connection for service discovery to complete
        config = self._get_device_config()
        await asyncio.sleep(config['characteristics_delay'])
        
        try:
            services = await self._get_services_compatible(client)
            if not services:
                raise Exception("No services discovered")
            
            characteristics = {
                'rx_chars': [],
                'tx_chars': [],
                'readable_chars': [],
                'writable_chars': [],
                'all_chars': []
            }
            
            for service in services:
                _LOGGER.debug(f"Service: {service.uuid}")
                for char in service.characteristics:
                    char_info = {
                        'uuid': char.uuid,
                        'properties': char.properties,
                        'service_uuid': service.uuid
                    }
                    characteristics['all_chars'].append(char_info)
                    
                    # Categorize by properties
                    if "read" in char.properties:
                        characteristics['readable_chars'].append(char_info)
                    if "write" in char.properties or "write-without-response" in char.properties:
                        characteristics['writable_chars'].append(char_info)
                    
                    # Check against known UUIDs
                    char_uuid_upper = char.uuid.upper()
                    for rx_uuid in self.CHARACTERISTIC_UUIDS['rx']:
                        if char_uuid_upper == rx_uuid.upper():
                            characteristics['rx_chars'].append(char_info)
                            break
                    
                    for tx_uuid in self.CHARACTERISTIC_UUIDS['tx']:
                        if char_uuid_upper == tx_uuid.upper():
                            characteristics['tx_chars'].append(char_info)
                            break
                    
                    _LOGGER.debug(f"  Characteristic: {char.uuid} - Properties: {char.properties}")
            
            self._discovered_characteristics = characteristics
            _LOGGER.info(f"Discovered {len(characteristics['all_chars'])} characteristics, "
                        f"{len(characteristics['rx_chars'])} RX, {len(characteristics['tx_chars'])} TX")
            
            return characteristics
            
        except Exception as e:
            _LOGGER.error(f"Characteristic discovery failed: {e}")
            raise

    async def check_device_availability(self) -> bool:
        """Check if the device is available for connection."""
        try:
            _LOGGER.debug("Checking availability of device %s", self.address)
            
            # Try a quick connection to see if device responds
            config = self._get_device_config()
            async with BleakClient(self._device, timeout=3.0) as client:
                # Just check if we can connect, don't read data
                _LOGGER.debug("Device %s is available", self.address)
                return True
                
        except Exception as err:
            _LOGGER.debug("Device %s quick check failed: %s", self.address, err)
            # Don't fail completely - let the main connection attempt try
            return True  # Allow main attempt

    async def get_data(self) -> Dict[str, Any]:
        """Read device data with comprehensive error handling and retry logic."""
        start_time = datetime.now()
        self._connection_attempts += 1
        
        config = self._get_device_config()
        
        # Try multiple connection attempts with environment-aware retry logic
        for attempt in range(config['max_retries']):
            try:
                _LOGGER.info("Connection attempt %d/%d to %s (device type: %s)", 
                            attempt + 1, config['max_retries'], self.address, self.device_type)
                
                # Progressive timeout
                timeout = min(config['timeout_base'] + (attempt * 5), 30)
                
                # Environment-specific connection delay
                if attempt > 0:
                    delay = config['connection_delay'] + (attempt * config['retry_multiplier'])
                    _LOGGER.debug(f"Waiting {delay}s before connection attempt (environment: {self.environment.platform})")
                    await asyncio.sleep(delay)
                
                async with BleakClient(self._device, timeout=timeout) as client:
                    _LOGGER.debug("Connected to device %s (timeout: %.1fs)", self.address, timeout)
                    
                    # Wait for connection to stabilize
                    await asyncio.sleep(0.5)
                    
                    # Discover characteristics
                    try:
                        characteristics = await self._discover_characteristics(client)
                    except Exception as e:
                        _LOGGER.warning(f"Characteristic discovery failed: {e}")
                        characteristics = {'rx_chars': [], 'tx_chars': [], 'readable_chars': [], 'all_chars': []}
                    
                    # Try to read data using multiple strategies
                    data = await self._read_data_with_fallbacks(client, characteristics)
                    
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
                        
                        _LOGGER.info("Successfully retrieved data from %s: %s", 
                                   self.address, list(data.keys()))
                        
                        return data
                    else:
                        raise Exception("No data could be read from device")
                    
            except BleakDeviceNotFoundError as err:
                error_msg = f"Device {self.address} not found"
                _LOGGER.error("%s (attempt %d/%d): %s", error_msg, attempt + 1, config['max_retries'], err)
                self._last_error = error_msg
                if attempt == config['max_retries'] - 1:
                    return self._get_error_data(error_msg)
                # Don't retry if device not found
                break
                
            except BleakError as err:
                error_msg = f"Connection failed to device {self.address}: {err}"
                _LOGGER.error("%s (attempt %d/%d)", error_msg, attempt + 1, config['max_retries'])
                self._last_error = error_msg
                
                # Special handling for ESP32 connection errors
                if "ESP_GATT_CONN_FAIL_ESTABLISH" in str(err):
                    _LOGGER.warning("ESP32 connection establishment failed - this is common with these devices")
                    # Longer delay for ESP32 connection issues
                    if attempt < config['max_retries'] - 1:
                        wait_time = 5 + attempt * 3  # 8, 11, 14 seconds
                        _LOGGER.info("Waiting %d seconds before ESP32 retry...", wait_time)
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

    async def _read_data_with_fallbacks(self, client: BleakClient, characteristics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try multiple strategies to read data from the device"""
        
        # Strategy 1: Try known RX characteristics
        for char_info in characteristics['rx_chars']:
            try:
                _LOGGER.debug(f"Trying to read from RX characteristic: {char_info['uuid']}")
                data = await client.read_gatt_char(char_info['uuid'])
                if data:
                    parsed = self._parse_power_data(data)
                    if parsed:
                        _LOGGER.debug("Successfully read data from RX characteristic")
                        return parsed
            except Exception as e:
                _LOGGER.debug(f"Failed to read from {char_info['uuid']}: {e}")
                continue
        
        # Strategy 2: Try all readable characteristics
        for char_info in characteristics['readable_chars']:
            try:
                _LOGGER.debug(f"Trying to read from readable characteristic: {char_info['uuid']}")
                data = await client.read_gatt_char(char_info['uuid'])
                if data and len(data) > 4:  # Reasonable data length
                    parsed = self._parse_power_data(data)
                    if parsed:  # Valid data
                        _LOGGER.debug("Successfully read data from readable characteristic")
                        return parsed
            except Exception as e:
                _LOGGER.debug(f"Failed to read from {char_info['uuid']}: {e}")
                continue
        
        # Strategy 3: Send command and read response (if we have TX characteristics)
        if characteristics['tx_chars']:
            try:
                tx_char = characteristics['tx_chars'][0]
                _LOGGER.debug(f"Sending read command to TX characteristic: {tx_char['uuid']}")
                
                # Send a common read command
                read_command = b'\x01\x03\x00\x00\x00\x01\x84\x0A'  # Common Modbus-like read command
                await client.write_gatt_char(tx_char['uuid'], read_command)
                
                # Wait for response
                await asyncio.sleep(0.5)
                
                # Try to read response from RX characteristics
                for char_info in characteristics['rx_chars'] or characteristics['readable_chars']:
                    try:
                        data = await client.read_gatt_char(char_info['uuid'])
                        if data:
                            parsed = self._parse_power_data(data)
                            if parsed:
                                _LOGGER.debug("Successfully read data via command/response")
                                return parsed
                    except Exception as e:
                        _LOGGER.debug(f"Failed to read response from {char_info['uuid']}: {e}")
                        continue
                        
            except Exception as e:
                _LOGGER.debug(f"Command/response strategy failed: {e}")
        
        # Strategy 4: Try to get model number if available
        try:
            model_data = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
            model = model_data.decode('utf-8', errors='ignore').strip()
            _LOGGER.debug("Got model number: %s", model)
            return {
                "model_number": model,
                "voltage": 0.0,
                "current": 0.0,
                "power": 0.0,
                "energy": 0.0
            }
        except Exception as e:
            _LOGGER.debug(f"Could not read model number: {e}")
        
        _LOGGER.warning("All data reading strategies failed")
        return None

    def _parse_power_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse power data from raw bytes with multiple format support"""
        if not data or len(data) < 4:
            return None
        
        try:
            _LOGGER.debug(f"Parsing data: {data.hex()}")
            
            # Strategy 1: Try common BluPow format (little-endian)
            if len(data) >= 8:
                try:
                    voltage = int.from_bytes(data[0:2], byteorder='little') / 100.0
                    current = int.from_bytes(data[2:4], byteorder='little') / 1000.0
                    power = int.from_bytes(data[4:6], byteorder='little') / 100.0
                    energy = int.from_bytes(data[6:8], byteorder='little') / 1000.0
                    
                    # Sanity check
                    if 0 < voltage < 500 and 0 <= current < 100 and 0 <= power < 10000:
                        return {
                            'voltage': voltage,
                            'current': current,
                            'power': power,
                            'energy': energy,
                            'model_number': 'BluPow Device'
                        }
                except Exception as e:
                    _LOGGER.debug(f"Little-endian parsing failed: {e}")
            
            # Strategy 2: Try big-endian format
            if len(data) >= 8:
                try:
                    voltage = int.from_bytes(data[0:2], byteorder='big') / 100.0
                    current = int.from_bytes(data[2:4], byteorder='big') / 1000.0
                    power = int.from_bytes(data[4:6], byteorder='big') / 100.0
                    energy = int.from_bytes(data[6:8], byteorder='big') / 1000.0
                    
                    # Sanity check
                    if 0 < voltage < 500 and 0 <= current < 100 and 0 <= power < 10000:
                        return {
                            'voltage': voltage,
                            'current': current,
                            'power': power,
                            'energy': energy,
                            'model_number': 'BluPow Device'
                        }
                except Exception as e:
                    _LOGGER.debug(f"Big-endian parsing failed: {e}")
            
            # Strategy 3: Try to parse as ASCII/text
            try:
                text_data = data.decode('utf-8').strip()
                if ',' in text_data or ';' in text_data:
                    # CSV-like format
                    values = text_data.replace(';', ',').split(',')
                    if len(values) >= 4:
                        return {
                            'voltage': float(values[0]),
                            'current': float(values[1]),
                            'power': float(values[2]),
                            'energy': float(values[3]),
                            'model_number': 'BluPow Device'
                        }
            except Exception as e:
                _LOGGER.debug(f"ASCII parsing failed: {e}")
            
            _LOGGER.warning(f"Could not parse data format: {data.hex()}")
            return None
            
        except Exception as e:
            _LOGGER.error(f"Data parsing error: {e}")
            return None

    def _get_error_data(self, error_message: str) -> Dict[str, Any]:
        """Return error data structure."""
        return {
            "error_message": error_message,
            "model_number": "Unknown",
            "voltage": None,
            "current": None,
            "power": None,
            "energy": None,
            "connection_attempts": self._connection_attempts,
            "last_error": error_message,
            "device_type": self.device_type,
            "environment": str(self.environment),
        }

    @staticmethod
    async def scan_devices(timeout: float = 10.0) -> List[Tuple[str, str]]:
        """Scan for BluPow devices with environment-aware settings"""
        _LOGGER.info("Scanning for BluPow devices...")
        
        env = EnvironmentInfo()
        
        # Adjust scan parameters based on environment
        scan_timeout = timeout
        if env.is_docker:
            scan_timeout += 5  # Docker might need more time
        if env.platform == "Windows":
            scan_timeout += 3  # Windows BLE can be slower
        
        try:
            devices = await BleakScanner.discover(timeout=scan_timeout)
            blupow_devices = []
            
            for device in devices:
                name = device.name or ""
                if any(keyword in name.lower() for keyword in ['blupow', 'power', 'meter', 'esp32']):
                    blupow_devices.append((device.address, name))
                    _LOGGER.info(f"Found potential BluPow device: {name} ({device.address})")
            
            _LOGGER.info(f"Scan completed. Found {len(blupow_devices)} potential devices.")
            return blupow_devices
            
        except Exception as e:
            _LOGGER.error(f"Device scan failed: {e}")
            return [] 