"""The BluPow integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # The gateway is responsible for managing its own devices.
    # The HA integration is just a passive listener for the MQTT topics.
    # We no longer send a command from here.

    # Forward the setup to the sensor platform.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # We no longer send a "remove_device" command. Unloading the entities
    # is sufficient. The gateway will persist its own device list.
    
    # Unload the sensor platform
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS) 