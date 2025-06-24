# 🛠️ **IMPLEMENTATION GUIDE**

**BluPow Gateway for Home Assistant**

---

## 🎯 **OVERVIEW**

This guide provides a technical walkthrough of the BluPow Gateway, a standalone service that acts as a bridge between Bluetooth Low Energy (BLE) BluPow devices and a Home Assistant instance. The gateway connects to devices, polls them for data, and publishes the results to an MQTT broker, which Home Assistant then consumes.

This decoupled architecture was chosen for its stability, scalability, and robustness, overcoming the challenges of direct Bluetooth integrations within Home Assistant.

---

## 🏗️ **ARCHITECTURE**

The gateway operates as a single, standalone Docker container and is logically divided into three primary modules, promoting a clean separation of concerns.

```mermaid
graph TD;
    subgraph BluPow Gateway Container;
        direction LR;
        
        main[main.py<br/><i>App Lifecycle</i>] -->|creates & uses| DeviceManager;
        main -->|creates & uses| MqttHandler;
        
        subgraph MqttHandler [mqtt_handler.py<br/><i>MQTT Communication</i>];
            direction TB;
            A[Handles MQTT Connection];
            B[Receives Commands<br/>(add, remove, discover)];
            C[Publishes Sensor Data];
            D[Publishes HA Discovery];
        end
        
        subgraph DeviceManager [device_manager.py<br/><i>Device State & Logic</i>];
            direction TB;
            E[Manages Device Dictionary];
            F[Manages BLE Device Cache];
            G[Handles BLE Polling Loops];
            H[Saves/Loads Device Config];
        end

        MqttHandler -->|delegates commands to| DeviceManager;
    end

    HomeAssistant[Home Assistant] <-->|MQTT Broker| MqttHandler;
    DeviceManager <-->|BLE| BluPowDevices[BluPow Devices];

    style main fill:#d4edda,stroke:#155724
    style MqttHandler fill:#cce5ff,stroke:#004085
    style DeviceManager fill:#fff3cd,stroke:#856404
```

### **1. `main.py` - Application Orchestrator**

This is the main entry point for the gateway. Its sole responsibility is to manage the application's lifecycle.

- **Initializes** the `DeviceManager` and `MqttHandler`.
- **Orchestrates** the startup sequence:
    1.  Creates the manager and handler instances.
    2.  Loads saved device configurations from disk.
    3.  Connects to the MQTT broker.
    4.  Starts the polling loops for all loaded devices.
- **Manages** the graceful shutdown sequence, ensuring all connections are closed and tasks are cancelled properly.

### **2. `device_manager.py` - Device Logic and State**

This module is the brain of the gateway, handling all state and direct interaction with BLE devices.

- **`DeviceManager` Class**: A singleton class that holds the state of all devices.
    - **Device Cache**: Maintains a dictionary of all active `BaseDevice` objects.
    - **Polling Tasks**: Manages the lifecycle of the asynchronous polling tasks for each device.
    - **Discovery Cache**: Stores the results of the last BLE scan to enable fast device adding without requiring a second scan.
    - **Configuration**: Handles loading and saving the `devices.json` configuration file.
    - **BLE Lock**: Contains a critical `asyncio.Lock` to ensure that all BLE operations (discovery, adding, polling) are executed sequentially to prevent conflicts at the hardware level.
- **`create_device` (Static Method)**: A factory function that, given a device type and address, returns the correct instantiated device driver object (e.g., `RenogyController`).

### **3. `mqtt_handler.py` - MQTT Communication**

This module isolates all logic related to the MQTT protocol. It acts as the gateway's external communication interface.

- **`MqttHandler` Class**:
    - **Connection Management**: Handles connecting, disconnecting, and automatically reconnecting to the MQTT broker.
    - **Command Handling**: Subscribes to the `blupow/gateway/command` topic and processes incoming JSON-formatted commands (`get_devices`, `discover_devices`, `add_device`, `remove_device`, `restart_gateway`).
    - **Delegation**: Does not implement business logic itself. Instead, it delegates the actions to the `DeviceManager` instance it holds. For example, on receiving an `add_device` command, it calls `device_manager.add_device()`.
    - **State & Discovery Publishing**: Provides methods for publishing sensor data and Home Assistant discovery payloads. These are called by the `DeviceManager` via a callback, maintaining the separation of concerns.

### **4. `devices/` - Device Drivers**

This directory contains the specific drivers for each supported piece of hardware.

- **`base.py`**: Defines the `BaseDevice` abstract base class, which all specific device drivers must inherit. It enforces the implementation of methods like `poll()` and `get_sensor_definitions()`.
- **`renogy_controller.py` / `renogy_inverter.py`**: Concrete implementations for specific Renogy products.
- **`generic_modbus_device.py`**: A flexible driver that can be configured via JSON for any Modbus-over-BLE device, allowing for easy expansion without writing new Python code.

