import asyncio
import concurrent.futures
import json
import logging
import os
import time
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

# Eagerly import device classes
from app.devices.renogy_controller import RenogyController
from app.devices.renogy_inverter import RenogyInverter
from app.devices.generic_modbus_device import GenericModbusDevice
from app.devices.base import BaseDevice

# --- Constants ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.path.dirname(APP_DIR), 'config')
DEVICE_CONFIG_FILE = os.path.join(CONFIG_DIR, 'devices.json') # Dummy file for now
GATEWAY_VERSION = "1.0.0" # Version for status reporting

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
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL_SECONDS", 30))
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
DISCOVERY_PREFIX = "homeassistant"


def create_device(config: Dict[str, Any]) -> BaseDevice:
    """Factory function to create device instances."""
    device_type = config.get("type")
    address = config.get("address")

    if not device_type or not address:
        raise ValueError(f"Device config is missing 'type' or 'address': {config}")
    
    _LOGGER.info(f"Creating device of type '{device_type}' for address '{address}'")

    if device_type == "renogy_controller":
        return RenogyController(address=address, device_type=device_type)
    elif device_type == "renogy_inverter":
        return RenogyInverter(address=address, device_type=device_type)
    elif device_type == "generic_modbus":
        return GenericModbusDevice(address=address, device_type=device_type, config=config)
    else:
        raise ValueError(f"Unknown device type: {device_type}")

def load_devices_from_config(config_path: str) -> Dict[str, BaseDevice]:
    """Loads device configurations from a JSON file."""
    _LOGGER.info(f"Loading device configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            devices_config = json.load(f)
        
        devices = {}
        for config in devices_config.get("devices", []):
            try:
                device = create_device(config)
                # Use MAC address as a unique ID
                devices[device.mac_address.upper()] = device
            except ValueError as e:
                _LOGGER.error(f"Failed to create device with config {config}: {e}")
        _LOGGER.info(f"Successfully loaded {len(devices)} devices.")
        return devices
    except FileNotFoundError:
        _LOGGER.warning(f"Device config file not found at {config_path}. No devices loaded.")
        return {}
    except json.JSONDecodeError:
        _LOGGER.error(f"Error decoding JSON from {config_path}.")
        return {}


def publish_mqtt_discovery(device: BaseDevice):
    """Publishes MQTT discovery messages for all sensors of a device."""
    if not MQTT_CLIENT:
        _LOGGER.error("MQTT client not available, skipping discovery.")
        return

    device_info = device.get_device_info()
    mac_address_safe = device.mac_address.replace(":", "")

    for sensor in device.get_sensor_definitions():
        sensor_id = sensor["id"]
        unique_id = f"blupow_{mac_address_safe}_{sensor_id}"
        
        topic_path = f"{DISCOVERY_PREFIX}/sensor/{unique_id}/config"
        state_topic = f"blupow/{device.mac_address}/state"
        
        payload = {
            "name": f"BluPow {mac_address_safe[:4]} {sensor['name']}",
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{sensor_id} }}}}",
            "device": {
                "identifiers": [f"blupow_{mac_address_safe}"],
                "name": f"BluPow Gateway Device ({device.mac_address})",
                "model": device.device_type,
                "manufacturer": "BluPow"
            },
            **sensor.get("metadata", {}) # Include unit, class, etc.
        }
        
        _LOGGER.info(f"Publishing discovery for sensor '{sensor_id}' on topic {topic_path}")
        MQTT_CLIENT.publish(topic_path, json.dumps(payload), retain=True)

def on_connect(client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        _LOGGER.info("Successfully connected to MQTT broker.")
        command_topic = "blupow/gateway/command"
        _LOGGER.info(f"Subscribing to command topic: {command_topic}")
        client.subscribe(command_topic)
    else:
        _LOGGER.error(f"Failed to connect to MQTT broker, return code {rc}\n")

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
    """Callback for when a message is received from the MQTT broker."""
    _LOGGER.info(f"Received command on topic {msg.topic}: {msg.payload.decode()}")
    # Command handling logic will be implemented in a future phase
    # For now, we just log the command.

def setup_mqtt_client() -> mqtt.Client:
    """Creates and newfigures the MQTT client."""
    client = mqtt.Client(client_id="blupow_gateway", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    _LOGGER.info(f"Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_PORT}")
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_PORT, 60)
    except ConnectionRefusedError:
        _LOGGER.error("Connection to MQTT broker refused. Check broker address and port.")
        raise
    except OSError as e:
        _LOGGER.error(f"OS error while connecting to MQTT broker: {e}. Is the broker running?")
        raise
    return client

async def poll_device(device: BaseDevice):
    """Polls a single device and publishes its state."""
    global MQTT_CLIENT
    _LOGGER.info(f"Polling device: {device.mac_address}")
    try:
        data = await device.poll()
        if data:
            if MQTT_CLIENT:
                state_topic = f"blupow/{device.mac_address}/state"
                _LOGGER.info(f"Publishing data for {device.mac_address} to {state_topic}")
                MQTT_CLIENT.publish(state_topic, json.dumps(data))
            else:
                _LOGGER.warning("MQTT client not ready, cannot publish data.")
        else:
            _LOGGER.warning(f"No data received from poll for device {device.mac_address}")
    except Exception:
        _LOGGER.exception(f"Unhandled exception while polling device {device.mac_address}")


async def run_gateway():
    """The main entry point and loop for the gateway."""
    global DEVICES, MQTT_CLIENT
    
    _LOGGER.info("--- BluPow Gateway Starting Up ---")
    
    # Load initial devices
    DEVICES = load_devices_from_config(os.getenv("CONFIG_FILE_PATH", "/config/devices.json"))

    # Setup and start MQTT client
    try:
        MQTT_CLIENT = setup_mqtt_client()
        MQTT_CLIENT.loop_start()
    except (ConnectionRefusedError, OSError):
        _LOGGER.error("Could not connect to MQTT. Gateway cannot start.")
        return

    # Allow time for MQTT to connect before publishing
    await asyncio.sleep(2) 

    # Publish gateway online status
    status_payload = {
        "state": "online",
        "version": GATEWAY_VERSION
    }
    status_topic = "blupow/gateway/status"
    _LOGGER.info(f"Publishing gateway status to {status_topic}")
    MQTT_CLIENT.publish(status_topic, json.dumps(status_payload), retain=True)

    # Publish discovery for all initial devices
    for device in DEVICES.values():
        publish_mqtt_discovery(device)

    # Main polling loop
    _LOGGER.info(f"Starting main polling loop with interval: {POLLING_INTERVAL} seconds")
    loop = asyncio.get_running_loop()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            _LOGGER.info("--- Kicking off new polling cycle ---")
            tasks = [loop.run_in_executor(executor, lambda d=d: asyncio.run(poll_device(d))) for d in DEVICES.values()]
            
            # Wait for the next cycle
            await asyncio.sleep(POLLING_INTERVAL)

def main():
    """Main function to run the gateway."""
    try:
        asyncio.run(run_gateway())
    except KeyboardInterrupt:
        _LOGGER.info("--- BluPow Gateway Shutting Down ---")
    finally:
        if MQTT_CLIENT:
            MQTT_CLIENT.loop_stop()

if __name__ == "__main__":
    main()