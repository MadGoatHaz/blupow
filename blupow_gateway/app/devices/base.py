import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

class BaseDevice(ABC):
    """Abstract base class for all BluPow device drivers."""

    def __init__(self, address: str, device_type: str):
        """
        Initialize the base device.
        :param address: The MAC address of the device.
        :param device_type: The type of the device (e.g., 'renogy_controller').
        """
        self._address = address.upper()
        self._device_type = device_type
        self._client: Optional[BleakClient] = None
        self._client_last_used: datetime = datetime.min
        self.CONNECTION_CACHE_SECONDS = 60 # Cache connection for 60 seconds

    @property
    def mac_address(self) -> str:
        """The MAC address of the device."""
        return self._address

    @property
    def device_type(self) -> str:
        """The type of the device."""
        return self._device_type

    async def _get_bleak_client(self) -> BleakClient:
        """Get a cached or new BleakClient."""
        if self._client and self._client.is_connected and \
           (datetime.now() - self._client_last_used) < timedelta(seconds=self.CONNECTION_CACHE_SECONDS):
            _LOGGER.debug(f"[{self.mac_address}] Reusing cached BLE connection.")
            self._client_last_used = datetime.now()
            return self._client

        # If client is old or disconnected, create a new one
        await self._disconnect() # Ensure old client is cleaned up
        _LOGGER.info(f"[{self.mac_address}] Establishing new BLE connection.")
        device = await BleakScanner.find_device_by_address(self.mac_address, timeout=10.0)
        if not device:
            raise BleakError(f"Device {self.mac_address} not found")
        
        self._client = BleakClient(device)
        assert self._client is not None # Satisfy the linter
        await self._client.connect()
        self._client_last_used = datetime.now()
        _LOGGER.info(f"[{self.mac_address}] New connection established.")
        return self._client
    
    async def _disconnect(self):
        """Disconnect the BleakClient if it's connected."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            _LOGGER.info(f"[{self.mac_address}] Connection released.")
        self._client = None

    @abstractmethod
    async def poll(self) -> Optional[Dict[str, Any]]:
        """
        Poll the device for its current state and data.
        This method should handle connection, data retrieval, and disconnection.
        It must be implemented by all subclasses.

        Returns:
            A dictionary containing sensor keys and their values, or None if polling fails.
        """
        raise NotImplementedError

    @abstractmethod
    def get_sensor_definitions(self) -> List[Dict[str, Any]]:
        """
        Return a list of sensor definitions for MQTT discovery.
        Each definition should be a dictionary describing a sensor.
        :return: A list of sensor definition dictionaries.
        """
        pass

    def get_device_name(self) -> str:
        """Return a user-friendly name for the device."""
        return f"{self.device_type.replace('_', ' ').title()} ({self.mac_address[-5:]})"

    def get_device_info(self) -> Dict[str, Any]:
        """
        Return basic information about the device.
        Can be overridden by subclasses for more specific info.
        """
        return {
            "address": self.mac_address,
            "type": self.device_type,
        }

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the device."""
        raise NotImplementedError 