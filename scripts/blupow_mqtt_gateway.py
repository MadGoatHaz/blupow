import asyncio
import logging
import os
import json
import struct
import time
from typing import Any, Dict, Optional, List, Set

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import paho.mqtt.client as mqtt

# --- Configuration ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "blupow")
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", 60))
INTER_DEVICE_DELAY_SECONDS = int(os.getenv("INTER_DEVICE_DELAY_SECONDS", 5))
CONNECTION_TIMEOUT = 20.0
READ_TIMEOUT = 15.0
CONFIG_FILE_PATH = "/app/config/devices.json"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# --- Device Storage ---
DEVICES_TO_POLL: Dict[str, Dict[str, Any]] = {}

def load_devices_from_config():
    """Load the list of devices from the config file."""
    global DEVICES_TO_POLL
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                DEVICES_TO_POLL = json.load(f)
            _LOGGER.info(f"Loaded {len(DEVICES_TO_POLL)} devices from {CONFIG_FILE_PATH}")
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
        device_type = payload.get("type")

        if not command or not address:
            _LOGGER.warning(f"Received invalid command: {payload}")
            return

        address = address.upper()

        if command == "add_device":
            if not device_type:
                _LOGGER.warning(f"Add command missing device type: {payload}")
                return
            _LOGGER.info(f"Received command to add device: {address} ({device_type})")
            DEVICES_TO_POLL[address] = {"type": device_type}
            save_devices_to_config()

        elif command == "remove_device":
            _LOGGER.info(f"Received command to remove device: {address}")
            if address in DEVICES_TO_POLL:
                del DEVICES_TO_POLL[address]
                save_devices_to_config()
                # Publish an offline message for the removed device
                publish_to_mqtt(MQTT_TOPIC_PREFIX, address, None)
            else:
                _LOGGER.warning(f"Device {address} not found in polling list.")

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        _LOGGER.error(f"Failed to decode MQTT command payload: {e}")

# --- MQTT Client Setup ---
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    _LOGGER.info(f"MQTT Connected with result code {rc}")
    # Subscribe to the command topic
    command_topic = f"{MQTT_TOPIC_PREFIX}/gateway/command"
    client.subscribe(command_topic)
    _LOGGER.info(f"Subscribed to command topic: {command_topic}")

