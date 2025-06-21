"""Config flow for BluPow integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluPow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Manual entry
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME, f"BluPow {address}")
            
            # Validate address format
            if self._is_valid_mac_address(address):
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_ADDRESS: address,
                        CONF_NAME: name,
                    },
                )
            else:
                errors[CONF_ADDRESS] = "invalid_address"

        # Build form schema
        schema = vol.Schema({
            vol.Required(CONF_ADDRESS): str,
            vol.Optional(CONF_NAME): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    def _is_valid_mac_address(self, address: str) -> bool:
        """Validate MAC address format."""
        import re
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        return bool(mac_pattern.match(address))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for BluPow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__()
        # Don't set config_entry explicitly - it's handled by the parent class

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "update_interval",
                    default=self.config_entry.options.get("update_interval", 30),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                vol.Optional(
                    "enable_diagnostics",
                    default=self.config_entry.options.get("enable_diagnostics", False),
                ): bool,
                vol.Optional(
                    "connection_timeout",
                    default=self.config_entry.options.get("connection_timeout", 20),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
            }),
        )

