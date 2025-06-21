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

### **Core Integration Files**
```
blupow/
├── __init__.py              # Integration initialization
├── manifest.json            # Integration metadata
├── config_flow.py           # Configuration UI
├── coordinator.py           # Data coordination & device communication
├── sensor.py                # Home Assistant sensor entities
├── blupow_client.py         # Bluetooth device client
├── const.py                 # Constants, sensor definitions
├── strings.json             # UI strings
└── translations/            # Multi-language support
    └── en.json
```

### **Development & Tools**
```
scripts/                     # Development and deployment tools
├── quick_integration_test.py    # Fast testing
├── comprehensive_integration_test.py  # Full test suite
├── deploy_production_fix.py     # Production deployment
├── bluetooth_connection_fix.py  # Connection debugging
└── validate_integration.py      # Integration validation
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
  feat: add support for new device model XYZ
  
  - Add device type detection for MAC pattern AA:BB:CC:*
  - Create sensor definitions for 15 new sensors
  - Update documentation with device-specific setup
  
  Fixes #123
  ```

### **3. Testing Checklist**
- [ ] **Unit tests pass**: All existing functionality works
- [ ] **Integration tests pass**: End-to-end testing successful  
- [ ] **Device testing**: Tested with actual hardware (if applicable)
- [ ] **Documentation updated**: README, guides updated as needed
- [ ] **No breaking changes**: Existing setups continue to work

### **4. Pull Request**
- **Create PR** with descriptive title and detailed description
- **Reference issues**: Link to related GitHub issues
- **Provide context**: Explain why the change is needed
- **Include screenshots**: Show UI changes if applicable

### **5. Review Process**
- **Automated checks**: CI/CD pipeline must pass
- **Code review**: Core maintainers will review
- **Testing**: Community testing and feedback
- **Approval**: Final approval from project maintainers

---

## 🐛 **Reporting Bugs**

### **Before Reporting**
1. **Search existing issues**: Check if bug already reported
2. **Test with latest version**: Ensure you're using current release
3. **Run diagnostics**: Use provided diagnostic tools
4. **Gather information**: Collect logs and system info

### **Bug Report Template**
```markdown
## 🐛 Bug Report

### **Description**
Clear description of what the bug is.

### **Expected Behavior**
What you expected to happen.

### **Actual Behavior**
What actually happened.

### **Environment**
- **Home Assistant Version**: 2024.x.x
- **BluPow Integration Version**: x.x.x  
- **Device Model**: RIV1230RCH-SPS
- **Device MAC**: D8:B6:73:BF:4F:75
- **Installation Method**: HACS / Manual

### **Reproduction Steps**
1. Go to '...'
2. Click on '...'
3. See error

### **Logs**
```
[Paste relevant log entries here]
```

### **Additional Context**
Screenshots, configuration files, etc.
```

---

## 💡 **Feature Requests**

### **Before Requesting**
- **Check existing requests**: Look for similar feature requests
- **Consider use case**: Is this beneficial to the community?
- **Think about implementation**: How complex would this be?

### **Feature Request Template**
```markdown
## ✨ Feature Request

### **Problem/Use Case**
Description of the problem this feature would solve.

### **Proposed Solution**
Your idea for how to solve it.

### **Alternative Solutions**
Other approaches you've considered.

### **Additional Context**
Screenshots, mockups, examples from other projects.

### **Implementation Ideas**
Technical thoughts on implementation (optional).
```

---

## 🏆 **Recognition**

### **Contributor Levels**
- **🌟 Contributors**: Code contributions, bug reports, documentation
- **⭐ Regular Contributors**: Multiple contributions, community help
- **🎖️ Core Contributors**: Major features, architectural decisions
- **👑 Maintainers**: Project leadership, release management

### **How We Recognize Contributors**
- **GitHub**: Contributors listed in repository
- **Documentation**: Credit in README and docs
- **Releases**: Recognition in changelog
- **Community**: Shout-outs in discussions and forums

---

## 📞 **Getting Help**

### **Development Questions**
- **GitHub Discussions**: Best for general questions
- **Discord**: Real-time chat with community
- **Issues**: For specific problems or bugs

### **Architecture Questions**  
- **Read the docs**: Start with [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)
- **Code comments**: Inline documentation explains complex logic
- **Ask maintainers**: Tag @MadGoatHaz in issues/PRs
- **Email support**: ghazlett@gmail.com for complex technical questions

### **Community Support**
- **Home Assistant Forum**: General Home Assistant integration questions
- **Reddit**: r/homeassistant community discussions
- **Discord**: Home Assistant development channels

---

## 📜 **Code of Conduct**

We are committed to providing a welcoming and inspiring community for all. Please:

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together constructively
- **Be patient**: Help newcomers learn and grow
- **Be inclusive**: Welcome people of all backgrounds and skill levels

Unacceptable behavior includes harassment, discrimination, or any form of disrespectful conduct. Report issues to project maintainers.

---

## 🙏 **Thank You!**

Your contributions make this project better for everyone. Whether you're:
- 🐛 **Fixing bugs**
- ✨ **Adding features** 
- 📚 **Improving documentation**
- 🧪 **Writing tests**
- 💬 **Helping other users**

...every contribution matters and is appreciated! 

**Welcome to the BluPow community! 🎉**

---

## 📞 **Contact & Support**

### **Project Maintainer**
- **Developer**: Garrett Hazlett ([@MadGoatHaz](https://github.com/MadGoatHaz))
- **Email**: ghazlett@gmail.com
- **GitHub**: [MadGoatHaz/blupow](https://github.com/MadGoatHaz/blupow)

### **Support Development**  
- **[GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)** - Monthly sponsorship
- **[PayPal Donation](https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD)** - One-time donation

### **Get Help**
- **Issues**: [GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MadGoatHaz/blupow/discussions)
- **Email**: ghazlett@gmail.com 