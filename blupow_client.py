"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any

from bleak import BleakClient, BleakError
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
    """A client to handle a persistent BLE connection to a Renogy device."""

    def __init__(self, device: BLEDevice):
        """Initialize the BluPowClient."""
        self._device = device
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._notification_queue = asyncio.Queue()

    @property
    def is_connected(self) -> bool:
        """Return True if the client is currently connected."""
        return self._client is not None and self._client.is_connected

    async def _notification_handler(self, sender: int, data: bytearray):
        """Handle incoming notifications."""
        await self._notification_queue.put(data)

    async def connect(self) -> bool:
        """Establish a persistent connection."""
        _LOGGER.info("Attempting to connect to %s", self._device.address)
        async with self._lock:
            if self.is_connected:
                return True
            try:
                self._client = BleakClient(self._device)
                await self._client.connect()
                _LOGGER.info("Successfully connected to %s", self._device.address)
                return True
            except (BleakError, asyncio.TimeoutError) as e:
                _LOGGER.error("Failed to connect to %s: %s", self._device.address, e)
                self._client = None
                return False

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if not self.is_connected:
            return
        _LOGGER.info("Disconnecting from %s", self._device.address)
        async with self._lock:
            if self._client:
                await self._client.disconnect()
            self._client = None

    async def get_data(self) -> dict[str, Any]:
        """Read device data."""
        async with self._lock:
            if not await self._ensure_connected():
                raise BleakError("Could not connect to the device.")

            try:
                # First, get the model number
                raw_model = await self._client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
                model = raw_model.decode("utf-8").strip()
                _LOGGER.info("Successfully read model number: %s", model)
                
                # Now, get the rest of the data
                data = await self._read_registers(REG_BATTERY_VOLTAGE, 7) # Read 7 registers starting from battery voltage
                
                parsed_data = self._parse_data(data)

                return {"model_number": model, **parsed_data}
            except Exception as e:
                _LOGGER.error("Failed to read device data: %s", e)
                raise BleakError(f"Failed to read device data: {e}") from e

    async def _read_registers(self, start_register: int, count: int) -> bytearray:
        """Read a range of registers from the device."""
        await self._client.start_notify(RENOGY_RX_CHAR_UUID, self._notification_handler)
        
        # Command to read registers
        # Format: ff 03 <start_reg_high> <start_reg_low> <count_high> <count_low> <crc>
        command = bytearray([0xff, 0x03, start_register >> 8, start_register & 0xff, 0x00, count])
        # For now, we don't calculate CRC. The device seems to work without it.
        # This is not ideal and should be fixed in the future.
        command.extend([0x00, 0x00])

        await self._client.write_gatt_char(RENOGY_TX_CHAR_UUID, command, response=True)
        
        response = bytearray()
        try:
            while True:
                notification = await asyncio.wait_for(self._notification_queue.get(), timeout=5.0)
                response.extend(notification)
                # The response ends when the length is as expected.
                # The first 3 bytes are header, then 2 bytes per register.
                if len(response) >= 3 + count * 2:
                    break
        finally:
            await self._client.stop_notify(RENOGY_RX_CHAR_UUID)

        return response

    def _parse_data(self, data: bytearray) -> dict[str, Any]:
        """Parse the raw data from the device."""
        # ff 03 0e <data> <crc>
        if len(data) < 3 or data[0] != 0xff or data[1] != 0x03:
            raise ValueError("Invalid response from device")

        data_len = data[2]
        if len(data) < 3 + data_len:
            raise ValueError("Incomplete response from device")

        payload = data[3:3 + data_len]
        
        # For now, we only parse battery and solar voltage
        battery_voltage = int.from_bytes(payload[0:2], "big") / 10
        solar_voltage = int.from_bytes(payload[12:14], "big") / 10 # 0x0107 is 6 registers after 0x0101
        
        return {
            "battery_voltage": battery_voltage,
            "solar_voltage": solar_voltage,
        }

    async def _ensure_connected(self) -> bool:
        """Ensures the client is connected, trying to reconnect if necessary."""
        if self.is_connected:
            return True
        return await self.connect()

