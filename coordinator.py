"""Data update coordinator for the BluPow integration."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .blupow_client import BluPowClient

_LOGGER = logging.getLogger(__name__)


class BluPowDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching BluPow data."""

    def __init__(self, hass: HomeAssistant, client: BluPowClient) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="BluPow",
            update_interval=30,  # Update every 30 seconds
        )
        self.client = client
        self.ble_device = client._device
        
        # Initialize with default data to prevent None errors
        self._data = {
            "model_number": "Unknown",
            "battery_voltage": None,
            "solar_voltage": None,
            "battery_current": None,
            "solar_current": None,
            "battery_soc": None,
            "battery_temp": None,
            "solar_power": None,
        }

    @property
    def data(self) -> dict[str, Any]:
        """Return the data."""
        return self._data

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via BluPow client."""
        try:
            _LOGGER.info("Attempting to fetch data from BluPow device")
            data = await self.client.get_data()
            if data:
                self._data.update(data)
                _LOGGER.info("Successfully fetched data: %s", data)
            else:
                _LOGGER.warning("No data received from BluPow device")
            return self._data
        except Exception as err:
            _LOGGER.error("Error fetching BluPow data: %s", err)
            # Keep existing data on error
            return self._data

