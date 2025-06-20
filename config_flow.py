"""Config flow for BluPow integration with enhanced device discovery."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Device discovery integration
try:
    from .device_discovery_system import BluPowDeviceDiscoverySystem
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False
    _LOGGER.warning("Device discovery system not available")

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluPow."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices = {}
        self.discovery_system = None
        if DISCOVERY_AVAILABLE:
            self.discovery_system = BluPowDeviceDiscoverySystem()

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if user_input.get("use_discovery", False):
                return await self.async_step_discovery()
            else:
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
        
        # Add discovery option if available
        if DISCOVERY_AVAILABLE:
            schema = schema.extend({
                vol.Optional("use_discovery", default=False): bool,
            })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "discovery_note": "Enable device discovery to automatically find Renogy devices" if DISCOVERY_AVAILABLE else ""
            }
        )

    async def async_step_discovery(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle device discovery step."""
        if not DISCOVERY_AVAILABLE:
            return await self.async_step_user()

        if user_input is not None:
            selected_address = user_input["device"]
            device_info = self.discovered_devices.get(selected_address)
            
            if device_info:
                await self.async_set_unique_id(selected_address)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=device_info.name,
                    data={
                        CONF_ADDRESS: selected_address,
                        CONF_NAME: device_info.name,
                        "device_type": device_info.device_type,
                        "recommendation_score": device_info.recommendation_score,
                    },
                )

        # Run device discovery
        try:
            _LOGGER.info("Running BluPow device discovery...")
            devices = await self.discovery_system.comprehensive_scan(duration=15.0)
            
            # Filter for Renogy devices only
            renogy_devices = {addr: info for addr, info in devices.items() if info.is_renogy}
            
            if not renogy_devices:
                return self.async_show_form(
                    step_id="discovery_failed",
                    data_schema=vol.Schema({}),
                    errors={"base": "no_devices_found"},
                    description_placeholders={
                        "troubleshooting": "No Renogy devices found. Try manual entry or check device power/proximity."
                    }
                )
            
            # Test connectivity for discovered devices
            await self.discovery_system.test_connectivity()
            
            self.discovered_devices = renogy_devices
            
            # Sort devices by recommendation score
            sorted_devices = sorted(
                renogy_devices.items(),
                key=lambda x: x[1].recommendation_score,
                reverse=True
            )
            
            # Create device selection options
            device_options = {}
            for address, device_info in sorted_devices:
                connection_status = "✅ Ready" if device_info.connectable else "⚠️ Needs testing"
                signal_quality = "📶 Excellent" if device_info.rssi > -60 else "📶 Good" if device_info.rssi > -75 else "📶 Fair"
                
                device_options[address] = f"{device_info.name} - {connection_status} - {signal_quality} ({device_info.rssi}dBm) - Score: {device_info.recommendation_score}/100"
            
            return self.async_show_form(
                step_id="discovery",
                data_schema=vol.Schema({
                    vol.Required("device"): vol.In(device_options),
                }),
                description_placeholders={
                    "devices_found": f"Found {len(renogy_devices)} Renogy device(s)",
                    "recommendation": "Devices are ranked by compatibility and signal strength. Choose the highest scored device for best results."
                }
            )
            
        except Exception as e:
            _LOGGER.error(f"Device discovery failed: {e}")
            return self.async_show_form(
                step_id="discovery_failed",
                data_schema=vol.Schema({}),
                errors={"base": "discovery_failed"},
                description_placeholders={
                    "error": str(e)
                }
            )

    async def async_step_discovery_failed(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle discovery failure."""
        return await self.async_step_user()

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
        self.config_entry = config_entry

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