---

## 💡 **DESIGN PHILOSOPHY**

The gateway's architecture is guided by three core principles:

1.  **Stability via Decoupling**: All direct device interaction (especially unstable Bluetooth operations) is handled in a separate process from Home Assistant. If the gateway encounters a fatal error with a device, it can restart without affecting Home Assistant's stability.
2.  **Maintainability via Modularity**: By separating responsibilities into `DeviceManager` (state), `MqttHandler` (communication), and `main` (lifecycle), the codebase is easier to understand, test, and extend. Adding a new feature doesn't require rewriting the entire application.
3.  **Resiliency via Statefulness**: The gateway is designed to be resilient to restarts and failures.
    -   **Configuration on Disk**: The list of added devices is saved to `devices.json`, so the gateway automatically restores its state after a restart.
    -   **BLE Discovery Cache**: The `DeviceManager` caches the results of a discovery scan. This allows the `add_device` command to be nearly instantaneous and robust against race conditions where a device might stop advertising between discovery and addition.

---

## 🔧 **OPERATIONAL FLOW**

### **Startup Sequence**
1.  `main.py` starts.
2.  `DeviceManager` and `MqttHandler` are instantiated.
3.  `DeviceManager` loads `devices.json` into its `devices` dictionary.
4.  `MqttHandler` connects to the MQTT broker.
5.  On successful connection, `MqttHandler._on_connect` is triggered. It iterates through all devices in the `DeviceManager` and publishes their Home Assistant discovery configs.
6.  `main.py` iterates through the loaded devices and starts a dedicated polling task for each one via `DeviceManager.start_polling_device()`.

### **Add Device Flow**
1.  A user triggers a discovery action in the Home Assistant UI.
2.  Home Assistant publishes a `discover_devices` command to the `blupow/gateway/command` topic.
3.  `MqttHandler` receives the command and calls `device_manager.discover_devices()`.
4.  `DeviceManager` performs a `BleakScanner.discover()` and stores the results in its `discovered_device_cache`. It returns a list of newly found devices.
5.  The user selects a device to add in the UI.
6.  Home Assistant publishes an `add_device` command with the device address and type.
7.  `MqttHandler` receives the command and calls `device_manager.add_device()`.
8.  `DeviceManager` retrieves the `BLEDevice` object from its cache (no second scan needed), creates a new driver instance, tests the connection, and if successful, adds it to the active `devices` dictionary, saves the config, and starts the polling loop.
9.  A success response is sent back to Home Assistant.

---

## 🗺️ **ARCHITECTURAL ROADMAP**

The modular architecture provides a strong foundation for future enhancements.

| Status | Feature | Description |
| :--- | :--- | :--- |
| ✅ **Working** | **Decoupled Gateway Architecture** | A standalone Docker container handles all BLE communication, ensuring HA stability. |
| ✅ **Working** | **MQTT Communication** | Uses the industry-standard MQTT protocol for robust and reliable data transfer. |
| ✅ **Working** | **Home Assistant Discovery** | Automatically discovers and configures new devices and their sensors in HA. |
| ✅ **Working** | **UI-Driven Device Management** | Add, remove, and list your devices directly from the Home Assistant interface. |
| ✅ **Working** | **Stateful Device Configuration** | The gateway saves its device list and reloads it on restart. |
| ✅ **Working** | **BLE Discovery Caching** | Discovered devices are cached to prevent race conditions during the add-device flow. |
| 🔜 **Planned** | **Advanced Polling Strategies** | Dynamically adjust polling frequency based on device state (e.g., poll faster when charging). |
| 🔜 **Planned** | **Bluetooth Proxy Integration** | Utilize Home Assistant's Bluetooth proxy capabilities to extend range. |

---

## 🔍 **DEBUGGING THE GATEWAY**

Troubleshooting the gateway involves checking the two main components: the gateway container itself and the MQTT broker.

1.  **Check the Gateway Logs**: This is the most important first step. Use Docker to view the real-time logs of the container.
    ```bash
    # From the blupow_gateway/ directory
    docker compose logs -f
    ```
    Look for any error messages related to Bluetooth, MQTT connection, or device polling.

