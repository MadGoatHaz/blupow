import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

class BaseDevice(ABC):
    """Abstract base class for all BluPow device drivers."""

    def __init__(self, address: str, device_type: str):
        """
        Initialize the base device.
        :param address: The MAC address of the device.
        :param device_type: The type of the device (e.g., 'renogy_controller').
        """
        self.mac_address = address.upper()
        self.device_type = device_type

    @abstractmethod
    async def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Connect to the device, retrieve data, and disconnect.
        This method should be implemented by each device driver.
        :return: A dictionary containing the retrieved sensor data, or None if an error occurred.
        """
        pass

    @abstractmethod
    def get_sensor_definitions(self) -> List[Dict[str, Any]]:
        """
        Return a list of sensor definitions for MQTT discovery.
        Each definition should be a dictionary describing a sensor.
        :return: A list of sensor definition dictionaries.
        """
        pass

    def get_device_info(self) -> Dict[str, Any]:
        """
        Return basic information about the device.
        Can be overridden by subclasses for more specific info.
        """
        return {
            "address": self.mac_address,
            "type": self.device_type,
        } 