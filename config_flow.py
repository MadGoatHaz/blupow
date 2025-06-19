"""Config flow for BluPow integration."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BluPowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluPow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to discover and select a device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            
            title = self._discovered_devices.get(address, address)
            return self.async_create_entry(title=title, data={CONF_ADDRESS: address})

        # Discover devices
        current_discoveries = async_discovered_service_info(self.hass, connectable=True)
        for discovery_info in current_discoveries:
            address = discovery_info.address
            name = discovery_info.name
            if name and (
                name.upper().startswith("REGO")
                or name.upper().startswith("RENOGY")
                or name.upper().startswith("BT-")
            ):
                self._discovered_devices[address] = name

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices)}),
        )

