import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional, Set

import paho.mqtt.client as mqtt

# Eagerly import device classes
from app.devices.renogy_controller import RenogyController
from app.devices.renogy_inverter import RenogyInverter
from app.devices.generic_modbus_device import GenericModbusDevice
from app.devices.base import BaseDevice

# --- Constants ---
GATEWAY_VERSION = "1.0.0"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)

# --- Global State ---
MQTT_CLIENT: Optional[mqtt.Client] = None
DEVICES: Dict[str, BaseDevice] = {}
POLLING_TASKS: Dict[str, asyncio.Task] = {}
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL_SECONDS", 30))
# --- TEMPORARY FIX ---
# Hardcoding the broker host to troubleshoot environment variable issues.
MQTT_BROKER_HOST = "blupow-mosquitto"
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
DISCOVERY_PREFIX = "homeassistant"

# --- Device Management ---

def create_device(config: Dict[str, Any]) -> BaseDevice:
    """Factory function to create device instances."""
    device_type = config.get("type")
    address = config.get("address")
    if not device_type or not address:
        raise ValueError("Device config missing 'type' or 'address'")
    
    _LOGGER.info(f"Creating device of type '{device_type}' for address '{address}'")
    
    if device_type == "renogy_controller":
        return RenogyController(address, device_type)
    if device_type == "renogy_inverter":
        return RenogyInverter(address, device_type)
    if device_type == "generic_modbus":
        return GenericModbusDevice(address, device_type, config)
    
    raise ValueError(f"Unknown device type: {device_type}")

async def start_polling_device(device: BaseDevice):
    """Creates a dedicated, cancellable polling loop for a device."""
    address = device.mac_address.upper()
    _LOGGER.info(f"Starting polling task for {address}")

    async def polling_loop():
        while True:
            _LOGGER.info(f"Polling device: {address}")
            try:
                data = await device.poll()
                if data and MQTT_CLIENT:
                    state_topic = f"blupow/{device.mac_address}/state"
                    MQTT_CLIENT.publish(state_topic, json.dumps(data))
                elif not data:
                    _LOGGER.warning(f"No data received from poll for device {address}")
            except Exception:
                _LOGGER.exception(f"Unhandled exception while polling {address}")
            
            await asyncio.sleep(POLLING_INTERVAL)

    task = asyncio.create_task(polling_loop())
    POLLING_TASKS[address] = task
    _LOGGER.info(f"Polling task for {address} successfully created.")

def stop_polling_device(address: str):
    """Stops the polling task for a specific device."""
    address = address.upper()
    if address in POLLING_TASKS:
        _LOGGER.info(f"Cancelling polling task for {address}")
        POLLING_TASKS[address].cancel()
        del POLLING_TASKS[address]
        _LOGGER.info(f"Polling task for {address} cancelled.")
    else:
        _LOGGER.warning(f"No polling task found to stop for {address}")

# --- MQTT Handling ---

def publish_mqtt_discovery(device: BaseDevice):
    """Publishes MQTT discovery messages for all sensors of a device."""
    if not MQTT_CLIENT: return
    mac_safe = device.mac_address.replace(":", "")
    for sensor in device.get_sensor_definitions():
        sensor_id = sensor["id"]
        unique_id = f"blupow_{mac_safe}_{sensor_id}"
        topic_path = f"{DISCOVERY_PREFIX}/sensor/{unique_id}/config"
        state_topic = f"blupow/{device.mac_address}/state"
        
        payload = {
            "name": f"BluPow {mac_safe[:4]} {sensor['name']}",
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{sensor_id} }}}}",
            "device": {
                "identifiers": [f"blupow_{mac_safe}"],
                "name": f"BluPow Device ({device.mac_address})",
                "model": device.device_type,
                "manufacturer": "BluPow"
            },
            **sensor.get("metadata", {})
        }
        MQTT_CLIENT.publish(topic_path, json.dumps(payload), retain=True)

