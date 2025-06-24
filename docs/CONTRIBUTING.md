# Contributing to BluPow

> [!IMPORTANT]
> **Maintainer Rules of Engagement & Workflow**: Before making any changes, review the established rules and workflow in [`docs/development/MAINTAINER_RULES.md`](./development/MAINTAINER_RULES.md). These rules are non-negotiable.

Welcome, and thank you for your interest in contributing to the BluPow project! This document provides guidelines to ensure a smooth development process.

# 🤝 Contributing to BluPow Integration

Thank you for your interest in contributing to the BluPow Home Assistant integration! We welcome contributions from the community and are excited to work with you.

---

## 🎯 **Quick Start for Contributors**

### **1. Development Setup**
```bash
# Clone the repository
git clone https://github.com/MadGoatHaz/blupow.git
cd blupow

# Create development environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

### **2. Test Your Setup**
```bash
# Run quick integration test
python3 scripts/quick_integration_test.py

# Run comprehensive test suite
python3 scripts/comprehensive_integration_test.py
```

### **3. Make Your Changes**
- Follow our coding standards (see below)
- Test thoroughly with the provided tools
- Update documentation as needed

### **4. Submit Your Contribution**
- Create a feature branch
- Make your changes
- Test everything works
- Submit a pull request

---

## 🛠️ **Development Environment**

### **Prerequisites**
- **Python 3.11+** (3.12+ recommended)
- **Home Assistant Core 2024.1.0+**
- **Bluetooth adapter** for testing
- **Renogy BluPow device** (for full testing)

### **Development Dependencies**
```bash
# Create requirements-dev.txt if not exists
pip freeze > requirements-dev.txt

# Essential development packages
pip install:
- pytest>=7.0.0
- black>=23.0.0
- flake8>=6.0.0
- mypy>=1.0.0
- pre-commit>=3.0.0
```

### **Home Assistant Development Setup**
```bash
# Install Home Assistant in development mode
pip install homeassistant

# Or use the development container (recommended)
# See: https://developers.home-assistant.io/docs/development_environment/
```

---

## 📋 **Types of Contributions**

### **🐛 Bug Fixes**
- **Sensor issues**: Unavailable sensors, incorrect values
- **Connection problems**: Bluetooth connectivity, timeouts
- **Performance issues**: Memory leaks, slow responses
- **Integration bugs**: Home Assistant compatibility

### **✨ Feature Enhancements**
- **New sensor types**: Additional monitoring capabilities
- **Device support**: New BluPow models
- **UI improvements**: Better configuration, dashboards
- **Performance optimizations**: Faster updates, lower overhead

### **📚 Documentation**
- **User guides**: Installation, configuration, troubleshooting
- **Developer docs**: Architecture, API documentation
- **Examples**: Dashboard configurations, automations
- **Translations**: Multi-language support

### **🧪 Testing & Quality**
- **Test cases**: Unit tests, integration tests
- **Performance testing**: Load testing, stress testing
- **Device compatibility**: Testing with different models
- **Quality assurance**: Code review, static analysis

---

## 🏗️ How to Add Support for a New Device

The BluPow Gateway is designed to be easily extensible. All device-specific logic is contained within **Driver** classes.

### **Option 1: The Device Uses Modbus (The Easy Way)**

If your device uses a standard Modbus protocol over BLE, you can likely add support without writing any code by using the `GenericModbusDevice` driver.

1.  **Read the Guide**: First, read the **[Custom Device Configuration Guide](guides/CUSTOM_DEVICE_GUIDE.md)** to understand how it works.
2.  **Find Device Specs**: You will need to know your device's Modbus register map and the UUIDs for its BLE service.
3.  **Configure `devices.json`**: Add a new entry for your device with the `type` set to `generic_modbus_device` and create the required `config` block.
4.  **Test**: Restart the gateway and check the logs. If the configuration is correct, your device should appear in Home Assistant.
5.  **Contribute**: If it works, please consider sharing your `config` block in a GitHub discussion so others can benefit!

### **Option 2: The Device Uses a Custom Protocol (The Developer Way)**

If your device has a non-standard communication protocol, you will need to create a new Python driver.

1.  **Create a New Driver File**: In the `blupow_gateway/app/devices/` directory, create a new file (e.g., `my_new_device.py`).
2.  **Create the Driver Class**: Inside the file, create a class that inherits from `BaseDevice`. The class name should be in CamelCase (e.g., `MyNewDevice`). The gateway will automatically use a snake_case version of this name (`my_new_device`) as the `type` in the configuration.
    ```python
    from .base import BaseDevice
    # ... other imports

    class MyNewDevice(BaseDevice):
        """Driver for the awesome new device."""
        
        def __init__(self, address: str, device_type: str):
            super().__init__(address, device_type)
            # Add any device-specific initialization here
        
        def get_sensor_definitions(self) -> List[Dict[str, Any]]:
            # Return a list of dicts defining your sensors for HA discovery
            # See renogy_controller.py for a detailed example
            return [
                {"key": "voltage", "name": "Voltage", "unit": "V"},
                # ... other sensors
            ]

        async def get_data(self) -> Optional[Dict[str, Any]]:
            # This is the core logic. Connect to the device via Bleak,
            # send commands, parse data, and return a dictionary 
            # where keys match the 'key' in your sensor definitions.
            # See renogy_controller.py for a detailed example.
            pass
    ```
3.  **Implement the Methods**:
    *   `get_sensor_definitions()`: This method must return a list of dictionaries, one for each sensor your device exposes. This data is used for Home Assistant's MQTT discovery.
    *   `get_data()`: This is where you implement the actual communication. Use the `bleak` library to connect, write, and read data. Parse the data and return it in a dictionary.
4.  **Test**: Configure your new device in `devices.json` using the auto-generated `type` and test it thoroughly.
5.  **Submit a Pull Request**: Once you are confident it works well, submit a PR to share your new driver with the community.

---

## 🎨 **Coding Standards**

### **Python Style Guide**
We follow **PEP 8** with some specific preferences:

```python
# ✅ Good: Clear, descriptive names
def get_battery_voltage(self) -> float:
    """Get current battery voltage in volts."""
    return self._data.get("battery_voltage", 0.0)

