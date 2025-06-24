# BluPow Project Genesis & AI Protocol

## ❗ AI DIRECTIVES: MANDATORY ONBOARDING PROTOCOL

**To the AI Assistant:**

**This is your primary instruction set. Read this document completely before taking any other action. Do not skim. Your primary goal is to maintain project stability and accelerate development by avoiding past mistakes.**

**The core problem this protocol solves is session-to-session context loss. Failure to follow these directives will lead to wasted time and destructive errors.**

### Onboarding Checklist
*Before you proceed, you must affirm your understanding and adherence to these points in your first response.*

- `[ ]` I acknowledge that I must read this entire document before performing any other file-system or code-related action.
- `[ ]` I have read the "Table of Critical Failures" and I understand that I am not to delete files without migrating their value, nor am I to alter the `README.md`'s user-facing content.
- `[ ]` I have read the 3-step deployment workflow and understand it is the only correct way to deploy changes.
- `[ ]` I commit to stating my plan and rationale before executing any complex or destructive action (e.g., `rm -rf`, major refactoring).

---

## 🏛️ **THE THREE PILLARS OF DEVELOPMENT: A MANDATORY STRATEGIC WORKFLOW**

This project adheres to a strict, high-level workflow to ensure quality, prevent regressions, and maintain a clean, understandable codebase. These are not suggestions; they are core requirements for all significant changes.

### **Pillar 1: Documentation First**
-   **The Rule**: Before a major refactor or the addition of a new feature, the relevant public-facing documentation (`README.md`) and technical guides (`IMPLEMENTATION_GUIDE.md`, `CONTRIBUTING.md`, etc.) **must be updated first**.
-   **The Rationale**: This methodology forces a clear, well-defined plan. The documentation becomes the contract and the definition of "done." The code is then written or refactored to fulfill this contract. This prevents scope creep and guarantees that documentation is never an afterthought, but rather the blueprint that guides the work.

### **Pillar 2: Refactor, then Enhance**
-   **The Rule**: You shall not add new features to unstable, poorly understood, or undocumented code. If a module is a known source of bugs or lacks clarity, it **must be refactored, stabilized, and documented first** before any new functionality is built upon it.
-   **The Rationale**: Building on a shaky foundation multiplies technical debt and guarantees future failures. We must stabilize and fully comprehend a component *before* we attempt to extend it. This prevents the "house of cards" effect where one change causes cascading, unrelated problems.

### **Pillar 3: Clean as You Go**
-   **The Rule**: When a piece of code, a script, a test, or a document is made obsolete by a refactor, it **must be removed** as part of the same commit or pull request. There is no "we'll clean it up later."
-   **The Rationale**: Dead code and stale documentation are not harmless artifacts; they are liabilities. They mislead future developers, create confusion, and pollute the codebase, making it harder to navigate and trust. Removing them immediately is a mandatory part of completing the work.

---

## 📖 TABLE OF CRITICAL FAILURES

This section documents key failures from past sessions. Understanding them is critical to avoiding repetition.