2.  **Inspect MQTT Traffic**: Use a tool like [MQTT Explorer](http://mqtt-explorer.com/) to connect to your broker and visualize the data flow.
    -   **Check for Commands**: When you perform an action in the HA UI, you should see a message published to the `blupow/gateway/command` topic.
    -   **Check for State**: You should see data being published by the gateway to `blupow/DEVICE_ADDRESS/state` topics.
    -   **Check for HA Discovery**: Ensure that the gateway is publishing configuration payloads to topics under `homeassistant/sensor/`. If these are missing, Home Assistant won't create the sensor entities.

---

## 📋 **PREREQUISITES**

### **System Requirements**
- Home Assistant Core 2024.1+
- Python 3.11+
- Bluetooth adapter with BLE support
- Container/system with appropriate permissions

### **Development Environment**
```bash
# Required packages
pip install bleak>=0.20.0
pip install homeassistant>=2024.1.0

# Development tools
pip install pytest
pip install black
pip install isort
```

### **Permissions Setup**
```bash
# For Docker/Container environments
docker run --privileged \
  --device /dev/bus/usb \
  -v /run/dbus:/run/dbus:ro \
  homeassistant/home-assistant
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Bluetooth permissions configured
- [ ] MAC address validated
- [ ] Device pairing completed
- [ ] All dependencies installed
- [ ] Debug logging enabled

### **Integration Testing**
- [ ] Config flow completes successfully
- [ ] Coordinator starts without errors
- [ ] First data fetch succeeds
- [ ] Sensors appear in Home Assistant
- [ ] Sensor values update correctly
- [ ] Error handling works (device offline test)

### **Production Deployment**
- [ ] Update interval optimized
- [ ] Error logging configured
- [ ] Fallback data handling verified
- [ ] Resource usage monitored
- [ ] Integration stability confirmed

---

## 📊 **PERFORMANCE MONITORING**

### **Key Metrics to Track**

```python
# Add to coordinator for monitoring
class BluPowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, mac_address: str):
        super().__init__(...)
        self._metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'avg_execution_time': 0.0,
            'last_success_time': None,
        }
    
    async def _async_update_data(self):
        start_time = time.time()
        self._metrics['total_updates'] += 1
        
        try:
            result = await self._subprocess_update()
            self._metrics['successful_updates'] += 1
            self._metrics['last_success_time'] = time.time()
            return result
        except Exception:
            self._metrics['failed_updates'] += 1
            raise
        finally:
            execution_time = time.time() - start_time
            # Update rolling average
            self._metrics['avg_execution_time'] = (
                self._metrics['avg_execution_time'] * 0.9 + execution_time * 0.1
            )
```

### **Health Check Script**

```python
# scripts/health_check.py
import asyncio
import sys
sys.path.append("/config/custom_components")

async def health_check():
    """Check integration health."""
    from blupow.blupow_client import BluPowClient
    
    mac_address = "D8:B6:73:BF:4F:75"  # Replace with your device
    client = BluPowClient(mac_address)
    
    print("🔍 BluPow Health Check")
    print(f"Device: {mac_address}")
    
    try:
        print("📡 Attempting connection...")
        connected = await client.connect()
        
        if connected:
            print("✅ Connection successful")
            
            print("📊 Reading data...")
            data = await client.read_device_info()
            
            if data:
                print(f"✅ Data retrieved: {len(data)} fields")
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print("❌ No data retrieved")
            
            await client.disconnect()
            print("✅ Disconnected cleanly")
            
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## 🔧 **CUSTOMIZATION OPTIONS**

### **Adjustable Parameters**

```python
# coordinator.py - Customizable settings
class BluPowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, mac_address: str, **options):
        # Configurable update interval
        update_interval = options.get('update_interval', 30)
        
        # Configurable timeout
        self.subprocess_timeout = options.get('subprocess_timeout', 20.0)
        
        # Configurable retry attempts
        self.max_retries = options.get('max_retries', 3)
        
        super().__init__(
            hass,
            _LOGGER,
            name="BluPow",
            update_interval=timedelta(seconds=update_interval),
        )
```

### **Advanced Configuration**

```yaml
# configuration.yaml
blupow:
  mac_address: "D8:B6:73:BF:4F:75"
  update_interval: 30
  subprocess_timeout: 20.0
  max_retries: 3
  fallback_enabled: true
  debug_subprocess: false
```

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation References**
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Bleak Bluetooth Library](https://bleak.readthedocs.io/)
- [Modbus Protocol Specification](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)

### **Example Integrations**
- [Bluetooth LE Device Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/bluetooth_le_tracker)
- [Modbus Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus)

### **Testing Tools**
- `bluetoothctl` - Bluetooth device management
- `hcitool` - Bluetooth adapter tools
- `nmap` - Network/Bluetooth scanning
- Home Assistant Developer Tools

---

**Implementation Guide Version**: 1.0  
**Last Updated**: June 20, 2025  
**Compatibility**: Home Assistant 2024.1+ 