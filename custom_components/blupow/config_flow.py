"""Config flow for BluPow."""
import asyncio
import json
import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
    SelectSelectorMode,
)

from .const import DOMAIN, DEVICE_TYPES

_LOGGER = logging.getLogger(__name__)

# MQTT Topics
COMMAND_TOPIC = "blupow/gateway/command"
RESPONSE_TOPIC_TEMPLATE = "blupow/gateway/response/{request_id}"


class BluPowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluPow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="BluPow Gateway", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow for this handler."""
        return BluPowOptionsFlowHandler(config_entry)


class BluPowOptionsFlowHandler(OptionsFlow):
    """Handle BluPow options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.configured_devices: list[dict[str, Any]] = []
        self.discovered_devices: list[dict[str, Any]] = []
        self.selected_device: dict[str, Any] = {}

    async def _async_gateway_request(self, command: str, **kwargs) -> Any | None:
        """Send a command to the gateway and await a response."""
        request_id = uuid.uuid4().hex
        response_topic = RESPONSE_TOPIC_TEMPLATE.format(request_id=request_id)
        response_queue = asyncio.Queue()

        @callback
        def on_message(msg: ReceiveMessage):
            """Handle incoming MQTT message."""
            _LOGGER.info(f"Received MQTT message on {msg.topic}")
            try:
                response = json.loads(msg.payload)
                _LOGGER.debug(f"Decoded response for {command}: {response}")
                response_queue.put_nowait(response)
            except json.JSONDecodeError:
                _LOGGER.error(f"Failed to decode JSON from gateway response: {msg.payload}")
                response_queue.put_nowait(None)

        _LOGGER.info(f"Subscribing to response topic: {response_topic}")
        unsubscribe = await mqtt.async_subscribe(self.hass, response_topic, on_message, 1)

        try:
            # Add a small delay to ensure the subscription is active before publishing.
            # This prevents a race condition where the gateway responds faster
            # than the broker can establish the subscription for the client.
            await asyncio.sleep(0.1)

            payload = {"command": command, "request_id": request_id, **kwargs}
            _LOGGER.info(f"Publishing command to {COMMAND_TOPIC}: {payload}")
            await mqtt.async_publish(self.hass, COMMAND_TOPIC, json.dumps(payload))
            
            _LOGGER.info(f"Waiting for gateway response for command '{command}'...")
            return await asyncio.wait_for(response_queue.get(), timeout=30.0)

        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout waiting for gateway response to '{command}' command.")
            return None
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred during gateway request '{command}': {e}")
            return None
        finally:
            unsubscribe()

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["discover_devices", "manage_devices"],
        )

    async def async_step_discover_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle device discovery using MQTT."""
        response = await self._async_gateway_request("discover_devices")
        if not response or response.get("status") != "success":
            return self.async_abort(reason="discovery_failed")

        devices = response.get("devices", [])
        if not devices:
            return self.async_abort(reason="no_devices_found")

        self.discovered_devices = devices
        return await self.async_step_select_discovered_device()
    
    async def async_step_manage_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show configured devices and offer removal."""
        if user_input is not None and "devices_to_remove" in user_input:
            devices_to_remove = user_input["devices_to_remove"]
            for address in devices_to_remove:
                _LOGGER.info(f"Requesting removal of device: {address}")
                await self._async_gateway_request("remove_device", address=address)
            return self.async_create_entry(title="", data=None)

        response = await self._async_gateway_request("get_devices")
        if not response or response.get("status") != "success":
            return self.async_abort(reason="get_devices_failed")

        self.configured_devices = response.get("devices", [])
        if not self.configured_devices:
            # Show an empty form with an informational description if no devices are configured.
            return self.async_show_form(
                step_id="manage_devices",
                data_schema=vol.Schema({}),
                description_placeholders={"no_devices": "There are currently no configured devices to manage."},
                last_step=True
            )

        device_choices = [
            SelectOptionDict(value=dev["address"], label=f"{dev.get('name', 'Unknown')} ({dev['address']})")
            for dev in self.configured_devices
        ]

        return self.async_show_form(
            step_id="manage_devices",
            data_schema=vol.Schema({
                vol.Required("devices_to_remove"): SelectSelector(
                    SelectSelectorConfig(options=device_choices, multiple=True, mode=SelectSelectorMode.LIST)
                ),
            }),
            last_step=True,
        )

    async def async_step_select_discovered_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle selection of a discovered device."""
        if user_input is not None:
            address = user_input["selected_device"]
            device_info = next((d for d in self.discovered_devices if d["address"] == address), None)
            if not device_info:
                return self.async_abort(reason="device_not_found")
            
            self.selected_device = device_info
            return await self.async_step_set_device_type()

        device_choices = [
            SelectOptionDict(value=dev["address"], label=f"{dev.get('name', 'Unknown')} ({dev['address']})")
            for dev in self.discovered_devices
        ]

        return self.async_show_form(
            step_id="select_discovered_device",
            data_schema=vol.Schema({
                vol.Required("selected_device"): SelectSelector(
                    SelectSelectorConfig(options=device_choices)
                ),
            }),
        )

    async def async_step_set_device_type(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Ask the user for the type of the selected device."""
        if user_input is not None:
            device_config = self.selected_device.copy()
            device_config["type"] = user_input["device_type"]
            
            if await self._async_add_device_to_gateway(device_config):
                return self.async_create_entry(title="", data={})
            return self.async_abort(reason="add_device_failed")

        device_type_options = [
            SelectOptionDict(value=key, label=key.replace("_", " ").title())
            for key in DEVICE_TYPES
        ]

        return self.async_show_form(
            step_id="set_device_type",
            description_placeholders={"device_name": self.selected_device.get("name", self.selected_device["address"])},
            data_schema=vol.Schema({
                vol.Required("device_type"): SelectSelector(
                    SelectSelectorConfig(options=device_type_options)
                ),
            })
        )

    async def _async_add_device_to_gateway(self, device_config: dict[str, Any]) -> bool:
        """Send an 'add_device' command to the gateway and wait for status."""
        response = await self._async_gateway_request("add_device", **device_config)
        return response is not None and response.get("status") == "success"

    async def async_step_add_device_manually(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Adding a device manually is not supported through this flow."""
        return self.async_abort(reason="not_implemented")

    async def async_step_remove_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Removing a device is not supported through this flow."""
        return self.async_abort(reason="not_implemented")

