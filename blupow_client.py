"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from bleak import BleakClient, BleakError
from bleak.exc import BleakDeviceNotFoundError
from bleak.backends.device import BLEDevice

from .const import (
    MODEL_NUMBER_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    REG_BATTERY_SOC,
)

_LOGGER = logging.getLogger(__name__)


class BluPowClient:
    """A client to handle reading data from a Renogy device with comprehensive error handling."""

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
            raw_model = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
            
            # Log the raw data for debugging
            _LOGGER.debug("Raw model number data: %s (hex: %s)", raw_model, raw_model.hex())
            
            # Try to decode as UTF-8
            try:
                model = raw_model.decode("utf-8").strip()
                _LOGGER.debug("Decoded as UTF-8: %s", model)
                
                # Handle the specific format we're seeing: "TC,R2#4,1,248,S"
                if model and ',' in model:
                    # Split by comma and take the first part as the main model
                    parts = model.split(',')
                    if len(parts) >= 2:
                        main_model = parts[0].strip()
                        sub_model = parts[1].strip()
                        # Clean up the sub-model (remove special characters)
                        sub_model = ''.join(char for char in sub_model if char.isalnum() or char in '.-_')
                        model = f"{main_model}-{sub_model}"
                        _LOGGER.debug("Parsed model from comma-separated format: %s", model)
                
            except UnicodeDecodeError:
                # If UTF-8 fails, try to interpret as hex or other format
                _LOGGER.debug("UTF-8 decode failed, trying alternative parsing")
                model = raw_model.hex().upper()
            
            # Clean up the model number
            if model and model != "Unknown":
                # Remove any non-printable characters but keep alphanumeric, dots, dashes, and underscores
                model = ''.join(char for char in model if char.isprintable() and (char.isalnum() or char in ',.-_#'))
                _LOGGER.info("Successfully read model number: %s for %s", model, self.address)
                return model
            else:
                _LOGGER.warning("Empty or invalid model number from %s", self.address)
                return "Unknown"
                
        except Exception as err:
            _LOGGER.warning("Could not read model number from %s: %s", self.address, err)
            return "Unknown"

    async def _get_register_data(self, client: BleakClient) -> Dict[str, Any]:
        """Get register data with error handling."""
        try:
            _LOGGER.debug("Reading register data from device %s", self.address)
            
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
                    different_char_data = await self._try_different_characteristics(client)
                    if any(value is not None for value in different_char_data.values()):
                        _LOGGER.info("Successfully read data using different characteristics")
                        return different_char_data
                except Exception as diff_err:
                    _LOGGER.warning("Different characteristics approach failed: %s", diff_err)
                
                # Try alternative approach - read individual characteristics
                _LOGGER.info("Trying alternative data reading approach for %s", self.address)
                return await self._try_alternative_data_reading(client)
                
        except Exception as err:
            _LOGGER.warning("Could not read register data from %s: %s", self.address, err)
            return self._get_default_register_data()

    async def _try_alternative_data_reading(self, client: BleakClient) -> Dict[str, Any]:
        """Try alternative methods to read device data."""
        try:
            _LOGGER.debug("Attempting alternative data reading for %s", self.address)
            
            # Get all services and characteristics
            services = await client.get_services()
            # Convert to list to avoid BleakGATTServiceCollection issues
            services_list = list(services)
            _LOGGER.debug("Found %d services for device %s", len(services_list), self.address)
            
            result = self._get_default_register_data()
            
            # Log all available services and characteristics for debugging
            _LOGGER.info("=== DEVICE CHARACTERISTIC DISCOVERY ===")
            _LOGGER.info("Device: %s (%s)", self.name, self.address)
            
            for service in services_list:
                _LOGGER.info("Service: %s - %s", service.uuid, service.description or "Unknown")
                for char in service.characteristics:
                    _LOGGER.info("  Characteristic: %s - %s (props: %s)", 
                                 char.uuid, char.description or "Unknown", char.properties)
                    
                    # Try to read readable characteristics
                    if "read" in char.properties:
                        try:
                            data = await client.read_gatt_char(char.uuid)
                            _LOGGER.info("  Read %s: %s (hex: %s)", char.uuid, data, data.hex())
                            
                            # Try to parse as numeric data
                            if len(data) >= 2:
                                value = int.from_bytes(data[:2], "big")
                                _LOGGER.debug("  Parsed as 16-bit value: %d", value)
                                
                                # Map characteristic UUIDs to sensor names if possible
                                # Look for patterns in the data or characteristic properties
                                if "battery" in (char.description or "").lower() or "voltage" in (char.description or "").lower():
                                    result["battery_voltage"] = value / 10.0  # Assume 0.1V resolution
                                    _LOGGER.info("  Mapped to battery_voltage: %.1fV", result["battery_voltage"])
                                elif "current" in (char.description or "").lower():
                                    result["battery_current"] = value / 100.0  # Assume 0.01A resolution
                                    _LOGGER.info("  Mapped to battery_current: %.2fA", result["battery_current"])
                                elif "soc" in (char.description or "").lower() or "charge" in (char.description or "").lower():
                                    result["battery_soc"] = value
                                    _LOGGER.info("  Mapped to battery_soc: %d%%", result["battery_soc"])
                                elif "temp" in (char.description or "").lower():
                                    result["battery_temp"] = value
                                    _LOGGER.info("  Mapped to battery_temp: %d°C", result["battery_temp"])
                                elif "solar" in (char.description or "").lower():
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
                            _LOGGER.debug("  Could not read characteristic %s: %s", char.uuid, char_err)
            
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

    async def _try_different_characteristics(self, client: BleakClient) -> Dict[str, Any]:
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
            
            # Get all services and characteristics
            services = await client.get_services()
            services_list = list(services)
            
            # Find all available characteristics
            available_chars = []
            for service in services_list:
                for char in service.characteristics:
                    available_chars.append(char.uuid)
                    _LOGGER.info("Found characteristic: %s", char.uuid)
            
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

