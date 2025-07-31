import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from app.devices.base import BaseDevice
from app.devices.renogy_controller import RenogyController
from app.devices.renogy_inverter import RenogyInverter
from app.devices.generic_modbus_device import GenericModbusDevice

_LOGGER = logging.getLogger(__name__)

# --- Constants ---
CONFIG_FILE_PATH = os.getenv("CONFIG_FILE_PATH", "/app/config/devices.json")


class DeviceManager:
    """Manages the state and lifecycle of all connected devices."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.devices: Dict[str, BaseDevice] = {}
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.discovered_device_cache: Dict[str, BLEDevice] = {}
        self.ble_lock = asyncio.Lock()
        self.polling_interval = int(os.getenv("POLLING_INTERVAL_SECONDS", 30))
        self._loop = loop
        self._mqtt_publisher = None # To be set by MqttHandler

    @staticmethod
    def create_device(
        address: str, device_type: str, config: dict, ble_device: Optional[BLEDevice] = None
    ) -> BaseDevice:
        """Factory function to create device instances."""
        if not device_type:
            raise ValueError("Device config missing 'type'")
        
        if device_type == "renogy_controller":
            return RenogyController(address, device_type, config, ble_device)
        if device_type == "renogy_inverter":
            return RenogyInverter(address, device_type, ble_device)
        if device_type == "generic_modbus_device":
            return GenericModbusDevice(address, device_type, config, ble_device)
    
        raise ValueError(f"Unknown device type: {device_type}")

    def set_mqtt_publisher(self, publisher):
        """Allows the MqttHandler to set a callback for publishing messages."""
        self._mqtt_publisher = publisher

    def load_devices_from_config(self):
        """Loads device configurations from the JSON config file."""
        if not os.path.exists(CONFIG_FILE_PATH):
            _LOGGER.info("Config file not found. Starting with no devices.")
            return
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                configs = json.load(f)
            
            for address, config in configs.items():
                try:
                    device = self.create_device(address, config.get("type"), config, None)
                    self.devices[address.upper()] = device
                    _LOGGER.info(f"Successfully loaded device from config: {address}")
                except (ValueError, TypeError) as e:
                    _LOGGER.error(f"Failed to create device for address {address} from config: {e}")
        except (json.JSONDecodeError, IOError) as e:
            _LOGGER.exception(f"Failed to read or parse config file at {CONFIG_FILE_PATH}")

    def save_devices_to_config(self):
        """Saves the current device configurations to the JSON config file."""
        configs = {
            address: dev.get_config()
            for address, dev in self.devices.items()
        }
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
            with open(CONFIG_FILE_PATH, 'w') as f:
                json.dump(configs, f, indent=2)
            _LOGGER.info(f"Successfully saved {len(configs)} device(s) to {CONFIG_FILE_PATH}")
        except IOError:
            _LOGGER.exception(f"Failed to write to config file at {CONFIG_FILE_PATH}")

    async def start_polling_device(self, device: BaseDevice, publish_discovery: bool = False):
        """Creates a dedicated, cancellable polling loop for a device."""
        address = device.mac_address.upper()
        
        if publish_discovery and self._mqtt_publisher:
            self._mqtt_publisher.publish_mqtt_discovery(device)

        _LOGGER.info(f"Starting polling task for {address}")

        async def polling_loop():
            availability_topic = f"blupow/{address}/status"
            while True:
                _LOGGER.info(f"Polling device: {address}")
                try:
                    data = await device.poll()
                    if data and self._mqtt_publisher:
                        self._mqtt_publisher.publish(availability_topic, "online", retain=True)
                        state_topic = f"blupow/{device.mac_address}/state"
                        self._mqtt_publisher.publish(state_topic, json.dumps(data))
                    else:
                        _LOGGER.warning(f"No data received from poll for device {address}. Setting to offline.")
                        if self._mqtt_publisher:
                            self._mqtt_publisher.publish(availability_topic, "offline", retain=True)
                except Exception:
                    _LOGGER.exception(f"Unhandled exception while polling {address}. Setting to offline.")
                    if self._mqtt_publisher:
                        self._mqtt_publisher.publish(availability_topic, "offline", retain=True)
                
                await asyncio.sleep(self.polling_interval)

        task = self._loop.create_task(polling_loop())
        self.polling_tasks[address] = task
        _LOGGER.info(f"Polling task for {address} successfully created.")

    def stop_polling_device(self, address: str):
        """Stops the polling task for a specific device."""
        address = address.upper()
        if address in self.polling_tasks:
            _LOGGER.info(f"Cancelling polling task for {address}")
            self.polling_tasks[address].cancel()
            del self.polling_tasks[address]
            if self._mqtt_publisher:
                availability_topic = f"blupow/{address}/status"
                self._mqtt_publisher.publish(availability_topic, "offline", retain=True)
            _LOGGER.info(f"Polling task for {address} cancelled and set to offline.")
        else:
            _LOGGER.warning(f"No polling task found to stop for {address}")

    async def add_device(self, address: str, device_type: str) -> Dict[str, Any]:
        """Adds a new device, tests connection, and starts polling."""
        address = address.upper()
        if address in self.devices:
            raise ValueError("Device already exists.")
        
        ble_device = self.discovered_device_cache.get(address)
        if not ble_device:
            raise ValueError("Device not found in discovery cache. Please re-discover.")
        
        device = self.create_device(address, device_type, {}, ble_device)
        
        _LOGGER.info(f"Testing connection to new device {address}...")
        # Add a small delay to allow the device to be ready for a connection
        await asyncio.sleep(1.0)
        connected = await device.test_connection()

        if not connected:
            await device.disconnect() # Ensure cleanup
            raise ConnectionError("Connection test failed for the new device.")
        
        _LOGGER.info(f"Connection test successful for {address}.")
        self.devices[address] = device
        self.save_devices_to_config()
        await self.start_polling_device(device, publish_discovery=True)
        _LOGGER.info(f"Successfully added and started polling for new device: {address}")
        return device.get_device_info()

    async def remove_device(self, address: str):
        """Stops polling, removes a device, and clears its discovery topics."""
        address = address.upper()
        if address not in self.devices:
            raise ValueError("Device not found.")

        self.stop_polling_device(address)
        
        device_to_remove = self.devices[address]
        if self._mqtt_publisher:
            self._mqtt_publisher.clear_device_topics(device_to_remove)

        del self.devices[address]
        self.save_devices_to_config()
        _LOGGER.info(f"Successfully removed device {address}")

    async def discover_devices(self) -> List[Dict[str, str]]:
        """Scans for BLE devices and returns a list of new discoveries."""
        _LOGGER.info("Starting BLE device scan...")
        # Try multiple times with longer timeout to improve discovery reliability
        max_retries = 3
        timeout = 15.0  # Increased timeout
        
        for attempt in range(max_retries):
            try:
                discovered = await BleakScanner.discover(timeout=timeout)
                self.discovered_device_cache.clear()
                for device in discovered:
                    self.discovered_device_cache[device.address] = device
                
                _LOGGER.info(f"Scan attempt {attempt + 1} complete. Found {len(self.discovered_device_cache)} devices.")
                
                # If we found devices, break out of the retry loop
                if self.discovered_device_cache:
                    break
                    
                # If no devices found and we have more retries, wait a bit before retrying
                if attempt < max_retries - 1:
                    _LOGGER.info(f"No devices found in attempt {attempt + 1}. Retrying in 2 seconds...")
                    await asyncio.sleep(2.0)
                    
            except BleakError as e:
                _LOGGER.error(f"Error during BLE scan attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    _LOGGER.info("Retrying in 2 seconds...")
                    await asyncio.sleep(2.0)
                else:
                    return []
        
        _LOGGER.info(f"Final scan complete. Found {len(self.discovered_device_cache)} devices.")
        
        return [
            {"name": d.name or "Unknown", "address": d.address}
            for d in self.discovered_device_cache.values()
            if d.address not in self.devices
        ]

    async def shutdown(self):
        """Shuts down the device manager, stopping all polling and device connections."""
        _LOGGER.info("Shutting down Device Manager...")
        for address in list(self.polling_tasks.keys()):
            self.stop_polling_device(address)
        
        for device in self.devices.values():
            await device.disconnect()
        _LOGGER.info("All device connections closed.") 