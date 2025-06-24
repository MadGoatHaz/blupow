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
        self.discovered_devices: list[dict[str, Any]] = []
        self.selected_device: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["discover_devices"],
        )

    async def async_step_discover_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle device discovery using MQTT."""
        request_id = uuid.uuid4().hex
        response_topic = RESPONSE_TOPIC_TEMPLATE.format(request_id=request_id)
        response_queue = asyncio.Queue()

        @callback
        def on_message(msg: ReceiveMessage):
            """Handle incoming MQTT message."""
            _LOGGER.debug(f"Received discovery response on {msg.topic}: {msg.payload}")
            try:
                response = json.loads(msg.payload)
                if response.get("status") == "success":
                    response_queue.put_nowait(response.get("devices", []))
                else:
                    _LOGGER.error(f"Gateway discovery failed: {response.get('reason')}")
                    response_queue.put_nowait(None)
            except json.JSONDecodeError:
                _LOGGER.error(f"Failed to decode JSON from discovery response: {msg.payload}")
                response_queue.put_nowait(None)

        # Subscribe to the response topic
        unsubscribe = await mqtt.async_subscribe(self.hass, response_topic, on_message, 1)

        try:
            # Publish the discovery request
            discovery_payload = {"command": "discover_devices", "request_id": request_id}
            await mqtt.async_publish(self.hass, COMMAND_TOPIC, json.dumps(discovery_payload))

            _LOGGER.info("Waiting for discovered devices from the gateway...")
            # Wait for the response from the queue with a timeout
            devices = await asyncio.wait_for(response_queue.get(), timeout=15.0)

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout waiting for gateway discovery response.")
            return self.async_abort(reason="discovery_timeout")
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred during discovery: {e}")
            return self.async_abort(reason="unknown_error")
        finally:
            # Always unsubscribe
            unsubscribe()

        if not devices:
            return self.async_abort(reason="no_devices_found")

        self.discovered_devices = devices
        return await self.async_step_select_discovered_device()

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
        request_id = uuid.uuid4().hex
        response_topic = RESPONSE_TOPIC_TEMPLATE.format(request_id=request_id)
        response_queue = asyncio.Queue()

        @callback
        def on_message(msg: ReceiveMessage):
            try:
                response = json.loads(msg.payload)
                response_queue.put_nowait(response.get("status") == "success")
            except json.JSONDecodeError:
                response_queue.put_nowait(False)

        unsubscribe = await mqtt.async_subscribe(self.hass, response_topic, on_message, 1)

        try:
            payload = {"command": "add_device", "request_id": request_id, **device_config}
            await mqtt.async_publish(self.hass, COMMAND_TOPIC, json.dumps(payload))
            
            _LOGGER.info(f"Waiting for gateway to add device {device_config.get('address')}...")
            return await asyncio.wait_for(response_queue.get(), timeout=10.0)

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout waiting for gateway response to add_device command.")
            return False
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred while adding device: {e}")
            return False
        finally:
            unsubscribe()

    async def async_step_add_device_manually(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Adding a device manually is not supported through this flow."""
        return self.async_abort(reason="not_implemented")

    async def async_step_remove_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Removing a device is not supported through this flow."""
        return self.async_abort(reason="not_implemented")

