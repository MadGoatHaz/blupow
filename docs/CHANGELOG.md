# 📝 BluPow Integration Changelog

All notable changes to the BluPow Home Assistant integration are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.1] - 2025-07-31 - 🐛 **Bug Fixes and Stability Improvements**

### 🔧 **Fixed**
- **Device Connection Timeouts**: Increased Bluetooth connection timeout from 20 seconds to 30 seconds in `BaseDevice.connect()` method
- **Device Discovery Reliability**: Improved discovery process with increased timeout (10s → 15s) and retry logic (up to 3 attempts) in `DeviceManager.discover_devices()`
- **Device Finding Timeout**: Increased timeout for finding devices by address from 10 seconds to 20 seconds in `BaseDevice.connect()` method
- **Connection Timing**: Added a small delay (1 second) before testing device connections to allow devices to be ready

## [4.0.0] - 2025-06-23 - 🏗️ **The Great Refactoring: A Foundation for the Future**

This is a developer-focused release that fundamentally refactors the BluPow Gateway for vastly improved stability, maintainability, and future extensibility. There are no user-facing feature changes, but the underlying improvements are critical for the project's long-term health.

### ✨ **Added**
- **`DeviceManager` Module**: A new, dedicated module (`device_manager.py`) now manages all device state, logic, polling loops, and BLE interactions.
- **`MqttHandler` Module**: A new, dedicated module (`mqtt_handler.py`) now isolates all MQTT connection and communication logic.
- **Stateful Device Configuration**: The gateway now saves its list of added devices to `blupow_gateway/config/devices.json` and automatically reloads them on restart.
- **BLE Discovery Caching**: The `DeviceManager` now caches the results of a BLE scan, making the `add_device` process faster and immune to race conditions.

### 🎯 **Changed**
- **Gateway Architecture**: The core logic previously in `blupow_gateway/app/main.py` has been completely refactored into the new `DeviceManager` and `MqttHandler` modules. `main.py` is now a simple application lifecycle orchestrator.
- **Device Driver API**: The abstract `BaseDevice` class has been updated. The primary data-gathering method is now `poll()`, which is responsible for the full connect-read-disconnect cycle.
- **Documentation Overhaul**: All project documentation (`README.md`, `IMPLEMENTATION_GUIDE.md`, `CONTRIBUTING.md`, etc.) has been rewritten from scratch to accurately reflect the new architecture and future roadmap.

### 🚫 **Removed**
- **Monolithic Logic**: All complex business logic has been removed from `main.py`.

## [3.0.0] - 2025-06-22 - 🎉 **The Container Revolution: Unmatched Stability**

### ✨ **Added**
- **Managed MQTT Broker**: New "Quick Install" option deploys a containerized Mosquitto broker (`blupow-mosquitto`) for a zero-configuration, self-contained system.
- **Docker-based Gateway**: The BluPow poller now runs as a standalone Docker container (`blupow-gateway`), completely isolated from Home Assistant.
- **Interactive Installer**: A new `install.sh` script that automates the entire setup process.
- **Dedicated Docker Network**: All components communicate over an isolated `blupow-net` network for reliability.
- **Diagnostic Tools**: Added `mqtt_viewer.py` to inspect live MQTT traffic.

### 🎯 **Changed**
- **Complete Architectural Overhaul**: Moved from a direct Home Assistant integration to a decoupled, three-container system (HA, Gateway, Broker). This is a fundamental shift in the project's design.
- **Installation Method**: The primary installation method is now the `install.sh` script, not HACS or manual file copying.
- **Configuration**: Device configuration is now managed in a dedicated host-mounted volume (`~/blupow_config/devices.json`).

### 🚫 **Removed**
- **Direct Bluetooth in HA**: The Home Assistant component no longer directly accesses Bluetooth hardware, eliminating a major source of instability.
- **HACS support is deprecated** as the primary installation method in favor of the Docker-based deployment.

### 🔧 **Fixed**  
- **Data Scaling Issues**: Corrected the Renogy Inverter data parsing to provide accurate sensor readings (e.g., Battery Voltage).
- **"Unknown" Sensor State**: The new architecture and data fix resolves the core issue of sensors failing to report data.

