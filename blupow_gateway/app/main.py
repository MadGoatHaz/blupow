import asyncio
import logging
import os
import json
import re
import importlib
import inspect
import pkgutil
import datetime
from typing import Any, Dict, Optional, Type

import paho.mqtt.client as mqtt

# --- Local Imports ---
from app.devices.base import BaseDevice
from app import devices as devices_package # Import the package to inspect it

# --- Configuration & Constants ---
GATEWAY_VERSION = "1.0.0" # For status reporting
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "blupow")
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", 60))
INTER_DEVICE_DELAY_SECONDS = int(os.getenv("INTER_DEVICE_DELAY_SECONDS", 5))
CONFIG_FILE_PATH = os.getenv("CONFIG_FILE_PATH", "/app/config/devices.json")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# --- Driver Mapping (will be populated dynamically) ---
DRIVER_MAP: Dict[str, Type[BaseDevice]] = {}

def _camel_to_snake(name: str) -> str:
    """Converts a CamelCase string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def load_drivers():
    """Dynamically find and load all device drivers."""
    _LOGGER.info("Dynamically loading device drivers...")
    # Iterate over all modules in the 'devices' package
    for _, module_name, _ in pkgutil.iter_modules(devices_package.__path__, devices_package.__name__ + '.'):
        if module_name.endswith('.base'):
            continue # Skip the base class module

        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find all classes in the module that are subclasses of BaseDevice
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseDevice) and obj is not BaseDevice:
                    driver_key = _camel_to_snake(name)
                    if driver_key in DRIVER_MAP:
                        _LOGGER.warning(f"Duplicate driver key '{driver_key}' found. Overwriting.")
                    
                    DRIVER_MAP[driver_key] = obj
                    _LOGGER.info(f"Successfully loaded driver: '{driver_key}' -> {name}")
        except Exception as e:
            _LOGGER.error(f"Failed to load driver from module '{module_name}': {e}", exc_info=True)

# --- Runtime State ---
DEVICES_TO_POLL: Dict[str, Dict[str, Any]] = {}
PUBLISHED_DISCOVERY_DEVICES: set = set()

def load_devices_from_config():
    """Load the list of devices from the config file."""
    global DEVICES_TO_POLL
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                DEVICES_TO_POLL = json.load(f)
            _LOGGER.info(f"Loaded {len(DEVICES_TO_POLL)} devices from {CONFIG_FILE_PATH}")
            # One-time driver load on startup
            if not DRIVER_MAP:
                load_drivers()
    except (json.JSONDecodeError, IOError) as e:
        _LOGGER.error(f"Error loading device config: {e}. Starting with an empty list.")
        DEVICES_TO_POLL = {}

def save_devices_to_config():
    """Save the current list of devices to the config file."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(DEVICES_TO_POLL, f, indent=4)
        _LOGGER.info(f"Saved {len(DEVICES_TO_POLL)} devices to {CONFIG_FILE_PATH}")
    except IOError as e:
        _LOGGER.error(f"Error saving device config: {e}")

# --- MQTT Command Handling ---
def handle_mqtt_command(client, userdata, msg):
    """Callback for handling commands from Home Assistant."""
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command")
        address = payload.get("address")
        
        if not command or not address:
            _LOGGER.warning(f"Received invalid command: {payload}")
            return

        address = address.upper()

        if command == "add_device":
            device_type = payload.get("type")
            if not device_type:
                _LOGGER.warning(f"Add command missing device type: {payload}")
                return
            if device_type not in DRIVER_MAP:
                _LOGGER.warning(f"Unknown device type '{device_type}' in add command.")
                return

            _LOGGER.info(f"Received command to add device: {address} ({device_type})")
            DEVICES_TO_POLL[address] = {"type": device_type}
            if "config" in payload: # Pass config for generic devices
                DEVICES_TO_POLL[address]["config"] = payload["config"]
            save_devices_to_config()

            # Immediately publish discovery for the new device
            driver = get_driver_for_device(address)
            if driver:
                _LOGGER.info(f"Dynamically publishing discovery for new device {address}")
                publish_discovery_messages(driver, MQTT_TOPIC_PREFIX)
            else:
                _LOGGER.error(f"Failed to get driver for newly added device {address}")

        elif command == "remove_device":
            _LOGGER.info(f"Received command to remove device: {address}")
            if address in DEVICES_TO_POLL:
                del DEVICES_TO_POLL[address]
                save_devices_to_config()
                publish_to_mqtt(MQTT_TOPIC_PREFIX, address, None) # Publish offline
            else:
                _LOGGER.warning(f"Device {address} not found in polling list.")

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        _LOGGER.error(f"Failed to decode MQTT command payload: {e}")

# --- MQTT Client Setup ---
mqtt_client = mqtt.Client()

# Set Last Will and Testament (LWT)
lwt_topic = f"{MQTT_TOPIC_PREFIX}/gateway/status"
lwt_payload = json.dumps({"state": "offline", "version": GATEWAY_VERSION})
mqtt_client.will_set(lwt_topic, payload=lwt_payload, qos=1, retain=True)

def publish_gateway_status():
    """Publishes the gateway's own status to a dedicated MQTT topic."""
    status_topic = f"{MQTT_TOPIC_PREFIX}/gateway/status"
    status_payload = {
        "state": "online",
        "version": GATEWAY_VERSION,
        "poll_interval_seconds": POLLING_INTERVAL_SECONDS,
        "devices_managed": len(DEVICES_TO_POLL),
        "drivers_loaded": list(DRIVER_MAP.keys()),
        "last_update": datetime.datetime.utcnow().isoformat()
    }
    _LOGGER.info("Publishing gateway status.")
    mqtt_client.publish(status_topic, json.dumps(status_payload), qos=1, retain=True)

