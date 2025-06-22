"""Config flow for BluPow."""
import logging
from typing import Any
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import mqtt
import json
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_DEVICE_TYPE

_LOGGER = logging.getLogger(__name__)

MQTT_COMMAND_TOPIC = "blupow/command"


class BluPowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluPow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_ADDRESS], data=user_input)

        current_addresses = self._async_current_ids()
        
        # Get all bluetooth service infos
        service_infos = async_discovered_service_info(self.hass)
        
        discovered_devices = {}
        for service_info in service_infos:
            # We assume Renogy devices will have a name starting with BT
            if service_info.name.startswith("BT") and service_info.address not in current_addresses:
                discovered_devices[service_info.address] = service_info.name

        if not discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(discovered_devices)}
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

