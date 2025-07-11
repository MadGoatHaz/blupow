"""
BluPow - Renogy Inverter Integration for Home Assistant

This integration provides comprehensive monitoring of Renogy RIV1230RCH-SPS 
inverter chargers via Bluetooth Low Energy (BLE) communication.

Features:
- 22 real-time sensor readings
- Energy dashboard integration
- Automatic device discovery
- Robust connection handling
"""
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .blupow_client import BluPowClient
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .coordinator import BluPowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    address = entry.data[CONF_ADDRESS]
    _LOGGER.info("Setting up BluPow integration for address: %s", address)

    # First, check if the device is available
    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), connectable=True)
    if not ble_device:
        _LOGGER.warning("Could not find BLE device with address %s. Retrying setup.", address)
        raise ConfigEntryNotReady(f"Could not find BLE device with address {address}")

    _LOGGER.info("Found BLE device: %s", ble_device.name)
        
    try:
        # Create the coordinator with the MAC address (it will create its own client)
        coordinator = BluPowDataUpdateCoordinator(
            hass, 
            address,
        )
        _LOGGER.info("Created BluPow coordinator")
        
        # Verify coordinator is properly initialized
        if not coordinator:
            _LOGGER.error("Failed to create coordinator")
            raise ConfigEntryNotReady("Failed to create coordinator")
        
        # Ensure we have initial data before setting up platforms
        _LOGGER.info("Performing initial coordinator refresh")
        await coordinator.async_config_entry_first_refresh()
        
        # Verify coordinator has data
        if not hasattr(coordinator, 'data') or coordinator.data is None:
            _LOGGER.error("Coordinator data is None after initialization")
            raise ConfigEntryNotReady("Coordinator data is None after initialization")
        
        _LOGGER.info("Coordinator initialized successfully with data: %s", coordinator.data)

        entry.runtime_data = coordinator

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("BluPow integration setup completed successfully")

        return True
        
    except Exception as err:
        _LOGGER.error("Failed to set up BluPow integration: %s", err)
        raise ConfigEntryNotReady(f"Failed to set up BluPow integration: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        pass

    return unload_ok

