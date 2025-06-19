"""The DataUpdateCoordinator for the BluPow integration."""
import logging
from datetime import timedelta
from typing import Any

from bleak.exc import BleakError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .blupow_client import BluPowClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)


class BluPowDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages polling for data and coordinating updates."""

    def __init__(self, hass: HomeAssistant, client: BluPowClient):
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{client.name}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Bluetooth device."""
        try:
            return await self.client.get_data()
        except BleakError as err:
            raise UpdateFailed(f"Failed to communicate with device: {err}") from err