def on_connect(client, userdata, flags, rc):
    _LOGGER.info(f"MQTT Connected with result code {rc}")
    command_topic = f"{MQTT_TOPIC_PREFIX}/gateway/command"
    client.subscribe(command_topic)
    _LOGGER.info(f"Subscribed to command topic: {command_topic}")
    publish_gateway_status()

def on_disconnect(client, userdata, rc):
    _LOGGER.warning(f"MQTT Disconnected with result code {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = handle_mqtt_command
if MQTT_USER and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
mqtt_client.loop_start()

def publish_discovery_messages(driver: BaseDevice, topic_prefix: str):
    """Publish MQTT discovery messages for a given device driver."""
    address = driver.mac_address
    address_safe = address.replace(":", "").lower()
    device_info = driver.get_device_info()

    device_payload = {
        "identifiers": [address],
        "name": f"BluPow-{address_safe}",
        "manufacturer": "BluPow Gateway",
        "model": device_info.get("type", "Unknown Device"),
    }

    availability_topic = f"{topic_prefix}/{address_safe}/availability"
    state_topic = f"{topic_prefix}/{address_safe}/state"

    for sensor_def in driver.get_sensor_definitions():
        sensor_key = sensor_def["key"]
        sensor_name = sensor_def["name"]
        
        unique_id = f"blupow_{address_safe}_{sensor_key}"

        discovery_payload = {
            "unique_id": unique_id,
            "name": f"{address_safe} {sensor_name}",
            "device": device_payload,
            "availability_topic": availability_topic,
            "json_attributes_topic": state_topic,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{sensor_key} }}}}",
        }
        
        if "unit" in sensor_def:
            discovery_payload["unit_of_measurement"] = sensor_def["unit"]
        if "icon" in sensor_def:
            discovery_payload["icon"] = sensor_def["icon"]
        if "device_class" in sensor_def:
            discovery_payload["device_class"] = sensor_def["device_class"]
        if "state_class" in sensor_def:
            discovery_payload["state_class"] = sensor_def["state_class"]
            
        discovery_topic = f"homeassistant/sensor/{unique_id}/config"
        
        _LOGGER.info(f"[{address}] Publishing discovery for sensor: {sensor_name}")
        mqtt_client.publish(discovery_topic, json.dumps(discovery_payload), qos=1, retain=True)

    PUBLISHED_DISCOVERY_DEVICES.add(address)

def get_driver_for_device(address: str) -> Optional[BaseDevice]:
    """Instantiate a driver for a given device address."""
    device_config = DEVICES_TO_POLL.get(address)
    if not device_config:
        _LOGGER.warning(f"No configuration found for device {address}")
        return None

    device_type = device_config.get("type")
    if not device_type:
        _LOGGER.warning(f"No type specified for device {address}")
        return None

    driver_class = DRIVER_MAP.get(device_type)
    if not driver_class:
        _LOGGER.error(f"No driver found for device type '{device_type}'")
        return None

    # Special handling for the generic driver, which requires a 'config' argument
    if driver_class.__name__ == 'GenericModbusDevice':
        device_specific_config = device_config.get("config")
        if not device_specific_config:
            _LOGGER.error(f"Device type 'generic_modbus_device' requires a 'config' block for {address}")
            return None
        try:
            return driver_class(address=address, device_type=device_type, config=device_specific_config)
        except (ValueError, TypeError) as e:
            _LOGGER.error(f"Failed to instantiate generic driver for {address}: {e}")
            return None
    else:
        # Standard drivers that don't require extra config
        return driver_class(address=address, device_type=device_type)

def publish_to_mqtt(topic_prefix: str, address: str, data: Optional[Dict]):
    """Publish data and availability to MQTT."""
    address_safe = address.replace(":", "").lower()
    availability_topic = f"{topic_prefix}/{address_safe}/availability"
    state_topic = f"{topic_prefix}/{address_safe}/state"

    if data:
        _LOGGER.info(f"[{address}] Publishing data to {state_topic}")
        mqtt_client.publish(availability_topic, "online", qos=1, retain=True)
        mqtt_client.publish(state_topic, json.dumps(data), qos=1, retain=False)
    else:
        _LOGGER.info(f"[{address}] Publishing offline status to {availability_topic}")
        mqtt_client.publish(availability_topic, "offline", qos=1, retain=True)

async def main():
    """Main polling loop."""
    load_devices_from_config()
    _LOGGER.info("Starting main polling loop.")

    while True:
        addresses_to_poll = list(DEVICES_TO_POLL.keys())

        if not addresses_to_poll:
            _LOGGER.info("No devices configured to poll. Waiting...")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
            continue

        for address in addresses_to_poll:
            driver = get_driver_for_device(address)
            if not driver:
                continue

            if driver.mac_address not in PUBLISHED_DISCOVERY_DEVICES:
                publish_discovery_messages(driver, MQTT_TOPIC_PREFIX)

            _LOGGER.info(f"--- Polling device: {driver.mac_address} ({driver.device_type}) ---")
            data = await driver.get_data()
            publish_to_mqtt(MQTT_TOPIC_PREFIX, driver.mac_address, data)

            if len(addresses_to_poll) > 1:
                _LOGGER.info(f"Delaying {INTER_DEVICE_DELAY_SECONDS}s before next device...")
                await asyncio.sleep(INTER_DEVICE_DELAY_SECONDS)

        _LOGGER.info(f"Polling cycle complete. Waiting for {POLLING_INTERVAL_SECONDS} seconds.")
        publish_gateway_status()
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Polling stopped by user.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()