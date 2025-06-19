"""
BluPow BLE Client for Home Assistant Integration

This client implements proactive environment detection and universal compatibility
following the BluPow Project Ideology.
"""

import asyncio
import logging
import platform
import sys
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

from bleak import BleakClient, BleakScanner, BleakError
from bleak.exc import BleakDeviceNotFoundError
from bleak.backends.device import BLEDevice

from .const import (
    MODEL_NUMBER_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    REG_BATTERY_SOC,
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
            "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",  # Nordic UART RX
            "0000FFE1-0000-1000-8000-00805F9B34FB",  # Common ESP32 RX
            "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",  # Alternative RX
        ],
        'tx': [
            "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",  # Nordic UART TX
            "0000FFE1-0000-1000-8000-00805F9B34FB",  # Common ESP32 TX
            "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",  # Alternative TX
        ]
    }

    def __init__(self, device: BLEDevice):
        """Initialize the BluPowClient with comprehensive error handling."""
        try:
            self._device = device
            self._notification_queue: asyncio.Queue[bytearray] = asyncio.Queue()
            self._connection_attempts = 0
            self._last_successful_connection = None
            self._last_error = None
            self._max_retries = 3
            self._base_timeout = 20.0  # Increased from 15.0
            self._discovered_characteristics = {}  # Cache discovered characteristics
            self.environment = EnvironmentInfo()
            self.device_type = "DEFAULT"  # Will be detected
            self._connection_lock = asyncio.Lock()
            
            _LOGGER.info("BluPow client initialized for device: %s (%s)", 
                        device.name or "Unknown", device.address)
                        
        except Exception as err:
            _LOGGER.error("Failed to initialize BluPow client: %s", err)
            raise

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

    async def _notification_handler(self, sender: int, data: bytearray):
        """Handle incoming notifications with error handling."""
        try:
            _LOGGER.debug("Received notification from %s: %s", sender, data.hex())
            await self._notification_queue.put(data)
        except Exception as err:
            _LOGGER.error("Error handling notification: %s", err)

    async def get_data(self) -> Dict[str, Any]:
        """Read device data with comprehensive error handling and retry logic."""
        start_time = datetime.now()
        self._connection_attempts += 1
        
        # Try multiple connection attempts with exponential backoff
        for attempt in range(self._max_retries):
            try:
                _LOGGER.info("Starting data retrieval for device %s (attempt %d/%d)", 
                            self.address, attempt + 1, self._max_retries)
                
                # Calculate timeout with exponential backoff, but cap at 30 seconds
                timeout = min(self._base_timeout * (2 ** attempt), 30.0)
                
                # Add connection delay for ESP32 devices to avoid connection conflicts
                if attempt > 0:
                    delay = 3 + attempt * 2  # 5, 7, 9 seconds for retries
                    _LOGGER.info("Waiting %d seconds before connection attempt...", delay)
                    await asyncio.sleep(delay)
                
                async with BleakClient(self._device, timeout=timeout) as client:
                    _LOGGER.debug("Connected to device %s (timeout: %.1fs)", self.address, timeout)
                    
                    # Wait a moment for connection to stabilize
                    await asyncio.sleep(0.5)
                    
                    # Get model number
                    model = await self._get_model_number(client)
                    
                    # Get register data
                    register_data = await self._get_register_data(client)
                    
                    # Combine data
                    result = {"model_number": model, **register_data}
                    
                    # Add metadata
                    result.update({
                        "connection_attempts": self._connection_attempts,
                        "connection_retry_attempt": attempt + 1,
                        "last_successful_connection": start_time.isoformat(),
                        "connection_duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    })
                    
                    self._last_successful_connection = start_time
                    self._last_error = None
                    
                    _LOGGER.info("Successfully retrieved data from %s: %s", 
                               self.address, list(result.keys()))
                    
                    return result
                    
            except BleakDeviceNotFoundError as err:
                error_msg = f"Device {self.address} not found"
                _LOGGER.error("%s (attempt %d/%d): %s", error_msg, attempt + 1, self._max_retries, err)
                self._last_error = error_msg
                if attempt == self._max_retries - 1:
                    return self._get_error_data(error_msg)
                # Don't retry if device not found
                break
                
            except BleakError as err:
                error_msg = f"Connection failed to device {self.address}: {err}"
                _LOGGER.error("%s (attempt %d/%d)", error_msg, attempt + 1, self._max_retries)
                self._last_error = error_msg
                
                # Special handling for ESP32 connection errors
                if "ESP_GATT_CONN_FAIL_ESTABLISH" in str(err):
                    _LOGGER.warning("ESP32 connection establishment failed - this is common with these devices")
                    # Longer delay for ESP32 connection issues
                    if attempt < self._max_retries - 1:
                        wait_time = 5 + attempt * 3  # 8, 11, 14 seconds
                        _LOGGER.info("Waiting %d seconds before ESP32 retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg)
                else:
                    if attempt < self._max_retries - 1:
                        # Wait before retry with exponential backoff
                        wait_time = 2 ** attempt
                        _LOGGER.info("Waiting %d seconds before retry...", wait_time)
                        await asyncio.sleep(wait_time)
                    else:
                        return self._get_error_data(error_msg)
                    
            except asyncio.TimeoutError as err:
                error_msg = f"Timeout connecting to device {self.address}"
                _LOGGER.error("%s (attempt %d/%d): %s", error_msg, attempt + 1, self._max_retries, err)
                self._last_error = error_msg
                
                if attempt < self._max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    _LOGGER.info("Waiting %d seconds before retry...", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    return self._get_error_data(error_msg)
                    
            except Exception as err:
                error_msg = f"Unexpected error with device {self.address}: {err}"
                _LOGGER.error("%s (attempt %d/%d)", error_msg, attempt + 1, self._max_retries)
                self._last_error = error_msg
                
                if attempt < self._max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    _LOGGER.info("Waiting %d seconds before retry...", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    return self._get_error_data(error_msg)
        
        # If we get here, all retries failed
        return self._get_error_data(f"All {self._max_retries} connection attempts failed")

    async def check_device_availability(self) -> bool:
        """Check if the device is available for connection."""
        try:
            _LOGGER.debug("Checking availability of device %s", self.address)
            
            # Try a quick connection to see if device responds
            async with BleakClient(self._device, timeout=3.0) as client:
                # Just check if we can connect, don't read data
                _LOGGER.debug("Device %s is available", self.address)
                return True
                
        except Exception as err:
            _LOGGER.debug("Device %s quick check failed: %s", self.address, err)
            # Don't fail completely - let the main connection attempt try
            return True  # Changed from False to True to allow main attempt

    async def _get_model_number(self, client: BleakClient) -> str:
        """Get model number with error handling."""
        try:
            _LOGGER.debug("Reading model number from device %s", self.address)
            
            # Try to read model number characteristic
            try:
                model_data = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
                model = model_data.decode('utf-8', errors='ignore').strip()
                _LOGGER.debug("Model number: %s", model)
                return model
            except Exception as model_err:
                _LOGGER.debug("Could not read model number: %s", model_err)
                return "Unknown"
                
        except Exception as err:
            _LOGGER.error("Error getting model number: %s", err)
            return "Unknown"

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

    async def _get_register_data(self, client: BleakClient) -> Dict[str, Any]:
        """Get register data with error handling."""
        try:
            _LOGGER.debug("Reading register data from device %s", self.address)
            
            # Discover characteristics first
            characteristics = await self._discover_characteristics(client)
            
            # Try to read register data with original UUIDs
            try:
                data = await self._read_registers(client, REG_BATTERY_SOC, 10)
                _LOGGER.debug("Raw register data received: %s", data.hex())
                parsed_data = self._parse_data(data)
                _LOGGER.debug("Successfully parsed register data: %s", list(parsed_data.keys()))
                return parsed_data
            except Exception as reg_err:
                _LOGGER.warning("Register reading failed for %s: %s", self.address, reg_err)
                
                # Try different characteristic UUIDs
                _LOGGER.info("Trying different characteristic UUIDs for %s", self.address)
                try:
                    different_char_data = await self._try_different_characteristics(client, characteristics)
                    if any(value is not None for value in different_char_data.values()):
                        _LOGGER.info("Successfully read data using different characteristics")
                        return different_char_data
                except Exception as diff_err:
                    _LOGGER.warning("Different characteristics approach failed: %s", diff_err)
                
                # Try alternative approach - read individual characteristics
                _LOGGER.info("Trying alternative data reading approach for %s", self.address)
                return await self._try_alternative_data_reading(client, characteristics)
                
        except Exception as err:
            _LOGGER.warning("Could not read register data from %s: %s", self.address, err)
            return self._get_default_register_data()

    async def _try_alternative_data_reading(self, client: BleakClient, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Try alternative methods to read device data."""
        try:
            _LOGGER.debug("Attempting alternative data reading for %s", self.address)
            
            result = self._get_default_register_data()
            
            # Log all available services and characteristics for debugging
            _LOGGER.info("=== DEVICE CHARACTERISTIC DISCOVERY ===")
            _LOGGER.info("Device: %s (%s)", self.name, self.address)
            
            # Try to read readable characteristics
            for char_info in characteristics.get('readable_chars', []):
                try:
                    data = await client.read_gatt_char(char_info['uuid'])
                    _LOGGER.info("  Read %s: %s (hex: %s)", char_info['uuid'], data, data.hex())
                    
                    # Try to parse as numeric data
                    if len(data) >= 2:
                        value = int.from_bytes(data[:2], "big")
                        _LOGGER.debug("  Parsed as 16-bit value: %d", value)
                        
                        # Map characteristic UUIDs to sensor names if possible
                        # Look for patterns in the data or characteristic properties
                        if "battery" in char_info['description'].lower() or "voltage" in char_info['description'].lower():
                            result["battery_voltage"] = value / 10.0  # Assume 0.1V resolution
                            _LOGGER.info("  Mapped to battery_voltage: %.1fV", result["battery_voltage"])
                        elif "current" in char_info['description'].lower():
                            result["battery_current"] = value / 100.0  # Assume 0.01A resolution
                            _LOGGER.info("  Mapped to battery_current: %.2fA", result["battery_current"])
                        elif "soc" in char_info['description'].lower() or "charge" in char_info['description'].lower():
                            result["battery_soc"] = value
                            _LOGGER.info("  Mapped to battery_soc: %d%%", result["battery_soc"])
                        elif "temp" in char_info['description'].lower():
                            result["battery_temp"] = value
                            _LOGGER.info("  Mapped to battery_temp: %d°C", result["battery_temp"])
                        elif "solar" in char_info['description'].lower():
                            # Try to determine if it's voltage or current based on value range
                            if value > 1000:  # Likely voltage in 0.1V units
                                result["solar_voltage"] = value / 10.0
                                _LOGGER.info("  Mapped to solar_voltage: %.1fV", result["solar_voltage"])
                            else:  # Likely current in 0.01A units
                                result["solar_current"] = value / 100.0
                                _LOGGER.info("  Mapped to solar_current: %.2fA", result["solar_current"])
                        else:
                            # Try to guess based on value ranges
                            if 1200 <= value <= 1500:  # Typical battery voltage range (12-15V in 0.1V units)
                                result["battery_voltage"] = value / 10.0
                                _LOGGER.info("  Guessed battery_voltage from value range: %.1fV", result["battery_voltage"])
                            elif 0 <= value <= 100:  # Typical SOC range
                                result["battery_soc"] = value
                                _LOGGER.info("  Guessed battery_soc from value range: %d%%", result["battery_soc"])
                            elif 200 <= value <= 500:  # Typical temperature range
                                result["battery_temp"] = value
                                _LOGGER.info("  Guessed battery_temp from value range: %d°C", result["battery_temp"])
                            
                except Exception as char_err:
                    _LOGGER.debug("  Could not read characteristic %s: %s", char_info['uuid'], char_err)
            
            _LOGGER.info("=== END CHARACTERISTIC DISCOVERY ===")
            
            # Check if we found any data
            found_data = any(value is not None for value in result.values())
            if found_data:
                _LOGGER.info("Alternative data reading successful for %s: %s", self.address, result)
            else:
                _LOGGER.warning("No data found through alternative reading for %s", self.address)
            
            return result
            
        except Exception as err:
            _LOGGER.error("Alternative data reading failed for %s: %s", self.address, err)
            return self._get_default_register_data()

    def _get_error_data(self, error_message: str) -> Dict[str, Any]:
        """Get error data structure."""
        return {
            "model_number": "Unknown",
            "battery_voltage": None,
            "solar_voltage": None,
            "battery_current": None,
            "solar_current": None,
            "battery_soc": None,
            "battery_temp": None,
            "solar_power": None,
            "error_message": error_message,
            "connection_attempts": self._connection_attempts,
            "last_error": self._last_error,
        }

    def _get_default_register_data(self) -> Dict[str, Any]:
        """Get default register data structure."""
        return {
            "battery_voltage": None,
            "solar_voltage": None,
            "battery_current": None,
            "solar_current": None,
            "battery_soc": None,
            "battery_temp": None,
            "solar_power": None,
        }

    async def _read_registers(
        self, client: BleakClient, start_register: int, count: int
    ) -> bytearray:
        """Read a range of registers from the device with comprehensive error handling."""
        try:
            # Clear any existing notifications
            await self._clear_notification_queue()
            
            # Check if characteristics exist before trying to use them
            try:
                if hasattr(client, 'services'):
                    # Use the services property instead of get_services() method
                    services = client.services
                else:
                    # Fallback for older bleak versions
                    services = await client.get_services()
                
                # Convert to list to avoid BleakGATTServiceCollection issues
                services_list = list(services)
                rx_char_found = False
                tx_char_found = False
                
                for service in services_list:
                    for char in service.characteristics:
                        if char.uuid == RENOGY_RX_CHAR_UUID:
                            rx_char_found = True
                        elif char.uuid == RENOGY_TX_CHAR_UUID:
                            tx_char_found = True
                
                if not rx_char_found:
                    raise BleakError(f"RX characteristic {RENOGY_RX_CHAR_UUID} was not found")
                if not tx_char_found:
                    raise BleakError(f"TX characteristic {RENOGY_TX_CHAR_UUID} was not found")
                    
                _LOGGER.debug("Found required characteristics for device %s", self.address)
                
            except Exception as err:
                _LOGGER.error("Error checking characteristics for %s: %s", self.address, err)
                raise BleakError(f"Characteristic check failed: {err}")
            
            # Start listening for notifications
            _LOGGER.debug("Starting notifications for device %s", self.address)
            await client.start_notify(RENOGY_RX_CHAR_UUID, self._notification_handler)

            try:
                # Build the Modbus command
                command = self._build_modbus_command(start_register, count)
                _LOGGER.debug("Sending command to %s: %s", self.address, command.hex())

                # Send the command
                await client.write_gatt_char(RENOGY_TX_CHAR_UUID, command, response=True)

                # Wait for response
                response = await self._wait_for_response()
                _LOGGER.debug("Received response from %s: %s", self.address, response.hex())
                
                return response

            finally:
                # Always stop notifications
                await self._stop_notifications(client)
                
        except BleakError as err:
            _LOGGER.error("BLE error reading registers from %s: %s", self.address, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error reading registers from %s: %s", self.address, err)
            raise

    async def _clear_notification_queue(self) -> None:
        """Clear the notification queue."""
        try:
            while not self._notification_queue.empty():
                try:
                    self._notification_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        except Exception as err:
            _LOGGER.debug("Error clearing notification queue: %s", err)

    def _build_modbus_command(self, start_register: int, count: int) -> bytearray:
        """Build Modbus command with validation."""
        try:
            command = bytearray(
                [0xFF, 0x03, start_register >> 8, start_register & 0xFF, 0x00, count]
            )
            command.extend([0x00, 0x00])  # No CRC for now
            return command
        except Exception as err:
            _LOGGER.error("Error building Modbus command: %s", err)
            raise

    async def _wait_for_response(self) -> bytearray:
        """Wait for response with timeout and validation."""
        try:
            response = bytearray()
            
            # Wait for first notification
            notification = await asyncio.wait_for(
                self._notification_queue.get(), timeout=10.0
            )

            if len(notification) < 3 or notification[0] != 0xFF or notification[1] != 0x03:
                raise ValueError(f"Invalid header in first notification: {notification.hex()}")

            response.extend(notification)
            expected_payload_len = notification[2]

            # Collect remaining data
            while len(response) < 3 + expected_payload_len:
                notification = await asyncio.wait_for(
                    self._notification_queue.get(), timeout=5.0
                )
                response.extend(notification)

            return response

        except asyncio.TimeoutError:
            raise BleakError("Timeout waiting for device response")
        except Exception as err:
            _LOGGER.error("Error waiting for response: %s", err)
            raise

    async def _stop_notifications(self, client: BleakClient) -> None:
        """Stop notifications with error handling."""
        try:
            await client.stop_notify(RENOGY_RX_CHAR_UUID)
            _LOGGER.debug("Stopped notifications for device %s", self.address)
        except Exception as err:
            _LOGGER.debug("Error stopping notifications for %s: %s", self.address, err)

    def _parse_data(self, data: bytearray) -> Dict[str, Any]:
        """Parse the raw data from the device with comprehensive error handling."""
        try:
            if len(data) < 3 or data[0] != 0xFF or data[1] != 0x03:
                raise ValueError(f"Invalid response header: {data.hex()}")

            data_len = data[2]
            if len(data) < 3 + data_len:
                raise ValueError(
                    f"Incomplete response: expected {3+data_len} bytes, got {len(data)}"
                )

            payload = data[3 : 3 + data_len]
            _LOGGER.debug("Parsing payload: %s", payload.hex())

            result = {}
            for key, (reg_offset, multiplier) in self._get_register_mappings().items():
                value = self._extract_register_value(payload, reg_offset, multiplier)
                result[key] = value
                _LOGGER.debug("Parsed %s: %s", key, value)

            return result

        except Exception as err:
            _LOGGER.error("Error parsing data: %s", err)
            return self._get_default_register_data()

    def _get_register_mappings(self) -> Dict[str, tuple[int, float]]:
        """Get register mappings for data parsing."""
        return {
            "battery_soc": (0x0100, 1.0),
            "battery_voltage": (0x0101, 0.1),
            "battery_current": (0x0102, 0.01),
            "battery_temp": (0x0103, 1.0),
            "solar_voltage": (0x0107, 0.1),
            "solar_current": (0x0108, 0.01),
            "solar_power": (0x0109, 1.0),
        }

    def _extract_register_value(self, payload: bytearray, reg_offset: int, multiplier: float) -> Optional[float]:
        """Safely extract and scale a value from the payload."""
        try:
            start = (reg_offset - REG_BATTERY_SOC) * 2
            if start + 2 <= len(payload):
                raw_value = int.from_bytes(payload[start : start + 2], "big")
                result = raw_value * multiplier
                _LOGGER.debug("Extracted value: raw=%d, scaled=%.3f", raw_value, result)
                return result
            else:
                _LOGGER.debug("Register offset %d out of payload range (len=%d)", reg_offset, len(payload))
                return None
        except Exception as err:
            _LOGGER.error("Error extracting register value for offset %d: %s", reg_offset, err)
            return None

    async def disconnect(self):
        """Disconnect from the device."""
        try:
            _LOGGER.debug("Disconnecting from device %s", self.address)
            # This is handled automatically by the context manager
        except Exception as err:
            _LOGGER.error("Error during disconnect: %s", err)

    def get_status_info(self) -> Dict[str, Any]:
        """Get status information about the client."""
        return {
            "device_name": self.name,
            "device_address": self.address,
            "connection_attempts": self._connection_attempts,
            "last_successful_connection": self._last_successful_connection.isoformat() if self._last_successful_connection else None,
            "last_error": self._last_error,
        }

    async def _try_different_characteristics(self, client: BleakClient, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Try different characteristic UUIDs that might be used by Renogy devices."""
        try:
            _LOGGER.info("Trying different characteristic UUIDs for %s", self.address)
            
            # Common characteristic UUIDs that might be used by Renogy devices
            possible_rx_uuids = [
                "0000cd02-0000-1000-8000-00805f9b34fb",  # Original
                "0000cd01-0000-1000-8000-00805f9b34fb",  # Alternative
                "0000cd03-0000-1000-8000-00805f9b34fb",  # Another possibility
                "0000cd04-0000-1000-8000-00805f9b34fb",  # Yet another
                "0000cd05-0000-1000-8000-00805f9b34fb",  # And another
            ]
            
            possible_tx_uuids = [
                "0000cd01-0000-1000-8000-00805f9b34fb",  # Original
                "0000cd02-0000-1000-8000-00805f9b34fb",  # Alternative
                "0000cd03-0000-1000-8000-00805f9b34fb",  # Another possibility
                "0000cd04-0000-1000-8000-00805f9b34fb",  # Yet another
                "0000cd05-0000-1000-8000-00805f9b34fb",  # And another
            ]
            
            # Find all available characteristics from discovery
            available_chars = [char['uuid'] for char in characteristics.get('all_chars', [])]
            
            # Try to find matching RX/TX characteristics
            rx_char = None
            tx_char = None
            
            for rx_uuid in possible_rx_uuids:
                if rx_uuid in available_chars:
                    rx_char = rx_uuid
                    _LOGGER.info("Found RX characteristic: %s", rx_char)
                    break
            
            for tx_uuid in possible_tx_uuids:
                if tx_uuid in available_chars:
                    tx_char = tx_uuid
                    _LOGGER.info("Found TX characteristic: %s", tx_char)
                    break
            
            if rx_char and tx_char:
                _LOGGER.info("Found working RX/TX pair: %s / %s", rx_char, tx_char)
                # Try to use these characteristics for register reading
                try:
                    # Use the found characteristics with a custom read method
                    data = await self._read_registers_with_uuids(client, REG_BATTERY_SOC, 10, rx_char, tx_char)
                    parsed_data = self._parse_data(data)
                    return parsed_data
                    
                except Exception as err:
                    _LOGGER.warning("Failed to use found RX/TX pair: %s", err)
            
            _LOGGER.warning("No suitable RX/TX characteristics found")
            return self._get_default_register_data()
            
        except Exception as err:
            _LOGGER.error("Error trying different characteristics: %s", err)
            return self._get_default_register_data()

    async def _read_registers_with_uuids(
        self, client: BleakClient, start_register: int, count: int, rx_uuid: str, tx_uuid: str
    ) -> bytearray:
        """Read registers using specified RX/TX UUIDs."""
        try:
            # Clear any existing notifications
            await self._clear_notification_queue()
            
            # Start listening for notifications
            _LOGGER.debug("Starting notifications for device %s with RX UUID %s", self.address, rx_uuid)
            await client.start_notify(rx_uuid, self._notification_handler)

            try:
                # Build the Modbus command
                command = self._build_modbus_command(start_register, count)
                _LOGGER.debug("Sending command to %s: %s", self.address, command.hex())

                # Send the command
                await client.write_gatt_char(tx_uuid, command, response=True)

                # Wait for response
                response = await self._wait_for_response()
                _LOGGER.debug("Received response from %s: %s", self.address, response.hex())
                
                return response

            finally:
                # Always stop notifications
                await self._stop_notifications_with_uuid(client, rx_uuid)
                
        except BleakError as err:
            _LOGGER.error("BLE error reading registers from %s: %s", self.address, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error reading registers from %s: %s", self.address, err)
            raise

    async def _stop_notifications_with_uuid(self, client: BleakClient, rx_uuid: str) -> None:
        """Stop notifications with error handling using specified UUID."""
        try:
            await client.stop_notify(rx_uuid)
            _LOGGER.debug("Stopped notifications for device %s with UUID %s", self.address, rx_uuid)
        except Exception as err:
            _LOGGER.debug("Error stopping notifications for %s: %s", self.address, err)

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

    async def connect(self) -> bool:
        """Connect to the BluPow device with environment-aware retry logic"""
        if self.client and self.client.is_connected:
            return True
            
        async with self._connection_lock:
            if self.client and self.client.is_connected:  # Double-check after acquiring lock
                return True
                
            config = self._get_device_config()
            
            for attempt in range(config['max_retries']):
                try:
                    _LOGGER.info(f"Connection attempt {attempt + 1}/{config['max_retries']} to {self.address}")
                    
                    # Progressive timeout
                    timeout = min(config['timeout_base'] + (attempt * 5), 30)
                    
                    # Create client
                    self.client = BleakClient(self.address, timeout=timeout)
                    
                    # Environment-specific connection delay
                    if attempt > 0:
                        delay = config['connection_delay'] + (attempt * config['retry_multiplier'])
                        _LOGGER.debug(f"Waiting {delay}s before connection attempt (environment: {self.environment.platform})")
                        await asyncio.sleep(delay)
                    
                    # Attempt connection
                    await self.client.connect()
                    
                    if self.client.is_connected:
                        _LOGGER.info(f"Successfully connected to {self.address}")
                        self.is_connected = True
                        
                        # Detect device type from name if available
                        try:
                            device_name = getattr(self.client, 'name', '') or ''
                            self.device_type = self._detect_device_type(device_name)
                            _LOGGER.debug(f"Detected device type: {self.device_type}")
                        except Exception as e:
                            _LOGGER.debug(f"Could not detect device name: {e}")
                        
                        # Discover characteristics
                        try:
                            await self._discover_characteristics(self.client)
                        except Exception as e:
                            _LOGGER.warning(f"Characteristic discovery failed, but connection succeeded: {e}")
                        
                        return True
                    
                except Exception as e:
                    _LOGGER.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if self.client:
                        try:
                            await self.client.disconnect()
                        except:
                            pass
                        self.client = None
                    
                    # Don't wait after the last attempt
                    if attempt < config['max_retries'] - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        _LOGGER.debug(f"Waiting {wait_time}s before next attempt...")
                        await asyncio.sleep(wait_time)
            
            _LOGGER.error(f"Failed to connect to {self.address} after {config['max_retries']} attempts")
            return False



    async def read_data(self) -> Optional[Dict[str, Any]]:
        """Read power data from the device with multiple fallback strategies"""
        if not self.is_connected or not self.client:
            raise Exception("Not connected to device")
        
        try:
            characteristics = await self._discover_characteristics(self.client)
            
            # Strategy 1: Try known RX characteristics
            for char_info in characteristics['rx_chars']:
                try:
                    _LOGGER.debug(f"Trying to read from RX characteristic: {char_info['uuid']}")
                    data = await self.client.read_gatt_char(char_info['uuid'])
                    if data:
                        return self._parse_power_data(data)
                except Exception as e:
                    _LOGGER.debug(f"Failed to read from {char_info['uuid']}: {e}")
                    continue
            
            # Strategy 2: Try all readable characteristics
            for char_info in characteristics['readable_chars']:
                try:
                    _LOGGER.debug(f"Trying to read from readable characteristic: {char_info['uuid']}")
                    data = await self.client.read_gatt_char(char_info['uuid'])
                    if data and len(data) > 4:  # Reasonable data length
                        parsed = self._parse_power_data(data)
                        if parsed:  # Valid data
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
                    await self.client.write_gatt_char(tx_char['uuid'], read_command)
                    
                    # Wait for response
                    await asyncio.sleep(0.5)
                    
                    # Try to read response from RX characteristics
                    for char_info in characteristics['rx_chars'] or characteristics['readable_chars']:
                        try:
                            data = await self.client.read_gatt_char(char_info['uuid'])
                            if data:
                                return self._parse_power_data(data)
                        except Exception as e:
                            _LOGGER.debug(f"Failed to read response from {char_info['uuid']}: {e}")
                            continue
                            
                except Exception as e:
                    _LOGGER.debug(f"Command/response strategy failed: {e}")
            
            raise Exception("No readable characteristics found or all read attempts failed")
            
        except Exception as e:
            _LOGGER.error(f"Failed to read data from {self.address}: {e}")
            raise

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
                            'energy': energy
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
                            'energy': energy
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
                            'energy': float(values[3])
                        }
            except Exception as e:
                _LOGGER.debug(f"ASCII parsing failed: {e}")
            
            _LOGGER.warning(f"Could not parse data format: {data.hex()}")
            return None
            
        except Exception as e:
            _LOGGER.error(f"Data parsing error: {e}")
            return None

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