async def on_mqtt_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
    """Callback for MQTT messages."""
    try:
        payload_str = msg.payload.decode()
        if not payload_str:
            _LOGGER.warning("Received empty MQTT message. Ignoring.")
            return
            
        data = json.loads(payload_str)
        command = data.get("command")
        address = data.get("address", "").upper()
        request_id = data.get("request_id")

        if command == "add_device":
            _LOGGER.info(f"Processing add_device command for {address} (Request ID: {request_id})")
            if address in DEVICES:
                _LOGGER.warning(f"Device {address} already exists. Ignoring.")
                if request_id:
                    client.publish(f"blupow/gateway/response/{request_id}", json.dumps({"status": "failure", "reason": "already_exists"}))
                return
            
            device = create_device(data)
            # Attempt to connect to verify the device is reachable
            if await device.test_connection():
                DEVICES[address] = device
                publish_mqtt_discovery(device)
                await start_polling_device(device)
                if request_id:
                    client.publish(f"blupow/gateway/response/{request_id}", json.dumps({"status": "success"}))
            else:
                _LOGGER.error(f"Failed to connect to device {address}. Not adding.")
                if request_id:
                    client.publish(f"blupow/gateway/response/{request_id}", json.dumps({"status": "failure", "reason": "cannot_connect"}))

        elif command == "remove_device":
            _LOGGER.info(f"Processing remove_device command for {address}")
            if address in DEVICES:
                stop_polling_device(address)
                del DEVICES[address]
                if request_id:
                    client.publish(f"blupow/gateway/response/{request_id}", json.dumps({"status": "success"}))
            else:
                _LOGGER.warning(f"Attempted to remove non-existent device: {address}")
                if request_id:
                    client.publish(f"blupow/gateway/response/{request_id}", json.dumps({"status": "failure", "reason": "not_found"}))

        elif command == "get_devices":
            _LOGGER.info(f"Processing get_devices command (Request ID: {request_id})")
            device_list = [
                {"address": dev.mac_address, "type": dev.device_type, "name": dev.get_device_name()}
                for dev in DEVICES.values()
            ]
            if request_id and MQTT_CLIENT:
                response_topic = f"blupow/gateway/response/{request_id}"
                MQTT_CLIENT.publish(response_topic, json.dumps({"status": "success", "devices": device_list}))

        elif command == "discover_devices":
            _LOGGER.info(f"Processing discover_devices command (Request ID: {request_id})")
            try:
                from bleak import BleakScanner
                _LOGGER.info("Starting BLE device scan...")
                discovered_devices = await BleakScanner.discover(timeout=10.0)
                _LOGGER.info(f"Scan complete. Found {len(discovered_devices)} devices.")
                
                # Filter for devices that might be Renogy/BluPow
                potential_devices = [
                    {"name": dev.name, "address": dev.address}
                    for dev in discovered_devices
                    if dev.name and ("renogy" in dev.name.lower() or "bt-" in dev.name.lower())
                ]
                
                if request_id and MQTT_CLIENT:
                    response_topic = f"blupow/gateway/response/{request_id}"
                    MQTT_CLIENT.publish(response_topic, json.dumps({"status": "success", "devices": potential_devices}))

            except Exception as e:
                _LOGGER.exception("An error occurred during device discovery.")
                if request_id and MQTT_CLIENT:
                    response_topic = f"blupow/gateway/response/{request_id}"
                    MQTT_CLIENT.publish(response_topic, json.dumps({"status": "failure", "reason": str(e)}))

    except json.JSONDecodeError:
        _LOGGER.warning(f"Received invalid JSON on MQTT topic {msg.topic}. Payload: {msg.payload.decode()}")
    except Exception as e:
        _LOGGER.exception(f"Error processing MQTT command: {e}")

def setup_mqtt_client(loop: asyncio.AbstractEventLoop) -> mqtt.Client:
    """Configures and connects the MQTT client."""
    client = mqtt.Client(client_id="blupow_gateway", protocol=mqtt.MQTTv311)
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    def on_mqtt_message_sync(client, userdata, msg):
        """A sync wrapper to schedule the async message handler."""
        asyncio.run_coroutine_threadsafe(on_mqtt_message(client, userdata, msg), loop)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info("Successfully connected to MQTT broker.")
            client.subscribe("blupow/gateway/command")
            # Also subscribe to the status topic to republish devices on HA restart
            client.subscribe("homeassistant/status")
        else:
            _LOGGER.error(f"Failed to connect to MQTT broker, code {rc}")

    client.on_connect = on_connect
    # Use the sync wrapper for the Paho MQTT client
    client.on_message = on_mqtt_message_sync

    client.connect(MQTT_BROKER_HOST, MQTT_PORT, 60)
    return client

# --- Main Application ---

async def main():
    """Main application entry point."""
    _LOGGER.info("--- BluPow Gateway Starting Up ---")
    global MQTT_CLIENT
    
    main_loop = asyncio.get_running_loop()

    try:
        MQTT_CLIENT = setup_mqtt_client(main_loop)
        MQTT_CLIENT.loop_start()
    except Exception as e:
        _LOGGER.exception("Failed to connect to MQTT. Gateway cannot start.")
        return

    # Publish gateway online status
    status_payload = {"state": "online", "version": GATEWAY_VERSION}
    MQTT_CLIENT.publish("blupow/gateway/status", json.dumps(status_payload), retain=True)
    _LOGGER.info("Gateway is online and waiting for commands.")
    
    # Keep the gateway running indefinitely
    try:
        while True:
            await asyncio.sleep(3600) # Sleep for an hour
    except asyncio.CancelledError:
        _LOGGER.info("Main task cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("--- BluPow Gateway Shutting Down ---")
    finally:
        if MQTT_CLIENT:
            MQTT_CLIENT.loop_stop()
        _LOGGER.info("Shutdown complete.")