| Failure Point | The Mistake | The Correct Protocol & Rationale |
| :--- | :--- | :--- |
| **UI Fails to Load** | Assuming `strings.json` was sufficient; deleting `translations/en.json`. | Home Assistant **mandates** that `custom_components/<integration>/translations/en.json` exists and is a 1:1 copy of `strings.json`. Failure to adhere to this will break the integration's UI. |
| **Incomplete Deployment** | Only restarting the gateway (`docker compose up`) after changing `custom_components` code. | The full 3-step deployment is **mandatory**: 1. Deploy Gateway (`install.sh`), 2. Copy Component (`sudo cp`), 3. Restart Home Assistant Server. Failure to follow all three steps results in old code running in HA. |
| **Premature Deletion** | Deleting the `docs/guides` directory without first reading the files and migrating their valuable content. | Always read files to assess for unique, hard-won knowledge before deleting them. The `git restore` command was required to fix this mistake. |
| **`config_flow.py` Instability** | A custom `GatewayClient` class was implemented with its own `asyncio` logic. | This caused `AttributeError` and event loop conflicts. The refactor to use Home Assistant's native MQTT helpers (`mqtt.async_publish`, `mqtt.async_subscribe`) is the stable, correct pattern. **Do not re-introduce a custom client.** |
| **`README.md` Overwrite** | Replacing the user-and-sponsor-focused `README.md` with a developer-focused one. | The main `README.md` is for the project's public face. Do not remove sponsorship, support, or user-facing installation information. Verify its content before editing. |
| **Hardcoded "Fake" Data** | Diagnostic scripts contained a hardcoded MAC address. | This created massive confusion during testing. All hardcoded test data has been removed and should not be reintroduced. |
| **`git commit` Failure** | Using a multi-line commit message with special characters directly on the command line. | The shell can misinterpret special characters and newlines. For complex commit messages, wrap the entire message in single quotes (`'`) to ensure it is treated as a single string. |
| **`asyncio` Event Loop Conflict** | A `BLE_LOCK` was created on the main thread but the Paho-MQTT callback, which tried to use it, runs in a separate thread. | This caused a fatal `RuntimeError: ... attached to a different loop`. When mixing `asyncio` with a threaded library, all calls into `asyncio` from the other thread **MUST** be scheduled via `asyncio.run_coroutine_threadsafe(coro, loop)`. Direct calls or `async` callbacks will fail. |
| **Brittle Discovery Filter** | The discovery logic in the gateway included an `if dev.name` check. | If a BLE device doesn't broadcast a name, or the name is missed during a scan, the device was filtered out and became impossible to add. The discovery must be inclusive of **all** non-configured devices; filtering should only happen on the `address` to avoid duplicates. |
| **Deceptive Docker Environment** | Countless hours were wasted debugging application code that was not actually running. | The runtime environment is guilty until proven innocent. Verify that `docker-compose.yml` is building from source (`build:`), mounting the app directory as a volume (`volumes: ['./app:/app']`), using the correct network (`network_mode: "host"`), and has necessary system access (`/var/run/dbus`). |
| **Unreliable Edit Model** | The `edit_file` tool repeatedly failed to apply both complex and simple changes correctly, often corrupting the file. | If an edit is mangled or fails to apply, do not attempt to fix it with more edits. The reliable workaround is to **delete the file** and immediately **recreate it** with the full, correct content in a single step. |

---

## 🚀 Full Deployment Workflow (Local Development)

This is the complete, verified workflow for deploying changes to both the gateway and the Home Assistant component on a local development machine.

**Prerequisite**: You are in the root of the `blupow` project directory. The host machine has a working Bluetooth adapter and a running Docker daemon.

### Step 1: Deploy the BluPow Gateway
The gateway runs as a Docker container. We use `docker compose` to build and run it. The `install.sh` script is the preferred method as it handles MQTT broker setup.

```bash
# This script builds the gateway image and launches the container.
# It also ensures an MQTT broker is running for the gateway to connect to.
./scripts/install.sh
```
*Verification*: Check that the gateway is running: `docker ps`. You should see a `blupow-gateway` container.

### Step 2: Deploy the Home Assistant Custom Component
The component files must be copied into your live Home Assistant configuration directory.

1.  **Identify HA Config Directory**: The Home Assistant `custom_components` directory is typically located at `~/.homeassistant/config/custom_components` or `/home/madgoat/opt/homeassistant/config/custom_components`.

2.  **Copy the Files**: Use `sudo` to copy the component files from the project into your Home Assistant instance.

    ```bash
    # Replace the destination path with your actual HA config path if different.
    sudo cp -r custom_components/blupow /home/madgoat/opt/homeassistant/config/custom_components/
    ```

### Step 3: Restart Home Assistant
Home Assistant **MUST** be restarted to load the new version of the custom component. This can be done via the UI (**Settings -> System -> Restart**) or from the command line if you have access.

**This three-step process is not optional.** Failure to follow it will result in the old code running, and your changes will not be reflected.

---

## 🏛️ System Architecture

The system uses a stable, decoupled architecture to isolate unstable Bluetooth operations from Home Assistant.

*   **BluPow Gateway (`blupow_gateway`)**: A standalone Docker container responsible for all BLE communication, device polling, and data parsing. It publishes sensor data and MQTT discovery topics. It listens for commands to dynamically manage its list of polled devices.

*   **MQTT Broker**: The central message bus (e.g., Mosquitto). It facilitates all communication.

*   **Home Assistant Integration (`custom_components/blupow`)**: A lightweight component inside Home Assistant. Its primary role is to provide the UI (Config Flow) for adding and removing devices. It publishes management commands (e.g., `add_device`, `discover_devices`, `remove_device`) to the gateway via MQTT. It does **not** create sensors directly; it relies on the gateway's MQTT discovery messages.

