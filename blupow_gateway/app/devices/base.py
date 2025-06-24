import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
import logging

_LOGGER = logging.getLogger(__name__)

class BaseDevice(ABC):
    """Abstract base class for all BluPow device drivers."""

    def __init__(self, address: str, device_type: str, ble_device: Optional[BLEDevice] = None):
        """
        Initialize the base device.
        :param address: The MAC address of the device.
        :param device_type: The type of the device (e.g., 'renogy_controller').
        :param ble_device: An optional, cached BLEDevice object from a discovery scan.
        """
        self._address = address.upper()
        self._device_type = device_type
        self._client: Optional[BleakClient] = None
        self._ble_device = ble_device # Cache the discovered device object

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._client is not None and self._client.is_connected

    @property
    def mac_address(self) -> str:
        """The MAC address of the device."""
        return self._address

    @property
    def device_type(self) -> str:
        """The type of the device."""
        return self._device_type

    async def connect(self, retries=3, delay=2) -> bool:
        """Establish a connection to the device with retries."""
        for attempt in range(retries):
            try:
                if self._client and self._client.is_connected:
                    _LOGGER.debug(f"[{self.mac_address}] Already connected.")
                    return True
                
                _LOGGER.info(f"[{self.mac_address}] Attempting to connect (Attempt {attempt + 1}/{retries})...")
                
                # Use the cached BLEDevice object if available, otherwise scan
                device_to_connect = self._ble_device
                if not device_to_connect:
                    _LOGGER.debug(f"[{self.mac_address}] No cached device, scanning for address...")
                    device_to_connect = await BleakScanner.find_device_by_address(self.mac_address, timeout=10.0)
                
                if not device_to_connect:
                    _LOGGER.warning(f"[{self.mac_address}] Device not found.")
                    raise BleakError(f"Device {self.mac_address} not found")
                
                self._client = BleakClient(device_to_connect)
                await self._client.connect()
                _LOGGER.info(f"[{self.mac_address}] Connection successful.")
                return True
            except BleakError as e:
                _LOGGER.error(f"[{self.mac_address}] Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
        
        _LOGGER.error(f"[{self.mac_address}] All connection attempts failed.")
        return False
    
    async def disconnect(self):
        """Disconnect the BleakClient if it's connected."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            _LOGGER.info(f"[{self.mac_address}] Disconnected.")
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

    def get_config(self) -> Dict[str, Any]:
        """Return the serializable configuration for the device."""
        return {
            "address": self.mac_address,
            "type": self.device_type,
        }

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