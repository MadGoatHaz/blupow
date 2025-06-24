"""The BluPow integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# The PLATFORMS list should be empty as we are no longer setting up a sensor platform.
# Home Assistant's MQTT integration will handle sensor creation via discovery.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    # We don't have any platforms to forward to.
    # This integration now only serves as a branding/grouping mechanism
    # and a UI entry point for future configuration.
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Since we are not setting up any platforms, we just return True.
    # If we had listeners, we would remove them here.
    return True 