<div align="center">

# BluPow - A Smart & Extensible Bluetooth to MQTT Gateway

</div>

This repository contains the BluPow Gateway and the companion Home Assistant integration. The gateway is designed to be a flexible, multi-device platform for polling data from Bluetooth Low Energy (BLE) power devices and publishing it to MQTT.

**Key Features:**
-   **Extensible:** Easily add support for new devices by creating simple "device profile" files.
-   **Smart Installer:** A single command intelligently detects your Home Assistant environment and performs the correct installation.
-   **User-Friendly:** Designed for a simple setup experience, whether you use Home Assistant OS or run your own Docker containers.

---

## Installation

A single, smart installer script handles everything. It will detect your Home Assistant environment and provide the correct instructions.

1.  Clone or download this repository.
2.  Navigate into the project directory.
3.  Make the installer executable: `chmod +x scripts/install.sh`
4.  Run the installer: `./scripts/install.sh`

The script will then guide you through the final steps for your specific setup.

---

## The BluPow Vision: Extensibility

BluPow is designed to be more than just an integration for a single brand. The architecture allows for easy expansion to support a wide variety of BLE-enabled power equipment.

### Device Profiles
The gateway uses a "device profile" system. Each supported device type has a corresponding Python file in the `blupow_addon/rootfs/app/devices` directory. This profile contains all the logic necessary to communicate with and parse data from that specific device.

### Adding New Devices
Advanced users can add support for new devices by creating their own profile files. For detailed instructions, please see the **[Adding New Devices Guide](docs/ADDING_DEVICES.md)**.

---
## Technical Documentation
For a deeper dive into the system's design, see the **[Technical Architecture Document](docs/TECHNICAL_ARCHITECTURE.md)**.
---
# Guide: Adding New Device Profiles to BluPow

This guide explains how advanced users can add support for new Bluetooth Low Energy (BLE) power devices to the BluPow Gateway.

## 1. The Device Profile Concept

The BluPow Gateway is designed to be extensible. All device-specific logic is contained within individual "profile" files located in the `blupow_addon/rootfs/app/devices/` directory. The gateway automatically discovers and loads any valid profile it finds in this directory.

To add a new device, you need to create a new Python file in this directory that adheres to the required structure.

## 2. Creating a New Profile File

Let's say you want to add support for a "PowerMax 5000" solar controller.

1.  **Create the File:**
    Create a new file named `powermax_5000.py` inside the `devices` directory. The filename (without `.py`) will be used as the `device_type` when adding the device in Home Assistant.

2.  **Implement the Profile:**
    Your file must contain two key components:
    -   A class that inherits from `BaseDevice`.
    -   A factory function named `get_device`.

    Here is a complete template:

    ```python
    from .base import BaseDevice
    from bleak import BleakClient
    from typing import Dict, Any

    # Define any UUIDs, commands, or constants your device needs
    VOLTAGE_UUID = "0000a001-0000-1000-8000-00805f9b34fb"
    COMMAND_UUID = "0000a002-0000-1000-8000-00805f9b34fb"
    GET_STATS_COMMAND = b"\x01\x03\x00\x00\x00\x08\x44\x0C" # Example command

    class PowerMax5000(BaseDevice):
        """
        Profile for the PowerMax 5000 Solar Controller.
        """

        @property
        def name(self) -> str:
            return "PowerMax 5000"

        def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
            """A helper function to parse the raw data from the device."""
            # IMPORTANT: This is where your custom parsing logic goes.
            # You'll need to understand the byte format of your device's response.
            if len(raw_data) < 4:
                return {} # Not enough data
            
            voltage = int.from_bytes(raw_data[0:2], 'big') / 10.0
            current = int.from_bytes(raw_data[2:4], 'big') / 100.0
            
            return {
                "voltage": voltage,
                "current": current,
                "power": voltage * current
            }

        async def get_data(self) -> Dict[str, Any]:
            """
            This is the main method called by the poller. It should handle
            the full sequence of connecting, commanding, and reading from the device.
            """
            # Example sequence:
            # 1. Write a command to the device to request data
            await self._client.write_gatt_char(COMMAND_UUID, GET_STATS_COMMAND)

            # 2. Read the response from the data characteristic
            raw_data = await self._client.read_gatt_char(VOLTAGE_UUID)

            # 3. Parse the raw data using your helper function
            parsed_data = self._parse_data(raw_data)
            
            return parsed_data

    def get_device(client: BleakClient, device_id: str):
        """
        Factory function that must exist in every profile file.
        The poller calls this to get an instance of your device handler.
        """
        return PowerMax5000(client, device_id)
    ```

## 3. Using Your New Profile

1.  **Rebuild the Add-on/Container:**
    After adding your new `.py` file, you must rebuild the BluPow Gateway for it to be included.
    -   **If using the Add-on:** Go to **Settings > Add-ons > BluPow MQTT Gateway** and click **REBUILD**.
    -   **If using Docker:** Run `docker compose up -d --build`.

2.  **Add the Device in Home Assistant:**
    -   Go to **Settings > Devices & Services** and add the BluPow integration.
    -   When prompted for the **Device Type**, enter the name of your new file (e.g., `powermax_5000`).
    -   Provide the MAC address.

The gateway will now use your new profile to poll the device. You can check the logs to see it in action and debug any issues with your parsing logic. 