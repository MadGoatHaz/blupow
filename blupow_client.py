"""API client for interacting with Renogy Bluetooth devices."""
import asyncio
import logging
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

from .const import MODEL_NUMBER_CHAR_UUID

_LOGGER = logging.getLogger(__name__)


class BluPowClient:
    """A client to handle a persistent BLE connection to a Renogy device."""

    def __init__(self, device: BLEDevice):
        """Initialize the BluPowClient."""
        self._device = device
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if the client is currently connected."""
        return self._client is not None and self._client.is_connected

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
                raw_model = await self._client.read_gatt_char(MODEL_NUMBER_CHAR_UUID)
                model = raw_model.decode("utf-8").strip()
                _LOGGER.info("Successfully read model number: %s", model)
                return {"model_number": model}
            except Exception as e:
                _LOGGER.error("Failed to read device data: %s", e)
                # In case of error, return a specific error value
                return {"model_number": "Read Error"}

    async def _ensure_connected(self) -> bool:
        """Ensures the client is connected, trying to reconnect if necessary."""
        if self.is_connected:
            return True
        return await self.connect()

