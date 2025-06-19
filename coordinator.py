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
            update_interval=None,  # We'll update manually for now
        )
        self.client = client
        self.ble_device = client._device

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via BluPow client."""
        try:
            _LOGGER.info("Attempting to fetch data from BluPow device")
            data = await self.client.get_data()
            _LOGGER.info("Successfully fetched data: %s", data)
            return data
        except Exception as err:
            _LOGGER.error("Error fetching BluPow data: %s", err)
            # Return empty data instead of raising
            return {
                "model_number": "Unknown",
                "battery_voltage": None,
                "solar_voltage": None,
                "battery_current": None,
                "solar_current": None,
                "battery_soc": None,
                "battery_temp": None,
                "solar_power": None,
            }