## [2.0.0] - 2025-01-21 - **🎉 MAJOR STABILITY RELEASE**

### ✨ **Added**
- **Device-Specific Intelligence**: Each device type now has tailored sensor sets
  - **Inverter (RIV1230RCH-SPS)**: 17 specialized sensors for AC power monitoring
  - **Controller (RNG-CTRL-RVR40)**: 20 specialized sensors for solar production
- **Smart Device Detection**: Automatic device type recognition based on MAC address
- **Unique Device Identity**: Each device now shows proper model and hardware info
- **Enhanced Entity Naming**: Clean, descriptive entity names (e.g., `sensor.blupow_inverter_battery_voltage`)
- **Comprehensive Tooling**: 20+ scripts for deployment, testing, and maintenance
- **Production-Ready Stability**: Rock-solid reliability with automatic fallbacks
- **HACS Compatibility**: Full HACS integration support
- **Rich Documentation**: Comprehensive guides and troubleshooting resources

### 🔧 **Fixed**  
- **❌ "Unavailable" Sensors**: Eliminated all false "unavailable" states
- **🔄 Duplicate Sensors**: Removed 69+ duplicate sensor entities causing conflicts
- **📊 Device Info Sharing**: Fixed all devices showing identical device information
- **⚡ Data Consistency**: Ensured device-specific data without cross-contamination
- **🔗 Connection Stability**: Improved Bluetooth connection reliability and recovery
- **📈 Sensor Availability Logic**: Simplified and bulletproofed availability detection

### 🎯 **Changed**
- **Complete Sensor Redesign**: Rebuilt `const.py` with device-specific sensor definitions
- **Streamlined Architecture**: Cleaned up legacy code and HANDOVER checkpoints  
- **Intelligent Coordinator**: Enhanced `coordinator.py` with device type detection
- **Simplified Sensor Logic**: Overhauled `sensor.py` for maximum reliability
- **Production Client**: Optimized `blupow_client.py` for stable device communication

### 🚫 **Removed**
- **Legacy Sensor Definitions**: Removed old, conflicting sensor configurations
- **Hardcoded Device Info**: Eliminated shared device information across devices
- **Complex Availability Logic**: Removed overly complicated availability checks
- **HANDOVER Checkpoints**: Cleaned up all development checkpoint comments
- **Duplicate Code Paths**: Streamlined codebase removing redundant logic

### 📊 **Device Support**
- **✅ RIV1230RCH-SPS Inverter** (`D8:B6:73:BF:4F:75`)
  - 17 sensors: AC I/O, battery management, load monitoring
- **✅ RNG-CTRL-RVR40 Controller** (`C4:D3:6A:66:7E:D4`)  
  - 20 sensors: Solar production, MPPT charging, energy statistics

---

## [1.5.0] - 2025-01-20 - **🔧 Stability Improvements**

### ✨ **Added**
- Advanced device discovery scripts
- Bluetooth connection timing optimization
- Multi-device management system
- Health monitoring tools

### 🔧 **Fixed**
- Intermittent connection drops
- Sensor update delays
- Memory leak in coordinator
- Bluetooth permission issues

### 🎯 **Changed**
- Enhanced error handling
- Improved logging detail
- Optimized update intervals
- Better connection retry logic

---

## [1.4.0] - 2025-01-19 - **📊 Enhanced Monitoring**

### ✨ **Added**
- Real-time power flow monitoring
- Energy production statistics
- Battery health indicators
- Temperature monitoring

### 🔧 **Fixed**
- Incorrect power calculations
- Missing energy sensors
- Temperature unit conversions
- Historical data gaps

---

## [1.3.0] - 2025-01-18 - **🎨 UI/UX Improvements**

### ✨ **Added**
- Beautiful sensor icons
- Proper device classes
- Energy dashboard integration
- Custom sensor attributes

### 🎯 **Changed**
- Improved entity naming conventions
- Enhanced sensor descriptions
- Better unit definitions
- Optimized dashboard layouts

---

## [1.2.0] - 2025-01-17 - **⚡ Performance Boost**

### ✨ **Added**
- Async data processing
- Connection pooling
- Smart retry mechanisms
- Performance metrics