# ❌ Avoid: Unclear abbreviations
def get_bv(self):
    return self._data.get("bv", 0)

# ✅ Good: Type hints and docstrings
async def update_data(self) -> dict[str, Any]:
    """Update device data and return sensor values.
    
    Returns:
        dict: Sensor data with keys matching sensor definitions
        
    Raises:
        ConnectionError: If device cannot be reached
    """
    
# ✅ Good: Error handling
try:
    data = await self._client.get_data()
    return self._process_data(data)
except BluetoothConnectionError as err:
    _LOGGER.warning("Connection failed: %s", err)
    raise UpdateFailed(f"Failed to update: {err}") from err
```

### **Home Assistant Integration Standards**
```python
# ✅ Good: Proper entity naming
@property
def unique_id(self) -> str:
    """Return unique ID for this sensor."""
    return f"{self._device_mac}_{self._sensor_key}"

@property
def name(self) -> str:
    """Return friendly name for this sensor."""
    return f"{self._device_name} {self._sensor_config.name}"

# ✅ Good: Proper availability logic
@property
def available(self) -> bool:
    """Return if sensor is available."""
    return (
        self.coordinator.last_update_success
        and self._sensor_key in self.coordinator.data
        and self.coordinator.data[self._sensor_key] is not None
    )
```

### **Code Formatting**
```bash
# Use Black for formatting
black --line-length 88 blupow/

# Use isort for import sorting
isort blupow/

# Use flake8 for linting
flake8 blupow/ --max-line-length 88
```

---

## 🧪 **Testing Guidelines**

### **Before Making Changes**
```bash
# 1. Test current functionality
python3 scripts/comprehensive_integration_test.py

# 2. Run specific device tests
python3 scripts/direct_device_test.py

# 3. Validate integration health
python3 scripts/validate_integration.py
```

### **After Making Changes**
```bash
# 1. Test your specific changes
python3 scripts/quick_integration_test.py

# 2. Full regression testing
python3 scripts/comprehensive_integration_test.py

# 3. Deploy and test in Home Assistant
python3 deploy_production_stability.py
```

### **Writing Tests**
```python
# tests/test_sensor.py
import pytest
from unittest.mock import Mock
from custom_components.blupow.sensor import BluPowSensor