def on_disconnect(client, userdata, rc):
    _LOGGER.warning(f"MQTT Disconnected with result code {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = handle_mqtt_command
if MQTT_USER and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
mqtt_client.loop_start()

# --- CRC Calculation & Parsers (Unchanged) ---
def _calculate_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def _bytes_to_int(bs: bytes, offset: int, size: int, signed: bool = False, scale: float = 1.0) -> float:
    value = int.from_bytes(bs[offset:offset+size], byteorder='big', signed=signed)
    return value * scale

def _parse_temperature(value, unit="c"):
    temp = (value & 0x7f) * (1 if (value >> 7 == 0) else -1)
    return round(((temp * 9/5) + 32), 2) if unit == "f" else temp

class BluPowPoller:
    """A stateless client to poll a single Renogy device."""

    def __init__(self, address: str, device_type: str):
        self.mac_address = address.upper()
        self.device_type = device_type
        self.device_id = 32 if self.device_type == "inverter" else 1
        
        notify_uuids = {
            "inverter": "0000ffd2-0000-1000-8000-00805f9b34fb",
            "controller": "0000fff1-0000-1000-8000-00805f9b34fb",
        }
        self.notify_uuid = notify_uuids.get(self.device_type, "0000fff1-0000-1000-8000-00805f9b34fb")
        self.write_uuid = "0000ffd1-0000-1000-8000-00805f9b34fb"
        
        self.sections = self._get_sections_for_model(self.device_type)
        self._data_buffer: Dict[str, Any] = {}
        self._notification_event = asyncio.Event()

    def _get_sections_for_model(self, device_type: str):
        if device_type == "inverter":
            # Inverter parsing logic can be added here
            return []
        else: # Controller
            return [
                {'register': 12, 'words': 8, 'parser': self._parse_controller_device_info},
                {'register': 256, 'words': 34, 'parser': self._parse_controller_charging_info},
                {'register': 57348, 'words': 1, 'parser': self._parse_controller_battery_type},
            ]

    async def get_data(self) -> Optional[Dict[str, Any]]:
        _LOGGER.debug(f"[{self.mac_address}] Starting data fetch process.")
        client = None
        try:
            _LOGGER.info(f"Scanning for {self.mac_address}...")
            device = await BleakScanner.find_device_by_address(self.mac_address, timeout=10.0)
            if not device:
                _LOGGER.warning(f"[{self.mac_address}] Device not found during scan.")
                return None

            client = BleakClient(device, timeout=CONNECTION_TIMEOUT)
            _LOGGER.info(f"[{self.mac_address}] Attempting to connect...")
            await client.connect()
            _LOGGER.info(f"[{self.mac_address}] Connected successfully.")

            await client.start_notify(self.notify_uuid, self._notification_handler)
            
            self._data_buffer.clear()
            for section in self.sections:
                command = self._build_modbus_command(section['register'], section['words'])
                self._notification_event.clear()
                await client.write_gatt_char(self.write_uuid, command, response=False)
                await asyncio.wait_for(self._notification_event.wait(), timeout=READ_TIMEOUT)
            
            return self._data_buffer

        except BleakError as e:
            _LOGGER.error(f"[{self.mac_address}] BleakError during operation: {e}")
            return None
        except asyncio.TimeoutError:
            _LOGGER.warning(f"[{self.mac_address}] Timeout waiting for notification or connection.")
            return None
        except Exception as e:
            _LOGGER.error(f"[{self.mac_address}] An unexpected error occurred: {e}", exc_info=True)
            return None
        finally:
            if client and client.is_connected:
                await client.disconnect()
                _LOGGER.info(f"[{self.mac_address}] Disconnected.")

    def _notification_handler(self, sender, data: bytearray):
        _LOGGER.debug(f"[{self.mac_address}] Received notification: {data.hex()}")
        parser_found = False
        for section in self.sections:
            # Response is payload + 5 bytes (addr, func, len, crc, crc)
            if len(data) == section['words'] * 2 + 5:
                parsed_data = section['parser'](data)
                self._data_buffer.update(parsed_data)
                parser_found = True
                break
        
        if not parser_found:
            _LOGGER.warning(f"[{self.mac_address}] Received unexpected data length: {len(data)}")
        
        self._notification_event.set()

    def _build_modbus_command(self, start_register: int, count: int) -> bytes:
        command = bytearray([
            self.device_id, 0x03,
            (start_register >> 8) & 0xFF, start_register & 0xFF,
            (count >> 8) & 0xFF, count & 0xFF
        ])
        crc = _calculate_crc(bytes(command))
        command.extend(crc)
        return bytes(command)

    # --- Parsers ---
    def _parse_controller_device_info(self, bs: bytes) -> Dict[str, Any]:
        return {'model': (bs[3:19]).decode('utf-8', 'ignore').strip().rstrip('\x00')}
    
    def _parse_controller_charging_info(self, bs: bytes) -> Dict[str, Any]:
        charging_state_map = {0: 'deactivated', 1: 'activated', 2: 'mppt', 3: 'equalizing', 4: 'boost', 5: 'floating', 6: 'current limiting'}
        load_state_map = {0: 'off', 1: 'on'}
        return {
            'battery_soc': _bytes_to_int(bs, 3, 2),
            'battery_voltage': _bytes_to_int(bs, 5, 2, scale=0.1),
            'battery_current': _bytes_to_int(bs, 7, 2, scale=0.01),
            'battery_temperature': _parse_temperature(int(_bytes_to_int(bs, 10, 1))),
            'controller_temperature': _parse_temperature(int(_bytes_to_int(bs, 9, 1))),
            'load_status': load_state_map.get(int(_bytes_to_int(bs, 67, 1)) >> 7, 'unknown'),
            'load_voltage': _bytes_to_int(bs, 11, 2, scale=0.1),
            'load_current': _bytes_to_int(bs, 13, 2, scale=0.01),
            'load_power': _bytes_to_int(bs, 15, 2),
            'solar_voltage': _bytes_to_int(bs, 17, 2, scale=0.1),
            'solar_current': _bytes_to_int(bs, 19, 2, scale=0.01),
            'solar_power': _bytes_to_int(bs, 21, 2),
            'charging_amp_hours_today': _bytes_to_int(bs, 37, 2),
            'discharging_amp_hours_today': _bytes_to_int(bs, 39, 2),
            'power_generation_today': _bytes_to_int(bs, 41, 2, scale=0.001), # Assuming Wh, converting to kWh
            'power_consumption_today': _bytes_to_int(bs, 43, 2, scale=0.001), # Assuming Wh, converting to kWh
            'power_generation_total': _bytes_to_int(bs, 59, 4, scale=0.001), # Assuming Wh, converting to kWh
            'charging_status': charging_state_map.get(int(_bytes_to_int(bs, 68, 1)), 'unknown'),
        }

    def _parse_controller_battery_type(self, bs: bytes) -> Dict[str, Any]:
        battery_type_map = {1: 'open', 2: 'sealed', 3: 'gel', 4: 'lithium', 5: 'custom'}
        return {'battery_type': battery_type_map.get(int(_bytes_to_int(bs, 3, 2)), 'unknown')}

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
        # Create a copy of keys to avoid issues if DEVICES_TO_POLL is modified during iteration
        addresses_to_poll = list(DEVICES_TO_POLL.keys())
        
        if not addresses_to_poll:
            _LOGGER.info("No devices configured to poll. Waiting...")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
            continue

        for address in addresses_to_poll:
            device_info = DEVICES_TO_POLL.get(address)
            if not device_info:
                continue

            poller = BluPowPoller(address, device_info["type"])
            _LOGGER.info(f"--- Polling device: {poller.mac_address} ({poller.device_type}) ---")
            data = await poller.get_data()
            publish_to_mqtt(MQTT_TOPIC_PREFIX, poller.mac_address, data)
            
            if len(addresses_to_poll) > 1:
                _LOGGER.info(f"Delaying {INTER_DEVICE_DELAY_SECONDS}s before next device...")
                await asyncio.sleep(INTER_DEVICE_DELAY_SECONDS)
        
        _LOGGER.info(f"Polling cycle complete. Waiting for {POLLING_INTERVAL_SECONDS} seconds.")
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Polling stopped by user.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect() 