"""The BluPow: Renogy Bluetooth integration."""
import logging

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_get_scanner,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import BluPowDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    address = entry.data[CONF_ADDRESS]
    _LOGGER.info("Setting up BluPow entry for %s", address)
    
    scanner = async_get_scanner(hass)
    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find BLE device with address {address}"
        )

    coordinator = BluPowDataUpdateCoordinator(hass, ble_device)

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

