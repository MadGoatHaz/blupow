"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

from .const import (
    MODEL_NUMBER_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_TX_CHAR_UUID,
    REG_BATTERY_SOC,
    REG_BATTERY_VOLTAGE,
    REG_SOLAR_VOLTAGE,
)

_LOGGER = logging.getLogger(__name__)


class BluPowClient:
    """A client to handle reading data from a Renogy device."""

    def __init__(self, device: BLEDevice):
        """Initialize the BluPowClient."""
        self._device = device
        self._notification_queue: asyncio.Queue[bytearray] = asyncio.Queue()
        self._max_retries = 3

    def name(self) -> str:
        """Return the name of the device."""
        return self._device.name or self._device.address

    async def _notification_handler(self, sender: int, data: bytearray):
        """Handle incoming notifications."""
        await self._notification_queue.put(data)

    async def get_data(self) -> dict[str, Any]:
        """Read device data."""
        async with BleakClient(self._device) as client:
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
                # Read a larger block of data starting from the lowest register address
                data = await self._read_registers(client, REG_BATTERY_SOC, 10)
                parsed_data = self._parse_data(data)
                return {"model_number": model, **parsed_data}
            except Exception as e:
                _LOGGER.warning("Could not read register data: %s", e)
                # Return basic data if register reading fails
                return {
                    "model_number": model,
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

        def get_value(reg_offset: int, multiplier: float = 1.0) -> float | None:
            """Safely extract and scale a value from the payload."""
            start = (reg_offset - REG_BATTERY_SOC) * 2
            if start + 2 <= len(payload):
                raw_value = int.from_bytes(payload[start : start + 2], "big")
                return raw_value * multiplier
            return None

        return {
            "battery_soc": get_value(0x0100),
            "battery_voltage": get_value(0x0101, 0.1),
            "battery_current": get_value(0x0102, 0.01),
            "battery_temp": get_value(0x0103),  # Needs special parsing for temp
            "solar_voltage": get_value(0x0107, 0.1),
            "solar_current": get_value(0x0108, 0.01),
            "solar_power": get_value(0x0109),
        }

    async def disconnect(self):
        """Disconnect from the device."""
        # This is handled automatically by the context manager
        pass

