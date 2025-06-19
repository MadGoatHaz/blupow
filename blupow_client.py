"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

from homeassistant.core import HomeAssistant

from .const import (
    MODEL_NUMBER_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    REG_BATTERY_VOLTAGE,
    REG_SOLAR_VOLTAGE,
)

_LOGGER = logging.getLogger(__name__)


class BluPowClient:
    """A client to handle reading data from a Renogy device."""

    def __init__(self, hass: HomeAssistant, device: BLEDevice):
        """Initialize the BluPowClient."""
        self._hass = hass
        self._device = device
        self._notification_queue: asyncio.Queue[bytearray] = asyncio.Queue()
        self._max_retries = 3

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device.name or self._device.address

    async def _notification_handler(self, sender: int, data: bytearray):
        """Handle incoming notifications."""
        await self._notification_queue.put(data)

    async def _get_client(self) -> BleakClient:
        """Connect to the device and return the BleakClient instance."""
        client = BleakClient(self._device, timeout=15.0)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                await client.connect()
                _LOGGER.info(
                    "%s: Connected to %s (attempt %d/%d)",
                    self.name,
                    self._device.address,
                    attempt,
                    max_attempts,
                )
                return client
            except (BleakError, asyncio.TimeoutError) as e:
                _LOGGER.warning(
                    "%s: Error connecting to %s (attempt %d/%d): %s",
                    self.name,
                    self._device.address,
                    attempt,
                    max_attempts,
                    e,
                )
                if attempt < max_attempts:
                    await asyncio.sleep(2 * attempt)  # Exponential backoff
                else:
                    raise BleakError(
                        f"Failed to connect to {self.name} after {max_attempts} attempts"
                    ) from e
        raise BleakError(f"Failed to connect to {self.name}")

    async def get_data(self) -> dict[str, Any]:
        """Read device data."""
        client = await self._get_client()
        try:
            # First, try to get the model number
            try:
                raw_model = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
                model = raw_model.decode("utf-8").strip()
                _LOGGER.info("Successfully read model number: %s for %s", 
                           model, self._device.address)
            except Exception as e:
                _LOGGER.warning("Could not read model number: %s", e)
                model = "Unknown"

            # Now, try to get the register data
            try:
                data = await self._read_registers(client, REG_BATTERY_VOLTAGE, 7)
                parsed_data = self._parse_data(data)
                return {"model_number": model, **parsed_data}
            except Exception as e:
                _LOGGER.warning("Could not read register data: %s", e)
                # Return basic data if register reading fails
                return {
                    "model_number": model,
                    "battery_voltage": None,
                    "solar_voltage": None,
                }
        finally:
            if client.is_connected:
                await client.disconnect()

    async def _read_registers(
        self, client: BleakClient, start_register: int, count: int
    ) -> bytearray:
        """Read a range of registers from the device."""
        # Clear any existing notifications
        while not self._notification_queue.empty():
            try:
                self._notification_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Start listening for notifications
        await client.start_notify(RENOGY_RX_CHAR_UUID, self._notification_handler)

        try:
            # Build the Modbus command
            command = bytearray(
                [0xFF, 0x03, start_register >> 8, start_register & 0xFF, 0x00, count]
            )
            command.extend([0x00, 0x00])  # No CRC for now

            _LOGGER.debug("Sending command: %s", command.hex())

            # Send the command
            await client.write_gatt_char(RENOGY_TX_CHAR_UUID, command, response=True)

            # Wait for response
            response = bytearray()
            try:
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

                _LOGGER.debug("Received response: %s", response.hex())
                return response

            except asyncio.TimeoutError:
                raise BleakError("Timeout waiting for device response")

        finally:
            # Always stop notifications
            try:
                await client.stop_notify(RENOGY_RX_CHAR_UUID)
            except Exception as e:
                _LOGGER.debug("Error stopping notifications: %s", e)

    def _parse_data(self, data: bytearray) -> dict[str, Any]:
        """Parse the raw data from the device."""
        if len(data) < 3 or data[0] != 0xFF or data[1] != 0x03:
            raise ValueError(f"Invalid response header: {data.hex()}")

        data_len = data[2]
        if len(data) < 3 + data_len:
            raise ValueError(
                f"Incomplete response: expected {3+data_len} bytes, got {len(data)}"
            )

        payload = data[3 : 3 + data_len]

        battery_voltage = None
        solar_voltage = None

        if len(payload) >= 2:
            battery_voltage = int.from_bytes(payload[0:2], "big") / 10

        if len(payload) >= 14:
            solar_voltage = int.from_bytes(payload[12:14], "big") / 10

        return {
            "battery_voltage": battery_voltage,
            "solar_voltage": solar_voltage,
        }

    async def disconnect(self):
        """Disconnect from the device."""
        # This is handled automatically by the context manager
        pass

