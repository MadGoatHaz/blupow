"""Data update coordinator for the BluPow integration."""
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .blupow_client import BluPowClient

_LOGGER = logging.getLogger(__name__)


class BluPowDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching BluPow data with comprehensive error handling."""

    def __init__(self, hass: HomeAssistant, client: BluPowClient) -> None:
        """Initialize with comprehensive error handling."""
        try:
            super().__init__(
                hass,
                _LOGGER,
                name="BluPow",
                update_interval=30,  # Update every 30 seconds
            )
            
            self.client = client
            self.ble_device = client._device if client else None
            
            # Initialize with default data structure to prevent None errors
            self._data = self._get_default_data()
            
            _LOGGER.info("BluPow coordinator initialized successfully")
            _LOGGER.debug("BLE device: %s", self.ble_device)
            _LOGGER.debug("Initial data: %s", self._data)
            
        except Exception as err:
            _LOGGER.error("Failed to initialize BluPow coordinator: %s", err)
            # Ensure we have basic data even on initialization failure
            self._data = self._get_default_data()
            raise

    def _get_default_data(self) -> Dict[str, Any]:
        """Get default data structure."""
        return {
            "model_number": "Unknown",
            "battery_voltage": None,
            "solar_voltage": None,
            "battery_current": None,
            "solar_current": None,
            "battery_soc": None,
            "battery_temp": None,
            "solar_power": None,
            "connection_status": "disconnected",
            "last_update": None,
            "error_count": 0,
        }

    @property
    def data(self) -> Dict[str, Any]:
        """Return the data with safety checks."""
        try:
            # Ensure _data attribute exists and is not None
            if not hasattr(self, '_data') or self._data is None:
                _LOGGER.warning("Data not initialized, creating default data")
                self._data = self._get_default_data()
            
            # Double-check that we have a valid dictionary
            if not isinstance(self._data, dict):
                _LOGGER.error("Data is not a dictionary, resetting to default")
                self._data = self._get_default_data()
            
            _LOGGER.debug("Returning coordinator data: %s", self._data)
            return self._data
            
        except Exception as err:
            _LOGGER.error("Error accessing coordinator data: %s", err)
            # Create a fresh default data structure
            self._data = self._get_default_data()
            return self._data

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via BluPow client with comprehensive error handling."""
        try:
            _LOGGER.info("Starting BluPow data update")
            
            # Ensure we have valid data structure
            if not hasattr(self, '_data') or self._data is None:
                self._data = self._get_default_data()
            
            # Check if client is available
            if not self.client:
                _LOGGER.error("BluPow client not available")
                self._update_error_status("Client not available")
                return self._data
            
            # Attempt to fetch data
            _LOGGER.debug("Attempting to fetch data from BluPow device")
            data = await self.client.get_data()
            
            if data and isinstance(data, dict):
                # Update data with new values
                self._data.update(data)
                self._data["connection_status"] = "connected"
                self._data["last_update"] = "success"
                self._data["error_count"] = 0
                
                _LOGGER.info("Successfully fetched BluPow data: %s", data)
                _LOGGER.debug("Updated data keys: %s", list(data.keys()))
                
            else:
                _LOGGER.warning("No valid data received from BluPow device")
                self._data["connection_status"] = "no_data"
                self._data["last_update"] = "no_data"
                self._data["error_count"] += 1
                
            return self._data
            
        except Exception as err:
            _LOGGER.error("Error fetching BluPow data: %s", err)
            self._update_error_status(str(err))
            return self._data

    def _update_error_status(self, error_message: str) -> None:
        """Update error status in data."""
        try:
            # Ensure we have valid data structure
            if not hasattr(self, '_data') or self._data is None:
                self._data = self._get_default_data()
            
            self._data["connection_status"] = "error"
            self._data["last_update"] = "error"
            self._data["error_count"] += 1
            self._data["last_error"] = error_message
            
            _LOGGER.debug("Updated error status: %s (count: %d)", 
                         error_message, self._data["error_count"])
                         
        except Exception as err:
            _LOGGER.error("Error updating error status: %s", err)

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information with error handling."""
        try:
            if not self.ble_device:
                return {
                    "name": "BluPow Device",
                    "address": "unknown",
                    "model": "Unknown",
                }
            
            return {
                "name": self.ble_device.name or "BluPow Device",
                "address": self.ble_device.address or "unknown",
                "model": self._data.get("model_number", "Unknown"),
            }
            
        except Exception as err:
            _LOGGER.error("Error getting device info: %s", err)
            return {
                "name": "BluPow Device",
                "address": "unknown",
                "model": "Unknown",
            }

    def get_connection_status(self) -> str:
        """Get current connection status."""
        try:
            return self._data.get("connection_status", "unknown")
        except Exception as err:
            _LOGGER.error("Error getting connection status: %s", err)
            return "error"

    def get_error_count(self) -> int:
        """Get current error count."""
        try:
            return self._data.get("error_count", 0)
        except Exception as err:
            _LOGGER.error("Error getting error count: %s", err)
            return 0

