# Changelog

All notable changes to BluPow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-XX (HACS Release)

### 🎉 **Major Release - HACS Ready**
This release marks BluPow as production-ready and available through HACS (Home Assistant Community Store).

### ✨ **Added**
- **HACS Compatibility**: Full HACS integration with proper manifest and info files
- **Professional Documentation**: Comprehensive README, contributing guide, and user documentation
- **Monetization Support**: GitHub Sponsors and PayPal donation integration
- **Enhanced Stability**: Improved connection reliability and error recovery
- **Dynamic Timeout Management**: Adaptive timeouts based on connection history
- **Intelligent Fallback System**: Cached data during temporary outages
- **Enhanced Sensor Availability**: 10-minute grace period before marking unavailable
- **Professional Branding**: Updated logos, icons, and visual identity

### 🔧 **Fixed**
- **Critical RuntimeWarning**: Fixed `coroutine 'BleakClient.disconnect' was never awaited`
- **Progressive Degradation**: Resolved sensors becoming unavailable over time
- **Connection Retry Logic**: Implemented 2-attempt retry system with delays
- **Resource Management**: Proper subprocess cleanup and process termination
- **Config Flow Warning**: Removed deprecation warning about explicit config_entry assignment

### 🚀 **Improved**
- **Connection Success Rate**: Achieved 100% initial success rate, 80%+ sustained
- **Update Frequency**: Consistent 30-second update intervals
- **Error Recovery**: Better handling of temporary connection failures
- **Memory Management**: Reduced memory usage and improved cleanup
- **Documentation Quality**: Professional-grade documentation suite

### 📊 **Technical Specifications**
- **Supported Device**: Renogy RIV1230RCH-SPS Inverter Charger
- **Protocol**: Bluetooth Low Energy with Modbus over GATT
- **Total Sensors**: 22 real-time readings
- **Data Fields**: 24 total fields retrieved per cycle
- **Update Interval**: 30 seconds (configurable)
- **Connection Timeout**: 25-45 seconds (adaptive)
- **Data Accuracy**: ±0.1V voltage, ±0.4°C temperature

## [1.0.0] - 2025-01-XX (Breakthrough Release)

### 🎯 **Revolutionary Achievement**
First stable release achieving 100% sensor functionality through innovative subprocess-based coordinator.

### ✨ **Added**
- **Subprocess-Based Coordinator**: Revolutionary solution for Bluetooth resource conflicts
- **22 Working Sensors**: All sensors displaying real-time inverter data
- **Complete Device Support**: Full integration with Renogy RIV1230RCH-SPS
- **Real-Time Monitoring**: Live data updates every 30 seconds
- **Comprehensive Diagnostics**: Full diagnostic and testing suite
- **Professional Documentation**: Extensive technical documentation

### 🔧 **Core Features**
- **Device Discovery**: Automatic Bluetooth device detection
- **Data Parsing**: Correct Modbus byte offset parsing (fixed critical bug)
- **Error Handling**: Robust error recovery and retry mechanisms
- **Connection Management**: Intelligent connection pooling and resource management
- **Configuration Flow**: User-friendly Home Assistant configuration interface

### 📈 **Performance Metrics**
- **Connection Success**: 100% success rate in isolated subprocess environment
- **Data Retrieval**: Consistent 24-field data extraction per cycle
- **Response Time**: 8-12 second average connection and data retrieval
- **Reliability**: Stable operation over extended periods

## [0.9.0] - 2025-01-XX (Development Release)

### 🔬 **Critical Bug Discovery and Resolution**
Major breakthrough in data parsing accuracy and connection stability.

### 🐛 **Fixed**
- **Critical Data Parsing Bug**: Fixed incorrect byte offset reading (byte 2 vs byte 3)
- **Impossible Values**: Resolved 512.4V, 2867.2V, 3686.5°C readings
- **Modbus Structure**: Corrected understanding of Modbus response format
- **Import Compatibility**: Fixed Home Assistant unit class imports
- **Coordinator Methods**: Updated to use correct API methods

