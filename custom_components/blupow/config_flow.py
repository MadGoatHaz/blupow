"""Config flow for BluPow."""
from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
import json

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BluPowConfigFlow(ConfigFlow, domain=DOMAIN):
    """A simple flow to mark that the BluPow integration is active."""
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step."""
        # Check if an entry is already configured. We only need one.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # There is no data to store, we just create the entry.
            return self.async_create_entry(title="BluPow Gateway Listener", data={})

        # Show a simple form to the user to confirm installation.
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BluPowOptionsFlowHandler(config_entry)


class BluPowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for BluPow. This is the "Configure" button handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_show_menu(
            step_id="init", menu_options=["add_device", "remove_device"]
        )

    async def async_step_add_device(self, user_input=None):
        """Handle adding a device."""
        if user_input is not None:
            _LOGGER.info(f"Adding device: {user_input['address']}")
            await self._publish_gateway_command("add_device", user_input)
            return self.async_create_entry(title="", data={})
    
        # Form to collect MAC and device type.
        # Ideally, the list of types would be fetched from the gateway itself.
        # For now, we'll hardcode the known ones.
        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema({
                vol.Required("address"): str,
                vol.Required("type"): vol.In(['renogy_controller', 'generic_modbus_device', 'renogy_inverter'])
            })
        )
    
    async def async_step_remove_device(self, user_input=None):
        """Handle removing a device."""
        if user_input is not None:
            _LOGGER.info(f"Removing device: {user_input['address']}")
            await self._publish_gateway_command("remove_device", user_input)
            return self.async_create_entry(title="", data={})

        # In a real implementation, we would fetch the list of configured
        # devices from the gateway to present here. For now, just a text box.
        return self.async_show_form(
            step_id="remove_device",
            data_schema=vol.Schema({
                vol.Required("address"): str,
            })
        )

    async def _publish_gateway_command(self, command: str, payload: dict[str, Any]):
        """Publish a command to the BluPow gateway."""
        topic = "blupow/gateway/command"
        # Add a request_id for potential future response matching
        full_payload = {"command": command, **payload, "request_id": self.config_entry.entry_id}
        
        _LOGGER.debug(f"Publishing to {topic}: {full_payload}")
        await self.hass.components.mqtt.async_publish(
            self.hass, topic, json.dumps(full_payload), qos=2, retain=False
        )

