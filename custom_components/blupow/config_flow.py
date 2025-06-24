"""Config flow for BluPow."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
import voluptuous as vol
import json
import asyncio
import uuid
from contextlib import asynccontextmanager

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    CONN_CLASS_LOCAL_PUSH,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS, CONF_NAME, CONF_TYPE
from homeassistant.core import callback, HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEVICE_TYPES

from homeassistant.components import mqtt
from homeassistant.components.mqtt import MQTTMessage

_LOGGER = logging.getLogger(__name__)
GATEWAY_COMMAND_TOPIC = "blupow/gateway/command"
GATEWAY_RESPONSE_TOPIC_BASE = "blupow/gateway/response"


@asynccontextmanager
async def gateway_request(hass: HomeAssistant, command: str, payload: Optional[Dict] = None, timeout: int = 10):
    """A context manager to send a request to the gateway and await a response."""
    request_id = str(uuid.uuid4())
    response_topic = f"{GATEWAY_RESPONSE_TOPIC_BASE}/{request_id}"
    response_received = asyncio.Event()
    response_payload = {"status": "failure", "reason": "timeout"}

    @callback
    def on_message(msg: MQTTMessage):
        """Handle the one-time response message."""
        try:
            nonlocal response_payload
            response_payload = json.loads(msg.payload)
        except json.JSONDecodeError:
            response_payload = {"status": "failure", "reason": "invalid_json"}
        finally:
            response_received.set()

    unsubscribe = await mqtt.async_subscribe(hass, response_topic, on_message, qos=0)

    try:
        command_payload = payload or {}
        command_payload["command"] = command
        command_payload["request_id"] = request_id
        await mqtt.async_publish(hass, GATEWAY_COMMAND_TOPIC, json.dumps(command_payload))

        try:
            await asyncio.wait_for(response_received.wait(), timeout)
        except asyncio.TimeoutError:
            _LOGGER.warning(f"Timeout waiting for gateway response for command '{command}' (Req ID: {request_id})")
            # response_payload is already set to timeout
        
        yield response_payload

    finally:
        unsubscribe()


class BluPowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for BluPow."""
    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial user step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Create a single placeholder entry. All devices will be managed via this one entry's options flow.
        return self.async_create_entry(title="BluPow", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return BluPowOptionsFlowHandler(config_entry)


class BluPowOptionsFlowHandler(OptionsFlow):
    """Handles the options flow for managing BluPow devices."""

    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry
        self.discovered_devices: list[dict] = []
        self.device_info: Optional[Dict[str, Any]] = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show the main menu for device management."""
        return self.async_show_menu(
            step_id="init", menu_options=["discover", "manual", "remove"]
        )

    # --- Discovery Flow ---
    async def async_step_discover(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step to trigger discovery and show results."""
        return await self.async_step_discover_wait()

    async def async_step_discover_wait(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Wait for discovery results from the gateway."""
        _LOGGER.info("Starting device discovery")
        try:
            async with gateway_request(self.hass, "discover_devices") as result:
                if result.get("status") == "success":
                    self.discovered_devices = result.get("devices", [])
                    _LOGGER.info(f"Discovery successful, found {len(self.discovered_devices)} devices.")
                    return await self.async_step_select_discovered_device()
                else:
                    _LOGGER.error(f"Discovery failed in gateway: {result.get('reason', 'unknown')}")
                    return self.async_abort(reason="discovery_failed")
        except Exception:
            _LOGGER.exception("Exception during discovery.")
            return self.async_abort(reason="discovery_exception")

    async def async_step_select_discovered_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Allow the user to select a device from the discovered list."""
        if not self.discovered_devices:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            # Find the full device info from the discovered list
            self.device_info = next((d for d in self.discovered_devices if d["address"] == address), None)
            if self.device_info:
                return await self.async_step_add_device()
            # If device not found (shouldn't happen), abort.
            return self.async_abort(reason="unknown_error")

        device_options = {
            device["address"]: f"{device.get('name', 'Unknown')} ({device['address']})"
            for device in self.discovered_devices
        }

        return self.async_show_form(
            step_id="select_discovered_device",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(device_options)}),
            description_placeholders={"device_count": len(self.discovered_devices)},
            last_step=False,
        )

    # --- Manual Add Flow ---
    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Allow manual entry of a device."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.device_info = user_input
            return await self.async_step_add_device()

        schema = {
            vol.Required(CONF_ADDRESS): str,
            vol.Required(CONF_TYPE): vol.In(DEVICE_TYPES),
            vol.Optional(CONF_NAME): str,
        }
        return self.async_show_form(step_id="manual", data_schema=vol.Schema(schema))

    # --- Shared Add Logic ---
    async def async_step_add_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Shared logic to add a device via the gateway."""
        errors: Dict[str, str] = {}
        
        if self.device_info is None:
            return self.async_abort(reason="unknown_error")
        
        try:
            payload = {
                "address": self.device_info[CONF_ADDRESS],
                "type": self.device_info.get(CONF_TYPE, "renogy_inverter"), # Default for discovered devices
                "name": self.device_info.get(CONF_NAME),
            }
            async with gateway_request(self.hass, "add_device", payload) as result:
                if result.get("status") == "success":
                    return self.async_create_entry(title="", data={}) # Finishes the options flow
                
                reason = result.get('reason', 'add_failed')
                _LOGGER.error(f"Failed to add device {payload['address']}: {reason}")
                if reason == 'already_exists':
                     errors["base"] = "device_already_configured"
                else:
                     errors["base"] = "add_failed"

        except Exception:
            _LOGGER.exception("Exception while adding device.")
            errors["base"] = "add_exception"
        
        # If we are here, it means adding failed. We need to show the form again.
        # Let's determine which flow we came from to show the correct form.
        # For simplicity now, we'll just abort with a generic message.
        # A more advanced implementation would re-show the form with an error.
        return self.async_abort(reason=errors.get("base", "add_failed"))

    # --- Remove Flow ---
    async def async_step_remove(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Fetch the list of devices that can be removed."""
        _LOGGER.debug("Attempting to fetch devices for removal")
        try:
            async with gateway_request(self.hass, "get_devices") as result:
                if result.get("status") == "success":
                    self.discovered_devices = result.get("devices", [])
                    if not self.discovered_devices:
                        return self.async_abort(reason="no_devices_configured")
                    return await self.async_step_select_device_to_remove()
                else:
                    _LOGGER.error(f"get_devices failed: {result.get('reason')}")
                    return self.async_abort(reason="get_devices_failed")
        except Exception:
            _LOGGER.exception("Exception during get_devices call.")
            return self.async_abort(reason="get_devices_failed")

    async def async_step_select_device_to_remove(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show the list of devices and handle removal."""
        if user_input is not None:
            address_to_remove = user_input[CONF_ADDRESS]
            payload = {"address": address_to_remove}
            try:
                async with gateway_request(self.hass, "remove_device", payload) as result:
                    if result.get("status") == "success":
                        return self.async_create_entry(title="", data={}) # Finish the flow
                    else:
                        _LOGGER.error(f"Failed to remove device: {result.get('reason')}")
                        return self.async_abort(reason="remove_failed")
            except Exception:
                _LOGGER.exception("Exception calling remove_device.")
                return self.async_abort(reason="remove_failed")

        device_options = {
            device["address"]: f"{device.get('name', 'Unknown')} ({device['address']})"
            for device in self.discovered_devices
        }

        return self.async_show_form(
            step_id="select_device_to_remove",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(device_options)}),
            description_placeholders={"device_count": len(device_options)}
        )

