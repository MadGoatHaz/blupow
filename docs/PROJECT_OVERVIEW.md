# BluPow: Universal BLE to MQTT Gateway for Home Assistant

**ETHOS**: Quality through understanding. Every component has its place. Document thoroughly without clutter. Full comprehension before action.

## Project Overview

BluPow is a comprehensive Home Assistant integration that bridges the gap between Bluetooth Low Energy (BLE) devices and your smart home. It provides real-time monitoring and a stable, extensible platform for integrating a wide variety of BLE-enabled hardware.

The project's primary goal is to provide a reliable, easy-to-use, and easy-to-extend solution for any device that uses BLE to broadcast data, with a special focus on devices using Modbus over BLE, such as many solar power components.

## Architecture Principles

### **1. Stability and Decoupling**
- **Gateway Model**: A standalone Python gateway, running in Docker, handles all BLE communication. This isolates potentially unstable Bluetooth interactions from the Home Assistant core, preventing crashes or slowdowns.
- **MQTT for Communication**: The gateway communicates with Home Assistant exclusively through MQTT. This is a robust, lightweight, and standard protocol for IoT communication.
- **HA Integration**: The Home Assistant component is extremely lightweight. Its only jobs are to provide a configuration UI and listen for device announcements via MQTT.

### **2. Extensibility**
- **Device-Agnostic Core**: The gateway is not tied to any specific brand (e.g., Renogy). Its core function is to scan for, connect to, and manage BLE devices.
- **Driver-Based Design**: Support for new devices is added by creating new "device driver" classes. This makes expansion straightforward and modular.
- **Generic Support**: The architecture can easily support any device that exposes data over BLE, from power inverters to temperature sensors and beyond.

### **3. Intelligence (Future Goal)**
- **Optimized Polling**: The system is designed to eventually move beyond static polling intervals. Future versions will aim to adjust polling frequency dynamically based on device state (e.g., polling an inverter more frequently when under heavy load).
- **Resource Awareness**: The gateway will be able to integrate with Home Assistant's Bluetooth proxies, allowing for greater range and removing the need for dedicated hardware on the host machine.

## Technical Architecture

### **Data Flow**
The data flow is simple and robust:
`BLE Device → BluPow Gateway (Docker) → MQTT Broker → Home Assistant Integration → HA Sensors`

### **Component Structure**
The project is split into two main components:
```
/
├── blupow_gateway/             # The standalone Python BLE-to-MQTT Gateway
│   ├── app/
│   │   ├── main.py             # App lifecycle orchestrator
│   │   ├── device_manager.py   # Handles all device state, logic, and polling
│   │   ├── mqtt_handler.py     # Manages all MQTT communication and command handling
│   │   └── devices/            # Directory for individual device drivers
│   │       ├── base.py         # Base class for all device drivers
│   │       └── renogy_*.py     # Example drivers for Renogy devices
│   └── Dockerfile
│
└── custom_components/
    └── blupow/                 # The Home Assistant integration
        ├── __init__.py
        ├── config_flow.py      # Handles the UI for discovery and adding devices
        └── manifest.json
```

## How Device Discovery Works
1. The user initiates discovery from the Home Assistant UI.
2. The HA integration publishes a `discover_devices` command to the `blupow/gateway/command` MQTT topic.
3. The BluPow Gateway receives the command and initiates a BLE scan.
4. The gateway performs a broad scan, filtering out only devices that have already been added to avoid clutter. **It does not filter by brand or name.**
5. It publishes the list of found devices back to a response topic.
6. The Home Assistant `config_flow` shows the user the list of discovered devices.
7. The user selects a device to add, and the `config_flow` sends an `add_device` command to the gateway.
8. The gateway creates, tests, and saves the new device, then publishes its MQTT discovery configuration to Home Assistant, which automatically creates the corresponding entities.

## Architectural Roadmap

Our modular architecture provides a strong foundation for future enhancements. The `DeviceManager` is the key enabler for most upcoming features.

### **Phase 1: Core Functionality (Complete)**
- **[✅] Decoupled Gateway**: Stable, standalone service.
- **[✅] MQTT Integration**: Robust communication layer.
- **[✅] UI-Driven Device Management**: Easy configuration from Home Assistant.
- **[✅] Core Device Drivers**: Support for Renogy and a generic Modbus template.

### **Phase 2: Intelligence and Efficiency (Planned)**
- **[🔜] Advanced Polling Engine**: The `DeviceManager` will be enhanced to support dynamic polling rates. For example, it could poll a solar controller every 5 seconds when `solar_power > 0` but drop to every 60 seconds at night to conserve resources.
- **[🔜] Bluetooth Proxy Integration**: We plan to leverage Home Assistant's Bluetooth proxy infrastructure. The `DeviceManager`'s connection logic will be updated to intelligently choose between a local adapter and a remote proxy, vastly improving placement flexibility and range.
- **[🔜] Expanded Device Library**: Add official drivers for common device categories:
    - Battery Management Systems (BMS)
    - Smart Shunts
    - DC-DC Chargers
    - Environmental Sensors (Temperature, Humidity)

The process for adding new community drivers remains simple:
1. Create a new Python class in the `blupow_gateway/app/devices/` directory that inherits from `BaseDevice`.
2. Implement the `poll()` and `get_sensor_definitions()` methods for your specific device.
3. Update the `create_device` factory function in `device_manager.py` to recognize your new device type.

## Success Metrics

1. **Stability**: The gateway runs reliably without impacting Home Assistant's performance.
2. **Extensibility**: New devices can be added with minimal, isolated code changes.
3. **Usability**: The device discovery and addition process is simple and intuitive for the end-user.
4. **Reliability**: Data from devices is polled accurately and consistently.
5. **Maintainability**: The codebase remains clean, modular, and well-documented.
6. **Efficiency**: The gateway uses system resources (CPU, BLE bandwidth) intelligently and respectfully.

---

<p align="center">
  <strong>🚀 Welcome to the BluPow Project!</strong><br/>
  <em>A universal bridge for your Bluetooth devices.</em>
</p> 