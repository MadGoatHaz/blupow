"""The BluPow integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# The PLATFORMS list is empty because sensors are created by the MQTT discovery mechanism,
# not by a platform within this integration. This integration's role is to provide a UI
# for configuring which devices the gateway should monitor.
PLATFORMS: list[str] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    # Store an empty dictionary for this config entry, if it doesn't exist.
    # This can be used to store any runtime data.
    hass.data.setdefault(DOMAIN, {})

    # This sets up the options flow handler.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # No platforms to unload, so we just return True.
    # The options listener is automatically removed by Home Assistant.
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id) 