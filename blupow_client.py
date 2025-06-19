"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from bleak.backends.device import BLEDevice

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

    async def _notification_handler(self, sender: int, data: bytearray):
        """Handle incoming notifications."""
        await self._notification_queue.put(data)

    async def get_data(self) -> dict[str, Any]:
        """Read device data."""
        async with bluetooth.async_get_bleak_client_for_device(
            self._hass, self._device
        ) as client:
            try:
                # First, get the model number
                raw_model = await client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
                model = raw_model.decode("utf-8").strip()
                _LOGGER.info(
                    "Successfully read model number: %s for %s",
                    model,
                    self._device.address,
                )

                # Now, get the rest of the data
                data = await self._read_registers(client, REG_BATTERY_VOLTAGE, 7)
                parsed_data = self._parse_data(data)

                return {"model_number": model, **parsed_data}
            except BleakError as e:
                _LOGGER.warning(
                    "Bluetooth error communicating with %s: %s", self._device.address, e
                )
                raise
            except Exception as e:
                _LOGGER.error(
                    "Unexpected error communicating with %s: %s", self._device.address, e
                )
                raise

    async def _read_registers(
        self, client: BleakClient, start_register: int, count: int
    ) -> bytearray:
        """Read a range of registers from the device."""
        while not self._notification_queue.empty():
            self._notification_queue.get_nowait()

        await client.start_notify(RENOGY_RX_CHAR_UUID, self._notification_handler)

        command = bytearray(
            [0xFF, 0x03, start_register >> 8, start_register & 0xFF, 0x00, count]
        )
        command.extend([0x00, 0x00])  # No CRC for now

        await client.write_gatt_char(RENOGY_TX_CHAR_UUID, command, response=True)

        response = bytearray()
        try:
            notification = await asyncio.wait_for(
                self._notification_queue.get(), timeout=10.0
            )

            if len(notification) < 3 or notification[0] != 0xFF or notification[1] != 0x03:
                raise ValueError(f"Invalid header in first notification: {notification}")

            response.extend(notification)
            expected_payload_len = notification[2]

            while len(response) < 3 + expected_payload_len:
                notification = await asyncio.wait_for(
                    self._notification_queue.get(), timeout=5.0
                )
                response.extend(notification)

        finally:
            await client.stop_notify(RENOGY_RX_CHAR_UUID)

        return response

    def _parse_data(self, data: bytearray) -> dict[str, Any]:
        """Parse the raw data from the device."""
        if len(data) < 3 or data[0] != 0xFF or data[1] != 0x03:
            raise ValueError(f"Invalid response header: {data}")

        data_len = data[2]
        if len(data) < 3 + data_len:
            raise ValueError(
                f"Incomplete response: expected {3+data_len} bytes, got {len(data)}"
            )

        payload = data[3 : 3 + data_len]

        battery_voltage = int.from_bytes(payload[0:2], "big") / 10
        solar_voltage = int.from_bytes(payload[12:14], "big") / 10

        return {
            "battery_voltage": battery_voltage,
            "solar_voltage": solar_voltage,
        }

