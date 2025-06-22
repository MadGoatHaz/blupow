# BluPow Technical Architecture

This document outlines the technical architecture of the BluPow Home Assistant integration ecosystem. The architecture is designed for stability, reliability, and ease of use, leveraging containerization and a decoupled message-passing system.

## Core Components

The BluPow system is composed of three main containerized components that work together to bring device data into Home Assistant.

### 1. BluPow MQTT Gateway (`blupow-gateway`)

*   **Description**: A standalone Docker container responsible for all communication with Bluetooth Low Energy (BLE) devices. It acts as a bridge, polling devices for data and publishing it to an MQTT broker.
*   **Technology**: Python, using the `bleak` library for BLE communication and `paho-mqtt` for MQTT communication.
*   **Key Features**:
    *   **Stateless Polling**: The gateway does not hold long-term state. It polls devices at a configurable interval.
    *   **Dynamic Device Loading**: Device-specific logic is loaded dynamically from "Device Profiles" (see below).
    *   **MQTT Command & Control**: The gateway listens on an MQTT topic (`blupow/command`) for commands like `add_device` or `remove_device`.
    *   **Resilience**: Runs as an independent, restartable service managed by Docker.

### 2. BluPow-Managed MQTT Broker (`blupow-mosquitto`)

*   **Description**: A dedicated, pre-configured Mosquitto MQTT broker, also running in a Docker container. This is the central message bus for the BluPow ecosystem.
*   **Technology**: `eclipse-mosquitto` Docker image.
*   **Key Features**:
    *   **Zero-Configuration**: The `install.sh` script sets up this broker automatically, requiring no user intervention for the recommended "Quick Install".
    *   **Isolated**: It runs on a dedicated Docker network (`blupow-net`), ensuring no conflicts with other services on the host.
    *   **Persistent**: Uses a host-mounted volume (`~/blupow_broker`) to persist data and logs across restarts.
    *   **Simplified Auth**: Configured for anonymous local access to simplify setup, as it's isolated on its own network.

### 3. Home Assistant Custom Component (`custom_components/blupow`)

*   **Description**: The integration that runs inside Home Assistant. It discovers and displays the data published by the gateway.
*   **Technology**: Home Assistant Integration Platform.
*   **Key Features**:
    *   **MQTT Discovery**: Uses Home Assistant's native MQTT Discovery mechanism. The gateway publishes configuration payloads that allow Home Assistant to automatically create sensor entities.
    *   **UI Configuration**: The integration features a configuration flow (`config_flow.py`) that guides the user through connecting to an MQTT broker.
    *   **Device Representation**: Creates Home Assistant `device` entries and links all `sensor` entities to that device for a clean user experience.

## Data Flow & Networking

The standard data flow in a BluPow-managed installation is as follows:

1.  **Installation**: The user runs `scripts/install.sh`, which creates the `blupow-net` Docker network and launches the `blupow-mosquitto` and `blupow-gateway` containers on it.
2.  **Configuration**: The user adds the BluPow integration in Home Assistant. This will eventually be extended to manage devices directly from the UI. Currently, devices are added via the `devices.json` configuration file.
3.  **Polling**: The `blupow-gateway` reads its configuration, discovers the specified devices, and connects to them via BLE.
4.  **Publishing**: The gateway parses the data according to the device's profile and publishes two types of messages to the `blupow-mosquitto` broker:
    *   **Discovery Payload**: A message to a topic like `homeassistant/sensor/blupow_D8B673BF4F75_battery_voltage/config`. This message contains a JSON payload telling Home Assistant how to create a "Battery Voltage" sensor for the device.
    *   **State Payload**: A message to a topic like `blupow/D8B673BF4F75/state`. This contains the actual sensor data (e.g., `{"battery_voltage": 12.5}`).
5.  **Home Assistant Integration**:
    *   The main Home Assistant MQTT integration (which must be configured to connect to the `blupow-mosquitto` broker) "sees" the discovery payload and creates the corresponding sensor entity.
    *   The new sensor entity listens to the state topic for updates.
6.  **Display**: The sensor appears in the Home Assistant UI with the correct data.

```mermaid
graph TD
    subgraph Host Machine
        subgraph Docker
            subgraph blupow-net (Docker Network)
                A[blupow-gateway] -- MQTT --> B[blupow-mosquitto]
            end
            C[Home Assistant] -- MQTT --> B
        end
        D(Renogy BLE Device) -- BLE --> A
    end
```

## Extensibility: The Driver-Based Model

The gateway is designed to be easily extensible to support new devices without changing the core gateway code. This is achieved through a **Driver-Based Model**.

*   **Location**: Drivers are Python classes located in the `blupow_gateway/app/devices/` directory.
*   **Structure**: Each driver (e.g., `renogy_controller.py`) defines a class that inherits from the abstract `BaseDevice` class. This ensures all drivers expose a consistent interface.
*   **Function**: The driver contains all the device-specific logic:
    *   The specific BLE characteristics to use for communication.
    *   The logic for building and parsing Modbus (or other protocol) commands.
    *   A complete definition of all sensors the device exposes, including names, units, and Home Assistant device classes.
*   **Dynamic Loading**: At startup, the gateway automatically scans the `devices` directory and loads any valid driver it finds. The `type` name used in the configuration (e.g., `renogy_controller`) is automatically derived from the driver's class name (`RenogyController`).

This approach makes adding a new, unique device as simple as creating a new driver file that implements the `BaseDevice` contract.

### The `GenericModbusDevice` Driver: Codeless Integration

To further enhance extensibility, the gateway includes the `generic_modbus_device.py` driver. This special driver allows users to integrate a vast range of new devices **without writing any Python code**.

*   **Configuration-Driven**: By setting a device's `type` to `generic_modbus_device` in the configuration, a user can provide a `config` block that defines the device's entire protocol.
*   **Capabilities**: The user can specify the Modbus device ID, BLE UUIDs, and a complete list of sensors, including their registers, data types, and scaling factors.
*   **Reference**: For detailed instructions, see the **[Custom Device Configuration Guide](guides/CUSTOM_DEVICE_GUIDE.md)**.

## Future Vision: Fully UI-Driven Management

The next evolution of the architecture will focus on enhancing the `config_flow.py` in the Home Assistant component to create a seamless, UI-driven experience.

*   **Smart Broker Selection**: The UI will guide the user to either:
    1.  **Use the BluPow-Managed Broker (Default)**: The integration will know how to connect to the `blupow-mosquitto` container automatically.
    2.  **Connect to a Custom Broker**: The user can provide the credentials for their own existing MQTT setup.
*   **Device Management from UI**: The Home Assistant integration will manage its own internal MQTT client to publish `add_device` and `remove_device` commands to the gateway. This will remove the need for users to manually edit `devices.json`, making the entire system configurable from the Home Assistant UI.
