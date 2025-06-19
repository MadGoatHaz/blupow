"""The DataUpdateCoordinator for the BluPow integration."""
import logging
from datetime import timedelta
from typing import Any

from bleak.exc import BleakError, BleakTimeoutError

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
            name=f"{DOMAIN}_{client._device.address}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Bluetooth device."""
        try:
            return await self.client.get_data()
        except BleakTimeoutError as err:
            _LOGGER.warning("Timeout connecting to device %s: %s", 
                          self.client._device.address, err)
            raise UpdateFailed(f"Connection timeout: {err}") from err
        except BleakError as err:
            _LOGGER.warning("Bluetooth error with device %s: %s", 
                          self.client._device.address, err)
            raise UpdateFailed(f"Bluetooth error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error with device %s: %s", 
                         self.client._device.address, err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