class TestBluPowSensor:
    """Test BluPow sensor functionality."""
    
    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator."""
        coordinator = Mock()
        coordinator.last_update_success = True
        coordinator.data = {
            "battery_voltage": 12.8,
            "battery_soc": 85,
        }
        return coordinator
    
    def test_battery_voltage_sensor(self, mock_coordinator):
        """Test battery voltage sensor."""
        sensor = BluPowSensor(
            coordinator=mock_coordinator,
            device_mac="D8:B6:73:BF:4F:75",
            sensor_key="battery_voltage",
        )
        
        assert sensor.state == 12.8
        assert sensor.unit_of_measurement == "V"
        assert sensor.available is True
```

---

## 📦 **Project Structure**

### **Core Gateway Files (`blupow_gateway/app`)**
```
app/
├── main.py              # Main application entrypoint, polling loop, MQTT client
├── utils.py             # Shared helper functions (e.g., CRC calculation)
└── devices/
    ├── base.py          # Abstract Base Class for all drivers
    ├── renogy_controller.py  # Example of a standard driver
    └── generic_modbus_device.py # The powerful configuration-driven driver
```

### **Home Assistant Component (`custom_components/blupow`)**
```
custom_components/blupow/
├── __init__.py          # Integration setup
├── manifest.json        # Integration metadata
├── config_flow.py       # Sets up connection to MQTT broker
└── sensor.py            # Defines the sensor entities in HA
```

### **Documentation**
```
docs/                        # Comprehensive documentation
├── TECHNICAL_ARCHITECTURE.md   # System architecture
├── DEVICE_DISCOVERY_GUIDE.md   # Device setup guide
├── IMPLEMENTATION_GUIDE.md     # Advanced configuration
└── troubleshooting/             # Problem solving guides
    └── TROUBLESHOOTING.md
```

---

## 🔍 **Understanding the Architecture**

### **Data Flow**
```
[BluPow Device] 
    ↓ (Bluetooth BLE)
[blupow_client.py] 
    ↓ (Raw device data)
[coordinator.py] 
    ↓ (Processed sensor data)
[sensor.py] 
    ↓ (Home Assistant entities)
[Home Assistant UI]
```

### **Key Components**

**1. BluPow Client (`blupow_client.py`)**
- Handles Bluetooth BLE communication
- Device-specific protocol implementation
- Raw data parsing and validation

**2. Data Coordinator (`coordinator.py`)**
- Manages update scheduling (30-second intervals)
- Device type detection and management
- Error handling and recovery
- Data transformation for Home Assistant

**3. Sensor Platform (`sensor.py`)**
- Creates Home Assistant sensor entities
- Maps device data to sensor values
- Handles availability and state management
- Provides proper units and device classes

**4. Constants (`const.py`)**
- Device-specific sensor definitions
- MAC address to device type mapping
- Sensor configurations (units, icons, classes)

---

## 🎯 **Common Development Tasks**

### **Adding a New Sensor**
```python
# 1. Add sensor definition to const.py
INVERTER_SENSORS = {
    # ... existing sensors ...
    "new_sensor_key": {
        "name": "New Sensor",
        "unit": "V",
        "icon": "mdi:flash",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# 2. Ensure blupow_client.py provides the data
async def get_data(self) -> dict:
    data = await self._get_raw_data()
    return {
        # ... existing mappings ...
        "new_sensor_key": data.get("new_sensor_raw_value"),
    }

# 3. Test the new sensor
python3 scripts/direct_device_test.py
```

### **Adding Device Support**
```python
# 1. Add device type mapping in const.py
DEVICE_TYPES = {
    # ... existing devices ...
    "AA:BB:CC:DD:EE:FF": {
        "name": "New Device Model",
        "model": "NEW-MODEL-123",
        "type": "new_device",
    },
}

# 2. Create sensor set for new device
NEW_DEVICE_SENSORS = {
    "sensor1": {"name": "Sensor 1", "unit": "V", ...},
    "sensor2": {"name": "Sensor 2", "unit": "A", ...},
}

# 3. Update get_device_sensors() function
def get_device_sensors(mac_address: str) -> dict:
    device_info = DEVICE_TYPES.get(mac_address.upper())
    if device_info["type"] == "new_device":
        return NEW_DEVICE_SENSORS
    # ... existing logic ...
```

### **Debugging Connection Issues**
```bash
# 1. Test basic connectivity
python3 scripts/direct_device_test.py

# 2. Check Bluetooth setup
python3 scripts/bluetooth_connection_fix.py

# 3. Monitor connection timing
python3 scripts/bluetooth_connection_timing_test.py

# 4. Enable debug logging
python3 scripts/enable_debug_logging.py
```

---

## 📋 **Pull Request Process**

### **1. Preparation**
- **Fork** the repository to your GitHub account
- **Create** a feature branch: `git checkout -b feature/your-feature-name`
- **Test** your changes thoroughly

### **2. Making Changes**
- **Write clear commit messages**: 
  ```
  feat: Add support for new sensor
  fix: Fix connection issue with device XYZ
  docs: Update installation guide
  ```

## 🎯 **Forcing UI Updates in Home Assistant**

**IMPORTANT**: Home Assistant aggressively caches the frontend (UI) components of integrations. If you make changes to the configuration flow (`config_flow.py`) or the UI text (`strings.json`), simply restarting Home Assistant is often **not enough** to see your changes.

To guarantee that Home Assistant discards its cache and loads your new UI code, you **must** increment the `version` number in the `custom_components/blupow/manifest.json` file.

**Example Workflow for UI Changes:**

1.  Make your changes in `config_flow.py` or `strings.json`.
2.  Open `custom_components/blupow/manifest.json`.
3.  Change `"version": "3.1.0"` to `"version": "3.1.1"`.
4.  Restart Home Assistant.

This version change signals to Home Assistant that the integration has been updated, forcing a complete reload of all its components.

### **3. Submit Pull Request**
- **Create** a pull request from your feature branch to the main repository
- **Provide** a clear title and description of your changes
- **Reference** any related issues or pull requests
- **Be** responsive to feedback and questions during the review process

Thank you for contributing to BluPow!

</rewritten_file>