### Communication Protocol
-   **Commands**: HA Integration -> Gateway. Published to `blupow/gateway/command`. Uses a request/response pattern with a unique response topic for each command (e.g., `blupow/gateway/response/<request_id>`).
-   **Sensor State**: Gateway -> HA. Published to device-specific topics (e.g., `blupow/<mac_address>/state`).
-   **Discovery**: Gateway -> HA. Published to Home Assistant's standard discovery topics (e.g., `homeassistant/sensor/blupow_<mac>_volts/config`).

---

## 📖 Key Historical Context & Decisions

*   **Initial UI Failures**: The integration initially suffered from blank screens and crashes during setup. This was traced to two root causes:
    1.  A missing `translations/en.json` file, which is mandatory for custom components.
    2.  A fundamentally broken `config_flow.py` that attempted to manage its own MQTT client and event loop, causing conflicts with Home Assistant's core.
*   **The Great Refactor (`config_flow.py`)**: The configuration flow was completely rewritten to use Home Assistant's built-in MQTT helpers (`mqtt.async_publish`, `mqtt.async_subscribe`). A robust `gateway_request` context manager was created to handle the request/response pattern reliably with timeouts.
*   **Elimination of Fake Data**: Early versions contained hardcoded "fake" device MAC addresses in diagnostic scripts, which caused significant confusion. These have all been purged and replaced with environment variables or dynamic discovery.
*   **Gateway API Standardization**: The gateway's commands (`discover_devices`, `add_device`, `get_devices`, `remove_device`) were standardized to all use the same request/response pattern for consistency and reliability.
*   **`install.sh` Incompleteness**: The installer script was found to only deploy the gateway, not the Home Assistant component itself. This led to confusion where gateway changes were live but UI changes were not. The documented workflow now includes the manual `sudo cp` step to rectify this.

---

## 🔮 Future Vision

With a stable core, the focus is on quality-of-life improvements and expanded support.
*   **Diagnostics**: Add a diagnostics section to the integration to expose gateway status and device polling statistics.
*   **Expand Device Support**: Add new dedicated drivers for other popular devices.
*   **Documentation**: Continuously refine this blueprint and other documentation as the project evolves.

---

## ⚙️ Feature Guide: Custom & Generic Devices

The gateway includes a powerful `generic_modbus_device` driver that allows you to integrate a wide variety of Modbus-over-BLE devices without writing any new code.

### How It Works
By setting a device's `type` to `generic_modbus_device` in the gateway's configuration, you can provide a `config` block that tells the gateway exactly how to communicate with and interpret data from your device. The gateway will then automatically handle polling and Home Assistant MQTT discovery.

### Configuration Example
```json
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
                "register": 100, "words": 1, "scale": 0.1,
                "unit": "V", "device_class": "voltage"
            },
            {
                "key": "total_energy",
                "name": "Total Energy",
                "register": 2500, "words": 2, "scale": 0.001,
                "unit": "kWh", "device_class": "energy", "state_class": "total_increasing"
            }
        ]
    }
}
```
*For a full list of sensor parameters, see the original `CUSTOM_DEVICE_GUIDE.md` in the `git` history.*

---

## ⚡ Feature Guide: Home Assistant Energy Dashboard

The BluPow integration is designed to work seamlessly with Home Assistant's Energy Dashboard.

### Default Sensor Mapping
| Energy Dashboard Category | BluPow Sensor Name     | Entity ID Suffix      |
| ------------------------- | ---------------------- | --------------------- |
| **Grid Consumption**      | `AC Load Power`        | `load_active_power`   |
| **Solar Production**      | `Solar Input Power`    | `solar_power`         |
| **Battery In/Out**        | `Battery Charging Power` & `AC Load Power` | `charging_power` & `load_active_power` |

### Configuration Steps
1.  In Home Assistant, navigate to **Settings -> Dashboards -> Energy**.
2.  Use the "Add" buttons to map the corresponding BluPow sensors from the table above.
3.  For **Battery Storage**, use `charging_power` for "Battery Charge" and `load_active_power` for "Battery Discharge".

### Advanced Usage with Template Sensors
Create powerful derived sensors in your `configuration.yaml`:
```yaml
template:
  - sensor:
      # Shows positive power when charging, negative when discharging
      - name: "Battery Power Flow"
        unit_of_measurement: "W"
        device_class: power
        state: >
          {% set charging = states('sensor.your_charging_power_sensor') | float(0) %}
          {% set discharging = states('sensor.your_load_power_sensor') | float(0) %}
          {% if charging > 0 %}
            {{ charging }}
          {% else %}
            {{ -1 * discharging }}
          {% endif %}
```