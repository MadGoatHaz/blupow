import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import paho.mqtt.client as mqtt

from .device_manager import DeviceManager
from app.devices.base import BaseDevice

_LOGGER = logging.getLogger(__name__)

# --- Constants ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "blupow-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
DISCOVERY_PREFIX = "homeassistant"


class MqttHandler:
    """Handles all MQTT communication for the gateway."""

    def __init__(self, loop: asyncio.AbstractEventLoop, device_manager: DeviceManager):
        self._loop = loop
        self._device_manager = device_manager
        self._client: Optional[mqtt.Client] = None
        
        # Give the device manager a way to publish messages
        self._device_manager.set_mqtt_publisher(self)

    def connect(self):
        """Sets up the MQTT client and connects to the broker."""
        self._client = mqtt.Client()
        if MQTT_USER and MQTT_PASS:
            self._client.username_pw_set(MQTT_USER, MQTT_PASS)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message_sync
        
        try:
            self._client.connect(MQTT_BROKER_HOST, MQTT_PORT, 60)
            self._client.loop_start()
            _LOGGER.info("MQTT client loop started.")
        except Exception:
            _LOGGER.exception("Failed to connect MQTT client.")
            raise # Re-raise to be handled by the main application loop

    def disconnect(self):
        """Disconnects the MQTT client."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            _LOGGER.info("MQTT client disconnected.")
            
    def publish(self, topic: str, payload: str, retain: bool = False):
        """Publishes a message to a given MQTT topic."""
        if self._client:
            self._client.publish(topic, payload, retain=retain)

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            _LOGGER.info("Successfully connected to MQTT broker.")
            client.subscribe("blupow/gateway/command")
            _LOGGER.info("Subscribed to command topic: blupow/gateway/command")
            # Set all devices to online when MQTT reconnects and republish discovery
            for device in self._device_manager.devices.values():
                self.publish_mqtt_discovery(device)
                availability_topic = f"blupow/{device.mac_address}/status"
                self.publish(availability_topic, "online", retain=True)
        else:
            _LOGGER.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_message_sync(self, client, userdata, msg):
        """Sync wrapper to schedule the async message handler in the event loop."""
        asyncio.run_coroutine_threadsafe(self._on_message(client, userdata, msg), self._loop)

    async def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        """Async handler for incoming MQTT messages."""
        try:
            payload_str = msg.payload.decode()
            if not payload_str:
                _LOGGER.warning("Received empty MQTT message. Ignoring.")
                return
            
            data = json.loads(payload_str)
            command = data.get("command")
            request_id = data.get("request_id")
            
            # Lock to ensure sequential BLE operations
            async with self._device_manager.ble_lock:
                await self._handle_command(command, data, request_id)

        except json.JSONDecodeError:
            _LOGGER.warning(f"Could not decode MQTT message: {msg.payload.decode()}")
        except Exception:
            _LOGGER.exception("Unhandled error processing MQTT message")

    async def _handle_command(self, command: str, data: Dict, request_id: Optional[str]):
        """Delegates command processing to specific methods."""
        response_payload = {}
        try:
            if command == "get_devices":
                devices = [dev.get_device_info() for dev in self._device_manager.devices.values()]
                response_payload = {"status": "success", "devices": devices}
            
            elif command == "discover_devices":
                devices = await self._device_manager.discover_devices()
                response_payload = {"status": "success", "devices": devices}

            elif command == "add_device":
                device_info = await self._device_manager.add_device(data["address"], data["type"])
                response_payload = {"status": "success", "device": device_info}

            elif command == "remove_device":
                await self._device_manager.remove_device(data["address"])
                response_payload = {"status": "success"}

            elif command == "restart_gateway":
                 # This command will be handled by main.py via a shutdown signal
                 # For now, just acknowledge. A more robust solution might use a callback.
                response_payload = {"status": "success", "message": "restarting"}
                # Trigger shutdown in the main loop
                self._loop.call_soon_threadsafe(self._loop.stop)
            
            else:
                response_payload = {"status": "failure", "reason": "unknown_command"}

        except (KeyError, TypeError, ValueError, ConnectionError) as e:
            _LOGGER.error(f"Error handling command '{command}': {e}")
            response_payload = {"status": "failure", "reason": str(e)}
        
        if request_id:
            response_topic = f"blupow/gateway/response/{request_id}"
            self.publish(response_topic, json.dumps(response_payload))

    def publish_mqtt_discovery(self, device: BaseDevice):
        """Publishes MQTT discovery messages for all sensors of a device."""
        mac_safe = device.mac_address.replace(":", "")
        availability_topic = f"blupow/{device.mac_address}/status"
        for sensor in device.get_sensor_definitions():
            sensor_id = sensor["key"]
            unique_id = f"blupow_{mac_safe}_{sensor_id}"
            topic_path = f"{DISCOVERY_PREFIX}/sensor/{unique_id}/config"
            state_topic = f"blupow/{device.mac_address}/state"
            
            payload = {
                "name": f"BluPow {mac_safe[:4]} {sensor['name']}",
                "unique_id": unique_id,
                "state_topic": state_topic,
                "availability_topic": availability_topic,
                "payload_available": "online",
                "payload_not_available": "offline",
                "value_template": f"{{{{ value_json.get('{sensor_id}') }}}}",
                "device": {
                    "identifiers": [f"blupow_{device.mac_address}"],
                    "name": device.get_device_name(),
                    "model": device.device_type,
                    "manufacturer": "BluPow"
                },
            }
            if "unit" in sensor: payload["unit_of_measurement"] = sensor["unit"]
            if "icon" in sensor: payload["icon"] = sensor["icon"]
            if "device_class" in sensor: payload["device_class"] = sensor["device_class"]
            if "state_class" in sensor: payload["state_class"] = sensor["state_class"]

            self.publish(topic_path, json.dumps(payload), retain=True)
            
    def clear_device_topics(self, device: BaseDevice):
        """Clears (un-publishes) the discovery topics for a device."""
        _LOGGER.info(f"Clearing MQTT discovery topics for {device.mac_address}")
        mac_safe = device.mac_address.replace(":", "")
        for sensor in device.get_sensor_definitions():
            sensor_id = sensor["key"]
            unique_id = f"blupow_{mac_safe}_{sensor_id}"
            topic_path = f"{DISCOVERY_PREFIX}/sensor/{unique_id}/config"
            self.publish(topic_path, "", retain=True) 