# BluPow - Renogy Bluetooth Power Monitoring Integration

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

**The ultimate automated Home Assistant power monitoring solution** - Seamlessly integrate Renogy Bluetooth devices with your Home Assistant Energy Dashboard.

## 🎯 Vision: One-Click Power Monitoring

Transform your solar/battery setup monitoring from manual configuration to **automated discovery and setup**:

1. **Install from HACS** → 2. **Answer 2-3 questions** → 3. **Complete Energy Dashboard**

## 📁 Project Organization

This project is now properly organized for maintainability and ease of use:

```
📂 docs/           # All documentation
📂 scripts/        # Setup and deployment scripts  
📂 tests/          # Testing and diagnostic tools
📂 info/           # Reference materials
📂 results/        # Test results and logs
```

**👀 See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete organization details.**

## 🚀 Quick Start

### 1. Container Setup (Required First)
```bash
# Fix Docker Bluetooth access (one-time setup)
chmod +x scripts/setup_container_bluetooth.sh
sudo ./scripts/setup_container_bluetooth.sh
```

### 2. Deploy Integration
```bash
# Deploy to Home Assistant
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 3. Test Your Device
```bash
# Run comprehensive diagnostics
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/tests/diagnostics/blupow_testing_suite.py
```

## 📖 Documentation

### 🆘 Need Help?
- **[Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING.md)** - Solve common issues
- **[Container Setup Guide](docs/guides/CONTAINER_SETUP_GUIDE.md)** - Fix Docker Bluetooth access

### 📚 User Guides  
- **[Future Vision](docs/guides/FUTURE_VISION.md)** - Automated HACS integration roadmap
- **[Energy Dashboard Plan](docs/guides/ENERGY_DASHBOARD_PLAN.md)** - Energy monitoring setup

### 🔧 Developer Resources
- **[Testing Guide](docs/development/TESTING_GUIDE.md)** - Testing procedures
- **[Context Guide](docs/development/CONTEXT_GUIDE.md)** - Development background
- **[Session Summary](docs/development/SESSION_SUMMARY.md)** - Recent development progress

## 🧪 Testing & Diagnostics

### Quick Device Test
```bash
# Quick connectivity test
tests/integration/quick_test.py
```

### Comprehensive Testing
```bash
# Full diagnostic suite
tests/diagnostics/blupow_testing_suite.py
```

### Specialized Tests
- **Device Discovery**: `tests/diagnostics/device_discovery_system.py`
- **Wake-up Testing**: `tests/diagnostics/device_wake_system.py`
- **Connection Testing**: `tests/integration/connection_test.py`
- **Proxy Testing**: `tests/integration/proxy_test.py`

## 🎯 Current Status

✅ **Working**: Core integration, device discovery, sensor creation  
⚠️ **Blocker**: Container Bluetooth access (AppArmor restrictions)  
🚀 **Next**: Automated HACS integration with setup wizard

**See [CURRENT_STATUS.md](docs/CURRENT_STATUS.md) for detailed status.**

## 🔧 Supported Devices

### Currently Supported
- **Renogy RNG-CTRL-RVR40** (Rover 40A Charge Controller)
- **BTRIC134000035** (Bluetooth module)

### Future Support (Planned)
- Additional Renogy charge controllers
- Renogy inverters and battery monitors  
- Shelly power monitoring devices
- Victron Energy devices
- Tesla Powerwall integration

## 🏗️ Architecture

### Core Integration Files
- `blupow_client.py` - Bluetooth communication
- `coordinator.py` - Data management
- `sensor.py` - Home Assistant sensors
- `config_flow.py` - Setup wizard

### Container Security
The integration includes comprehensive solutions for Docker Bluetooth access issues, including custom AppArmor profiles and automated setup scripts.

## 🤝 Contributing

### Development Setup
1. **Read**: `docs/development/CONTEXT_GUIDE.md`
2. **Test**: Use tools in `tests/` directory
3. **Document**: Update appropriate `docs/` files

### Adding Features
- Tests → `tests/` subdirectories
- Documentation → `docs/` subdirectories  
- Reference materials → `info/`

## 📋 Requirements

- **Home Assistant** 2023.8+
- **Python** 3.8+
- **Bluetooth** adapter with BlueZ
- **Docker** with Bluetooth access
- **Renogy device** with Bluetooth enabled

## 🔒 Security

This integration includes comprehensive security considerations:
- Custom AppArmor profiles for container isolation
- Minimal privilege Docker configurations
- Secure Bluetooth communication protocols

**See [AppArmor Info](info/AppArmor%20Info.txt) for detailed security reference.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Home Assistant community for integration framework
- Renogy for Bluetooth protocol documentation
- cyrils/renogy-bt for protocol insights
- AppArmor project for container security

---

**🎯 Goal**: Make renewable energy monitoring as simple as clicking "Install" in HACS!
