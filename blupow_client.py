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
        
        try:
            _LOGGER.info("Starting data retrieval for device %s (attempt %d)", 
                        self.address, self._connection_attempts)
            
            async with BleakClient(self._device, timeout=15.0) as client:
                _LOGGER.debug("Connected to device %s", self.address)
                
                # Get model number
                model = await self._get_model_number(client)
                
                # Get register data
                register_data = await self._get_register_data(client)
                
                # Combine data
                result = {"model_number": model, **register_data}
                
                # Add metadata
                result.update({
                    "connection_attempts": self._connection_attempts,
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
            _LOGGER.error("%s: %s", error_msg, err)
            self._last_error = error_msg
            return self._get_error_data(error_msg)
            
        except BleakError as err:
            error_msg = f"Connection failed to device {self.address}: {err}"
            _LOGGER.error("%s: %s", error_msg, err)
            self._last_error = error_msg
            return self._get_error_data(error_msg)
            
        except asyncio.TimeoutError as err:
            error_msg = f"Timeout connecting to device {self.address}"
            _LOGGER.error("%s: %s", error_msg, err)
            self._last_error = error_msg
            return self._get_error_data(error_msg)
            
        except Exception as err:
            error_msg = f"Unexpected error with device {self.address}: {err}"
            _LOGGER.error(error_msg)
            self._last_error = error_msg
            return self._get_error_data(error_msg)

    async def _get_model_number(self, client: BleakClient) -> str:
        """Get model number with error handling."""
        try:
            _LOGGER.debug("Reading model number from device %s", self.address)
            raw_model = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
            model = raw_model.decode("utf-8").strip()
            _LOGGER.info("Successfully read model number: %s for %s", 
                       model, self.address)
            return model
        except Exception as err:
            _LOGGER.warning("Could not read model number from %s: %s", self.address, err)
            return "Unknown"

    async def _get_register_data(self, client: BleakClient) -> Dict[str, Any]:
        """Get register data with error handling."""
        try:
            _LOGGER.debug("Reading register data from device %s", self.address)
            data = await self._read_registers(client, REG_BATTERY_SOC, 10)
            parsed_data = self._parse_data(data)
            _LOGGER.debug("Successfully parsed register data: %s", list(parsed_data.keys()))
            return parsed_data
        except Exception as err:
            _LOGGER.warning("Could not read register data from %s: %s", self.address, err)
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
                
        except Exception as err:
            _LOGGER.error("Error reading registers from %s: %s", self.address, err)
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

