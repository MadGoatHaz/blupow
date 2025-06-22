# BluPow Gateway: Custom Device Configuration Guide

The BluPow Gateway now includes a powerful `generic_modbus_device` driver that allows you to integrate a wide variety of Modbus-over-BLE devices without writing any new code. If you have a device that uses a standard Modbus RTU protocol over a Bluetooth Low Energy serial-like service, you can likely integrate it using this method.

## How It Works

You configure your device in the gateway's `devices.json` file. By setting the `type` to `generic_modbus_device`, you can provide a `config` block that tells the gateway exactly how to communicate with and interpret data from your device.

The gateway will use this configuration to:
1.  Connect to the specified BLE device.
2.  Send Modbus read commands for each sensor you define.
3.  Parse the incoming data according to your specifications (scaling, signed/unsigned, etc.).
4.  Publish the data to MQTT.
5.  Automatically announce the device and its sensors to Home Assistant using MQTT Discovery.

## Configuration Example

Below is an example of a `devices.json` file configured to poll a hypothetical "Custom Power Meter" in addition to a standard Renogy Controller.

`/app/config/devices.json`:
```json
{
    "AA:BB:CC:DD:EE:FF": {
        "type": "renogy_controller"
    },
    "11:22:33:44:55:66": {
        "type": "generic_modbus_device",
        "config": {
            "device_id": 1,
            "notify_uuid": "0000ffe1-0000-1000-8000-00805f9b34fb",
            "write_uuid": "0000ffe2-0000-1000-8000-00805f9b34fb",
            "sensors": [
                {
                    "key": "main_voltage",
                    "name": "Main Voltage",
                    "register": 100,
                    "words": 1,
                    "scale": 0.1,
                    "unit": "V",
                    "device_class": "voltage",
                    "icon": "mdi:flash"
                },
                {
                    "key": "current_flow",
                    "name": "Current Flow",
                    "register": 102,
                    "words": 1,
                    "scale": 0.01,
                    "signed": true,
                    "unit": "A",
                    "device_class": "current",
                    "icon": "mdi:current-ac"
                },
                {
                    "key": "total_energy",
                    "name": "Total Energy",
                    "register": 2500,
                    "words": 2,
                    "scale": 0.001,
                    "unit": "kWh",
                    "device_class": "energy",
                    "state_class": "total_increasing"
                },
                {
                    "key": "device_temp",
                    "name": "Device Temperature",
                    "register": 50,
                    "words": 1,
                    "unit": "°C",
                    "device_class": "temperature",
                    "icon": "mdi:thermometer"
                }
            ]
        }
    }
}
```

### `config` Block Parameters

*   `device_id` (integer, optional, default: `1`): The Modbus slave ID of your device.
*   `notify_uuid` (string, required): The UUID of the BLE characteristic the gateway should listen on for responses.
*   `write_uuid` (string, required): The UUID of the BLE characteristic the gateway should write commands to.
*   `sensors` (list, required): A list of sensor objects to be polled.

### `sensors` Object Parameters

Each object in the `sensors` list defines one sensor to be created in Home Assistant.

*   `key` (string, required): A unique, machine-friendly identifier for the sensor (e.g., `battery_soc`). This is used in the MQTT JSON payload.
*   `name` (string, required): The human-friendly name that will appear in Home Assistant (e.g., `Battery SOC`).
*   `register` (integer, required): The Modbus holding register to read from.
*   `words` (integer, optional, default: `1`): The number of 16-bit words to read. Most values are 1 word (2 bytes), but larger values like total energy might be 2 words (4 bytes).
*   `scale` (float, optional, default: `1.0`): A factor to multiply the raw value by. For example, if the device returns voltage as `2401`, a scale of `0.1` will result in `240.1`.
*   `signed` (boolean, optional, default: `false`): Set to `true` if the value can be negative (e.g., current that can flow in two directions).
*   `unit` (string, optional): The unit of measurement (e.g., `V`, `A`, `W`, `kWh`, `°C`).
*   `device_class` (string, optional): The Home Assistant device class for proper UI representation (e.g., `voltage`, `power`, `energy`).
*   `state_class` (string, optional): The Home Assistant state class, crucial for long-term statistics (e.g., `total_increasing` for energy meters).
*   `icon` (string, optional): A specific `mdi:icon` name to override the default Home Assistant icon.

With this guide, you should be able to configure a wide range of new devices for monitoring with your BluPow Gateway. 