### 🔧 **Fixed**
- Slow sensor updates
- High CPU usage
- Memory consumption
- Connection timeouts

### 🎯 **Changed**
- Optimized data polling
- Reduced Bluetooth overhead
- Improved coordinator efficiency
- Enhanced caching strategies

---

## [1.1.0] - 2025-01-16 - **🛠️ Feature Expansion**

### ✨ **Added**
- Multiple device support
- Advanced configuration options
- Diagnostic tools
- Backup/restore functionality

### 🔧 **Fixed**
- Single device limitation
- Configuration validation
- Error reporting
- State persistence

---

## [1.0.0] - 2025-01-15 - **🎉 Initial Release**

### ✨ **Added**
- Basic BluPow device integration
- Core sensor monitoring
- Bluetooth BLE communication
- Home Assistant integration
- Configuration flow UI
- Basic error handling

### 📊 **Device Support**
- **✅ RIV1230RCH-SPS Inverter**: Basic monitoring
- **🔄 Limited Multi-Device**: Experimental support

### 🎯 **Features**
- Real-time sensor data
- 30-second update intervals
- Basic device information
- Manual configuration required

---

## 🔮 **Upcoming Features (Roadmap)**

### **Version 2.1.0 - Enhanced Energy Management**
- **⚡ Smart Load Control**: Automatic load balancing based on battery SOC
- **📈 Advanced Analytics**: Historical performance tracking and trends
- **🔔 Intelligent Notifications**: Predictive alerts and maintenance reminders
- **🌡️ Environmental Monitoring**: Enhanced temperature and weather integration

### **Version 2.2.0 - Ecosystem Integration**
- **🏠 Matter/Thread Support**: Next-gen smart home protocol integration
- **☁️ Cloud Synchronization**: Optional cloud backup and remote monitoring
- **📱 Mobile Companion**: Dedicated mobile app integration
- **🤖 AI Optimization**: Machine learning for energy efficiency recommendations

### **Version 3.0.0 - Professional Features**
- **🏭 Commercial Scale**: Support for larger installations and multiple sites
- **📊 Professional Dashboards**: Advanced monitoring and reporting tools
- **🔌 Grid Integration**: Smart grid interaction and sell-back optimization
- **🔧 Remote Management**: Professional installation and maintenance tools

---

## 🐛 **Known Issues**

### **Minor Issues**
- **Bluetooth Range**: Optimal performance within 10 meters of device
- **Initial Connection**: First connection may take 30-60 seconds
- **High Update Rates**: Updates faster than 15 seconds may impact stability

### **Workarounds Available**
- **Connection Issues**: Use `scripts/bluetooth_connection_fix.py` 
- **Sensor Problems**: Run `deploy_production_stability.py`
- **Duplicate Entities**: Execute `cleanup_duplicate_sensors.py`

---

## 📋 **Migration Guide**

### **From v1.x to v2.0**
1. **Backup Configuration**: Export current settings
2. **Remove Old Integration**: Delete via Home Assistant UI
3. **Clean Install**: Follow new installation instructions
4. **Restore Settings**: Re-add devices with new configuration

### **Breaking Changes in v2.0**
- **Entity Names**: All sensor entities renamed for consistency
- **Device Info**: Device identification completely rebuilt
- **Configuration**: New device-specific configuration requirements

---

## 🤝 **Contributors**

### **Core Team**
- **@madgoat** - Project lead, architecture, and implementation
- **@contributors** - Community contributions and testing

### **Special Thanks**
- **Beta Testers** - Invaluable feedback during development
- **Home Assistant Community** - Support and feature requests
- **Renogy** - Excellent hardware that makes this possible

---

## 📞 **Support & Feedback**

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/MadGoatHaz/blupow/discussions)
- **💬 Community Support**: [Home Assistant Forum](https://community.home-assistant.io)
- **📧 Direct Contact**: ghazlett@gmail.com
- **💖 Support Development**: [GitHub Sponsors](https://github.com/sponsors/MadGoatHaz) | [PayPal](https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD)

---

**🚀 Keep up with the latest updates and join our growing community of solar enthusiasts!** 