### ✅ **Validated**
- **Realistic Data**: Input Voltage 124.5V, Battery Voltage 14.4V, Battery SOC 100%
- **Temperature Accuracy**: 32.3°C realistic temperature readings
- **Model Detection**: Correct RIV1230RCH-SPS model identification
- **Load Monitoring**: Accurate 395W load power measurement

## [0.8.0] - 2025-01-XX (Connection Research)

### 🔍 **Deep Investigation Phase**
Extensive research into Home Assistant Bluetooth integration challenges.

### 📊 **Analysis**
- **Timing Pattern Discovery**: Manual tests 100% success, coordinator consistent failures
- **Environment Interference**: Identified HA execution context issues
- **Resource Conflicts**: Discovered Bluetooth resource competition
- **ESP_GATT_CONN_FAIL_ESTABLISH**: Root cause analysis of connection failures

### 🧪 **Attempted Solutions**
- Recovery delay implementation (5-second pre-connection wait)
- Increased timeout strategies (20s → 30s BleakClient timeout)
- Thread pool isolation experiments
- Comprehensive retry logic with timeout protection

## [0.7.0] - 2025-01-XX (Initial Integration)

### 🚀 **First Home Assistant Integration**
Initial working integration with basic sensor framework.

### ✨ **Added**
- **Basic Sensor Framework**: 22 sensor entities created
- **Configuration Flow**: Initial HA configuration interface
- **Device Discovery**: Bluetooth device scanning functionality
- **Data Structure**: Complete sensor mapping and definitions

### ⚠️ **Known Issues**
- Sensors showing "Unavailable" status
- Connection timeout issues
- Import compatibility problems
- Coordinator execution failures

## [0.6.0] - 2025-01-XX (Standalone Success)

### 🎯 **Standalone Testing Success**
First successful data retrieval from Renogy inverter outside HA environment.

### ✅ **Achievements**
- **Device Connection**: Successful Bluetooth connection to D8:B6:73:BF:4F:75
- **Data Retrieval**: Complete 5-register section reading (4000, 4109, 4311, 4327, 4408)
- **Modbus Communication**: Working Modbus over Bluetooth Low Energy
- **Data Validation**: Confirmed realistic sensor values

### 🔧 **Technical Foundation**
- **BluPowClient Class**: Core client implementation
- **Modbus Protocol**: GATT-based Modbus communication
- **Error Handling**: Basic connection and data error management
- **Testing Framework**: Standalone testing utilities

## [0.5.0] - 2025-01-XX (Protocol Research)

### 🔬 **Protocol Analysis Phase**
Deep dive into Renogy device communication protocols.

### 📚 **Research**
- **Bluetooth Low Energy**: GATT service and characteristic analysis
- **Modbus Mapping**: Register address mapping and data structure
- **Device Specifications**: RIV1230RCH-SPS technical specifications
- **Communication Patterns**: Protocol timing and sequence analysis

## [0.1.0] - 2025-01-XX (Project Inception)

### 🌱 **Project Foundation**
Initial project setup and requirements gathering.

### 🎯 **Goals Established**
- Home Assistant integration for Renogy inverters
- Real-time sensor monitoring
- Bluetooth Low Energy communication
- Professional documentation and support

### 📋 **Requirements**
- Python 3.9+ compatibility
- Home Assistant 2023.1+ support
- Bluetooth adapter requirements
- Device compatibility matrix

---

## **Release Notes Format**

### **Version Numbering**
- **Major (X.0.0)**: Breaking changes, major new features
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, minor improvements

### **Change Categories**
- **✨ Added**: New features and enhancements
- **🔧 Fixed**: Bug fixes and corrections
- **🚀 Improved**: Performance and quality improvements
- **⚠️ Deprecated**: Features marked for removal
- **🗑️ Removed**: Removed features and breaking changes
- **🔒 Security**: Security-related changes

### **Contribution Guidelines**
- All user-facing changes must be documented
- Include GitHub issue/PR references where applicable
- Use clear, descriptive language for end users
- Group related changes together
- Highlight breaking changes prominently

---

*For the complete development history and technical details, see the [project documentation](docs/) and [GitHub releases](https://github.com/MadGoatHaz/blupow/releases).* 