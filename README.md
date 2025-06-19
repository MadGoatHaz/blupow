# 🔋 BluPow: Universal Renogy Bluetooth Integration

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Compatible-blue.svg)](https://www.home-assistant.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](FINAL_SUCCESS_SUMMARY.md)

> **Enterprise-grade Home Assistant integration for Renogy solar charge controllers with universal compatibility and intelligent environment detection.**

## 🎯 What BluPow Has Become

BluPow has evolved from a basic BLE client into a **sophisticated, environment-aware integration** that embodies the **"assume nothing, detect everything"** philosophy. It automatically detects and adapts to any Home Assistant installation type, platform, and environment.

### 🏆 Key Achievements

- ✅ **Universal Compatibility**: Works seamlessly across Docker, HassIO, Core, and Manual installations
- ✅ **Multi-Platform Support**: Linux (BlueZ), Windows (WinRT), macOS (CoreBluetooth)
- ✅ **Environment Intelligence**: Automatic detection and adaptation to any environment
- ✅ **Enterprise Reliability**: Robust error handling with comprehensive retry logic
- ✅ **Modern Architecture**: Future-proof implementation using latest APIs
- ✅ **Zero Configuration**: Intelligent defaults with automatic optimization

## 🚀 Features

### Core Functionality
- **Real-time monitoring** of Renogy solar charge controllers via Bluetooth
- **8 comprehensive sensors**: Battery voltage/current/SOC/temperature, Solar voltage/current/power, Model info
- **Automatic device discovery** with intelligent pairing
- **Live data updates** with configurable refresh intervals

### Advanced Capabilities
- 🔍 **Proactive Environment Detection**: Automatically detects platform, installation type, and BLE backend
- 🔄 **Intelligent Retry Logic**: Progressive delays with environment-aware timeouts
- 🎯 **Device Type Recognition**: ESP32 vs DEFAULT device handling with optimized connection strategies
- 📊 **Comprehensive Logging**: DEBUG-level logging for troubleshooting and monitoring
- 🛡️ **Graceful Error Handling**: Robust connection management with automatic recovery

## ❤️ Support This Project

If you find BluPow useful, please consider supporting its development. Your contributions help cover the costs of hardware and caffeinated beverages!

- **[Sponsor on GitHub](https://github.com/sponsors/MadGoatHaz)**
- **[Send a tip via PayPal](https://www.paypal.com/paypalme/ghazlett)**

### Universal Compatibility Matrix

| Installation Type | Platform | BLE Backend | Status |
|------------------|----------|-------------|---------|
| Home Assistant Docker | Linux | BlueZ | ✅ Fully Supported |
| Home Assistant OS (HassIO) | Linux | BlueZ | ✅ Fully Supported |
| Home Assistant Core | Linux | BlueZ | ✅ Fully Supported |
| Home Assistant Core | Windows | WinRT | ✅ Fully Supported |
| Home Assistant Core | macOS | CoreBluetooth | ✅ Fully Supported |
| Manual Installation | Any | Auto-detect | ✅ Fully Supported |

## 📦 Installation

### Method 1: Automated Deployment (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/blupow.git
cd blupow

# Run the intelligent deployment script
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:
- 🔍 **Auto-detect your Home Assistant installation** (Docker/HassIO/Core/Manual)
- 📁 **Find the correct paths** automatically
- 💾 **Create intelligent backups** with conflict-free naming
- 🔐 **Handle permissions** appropriately for your environment
- 🔄 **Restart Home Assistant** with confirmation

### Method 2: Manual Installation
```bash
# Copy to custom_components directory
cp -r blupow /path/to/homeassistant/config/custom_components/

# Restart Home Assistant
# Method varies by installation type - the deploy script handles this automatically
```

### Method 3: HACS (Coming Soon)
BluPow will be available through HACS for even easier installation and updates.

## ⚙️ Configuration

### Automatic Setup (Zero Configuration)
1. Navigate to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **"BluPow"**
4. Select your Renogy device from the discovered list
5. Click **Submit** - BluPow handles the rest automatically!

### Advanced Configuration (Optional)
```yaml
# configuration.yaml (optional customization)
blupow:
  update_interval: 30  # seconds (default: 30)
  
# Enable debug logging (optional)
logger:
  logs:
    custom_components.blupow: debug
```

## 📊 Sensors & Data

BluPow provides comprehensive monitoring through 8 intelligent sensors:

### Battery Monitoring
- **Battery Voltage** (V) - Real-time battery voltage with precision
- **Battery Current** (A) - Charging/discharging current flow
- **Battery SOC** (%) - State of charge with intelligent calculation
- **Battery Temperature** (°C) - Thermal monitoring for safety

### Solar Panel Monitoring
- **Solar Voltage** (V) - PV panel voltage output
- **Solar Current** (A) - Current generation from panels
- **Solar Power** (W) - Calculated power generation

### System Information
- **Model Number** - Device identification and firmware info

### Intelligent Data Handling
- 🔄 **Automatic unit conversion** and validation
- 📈 **Historical data retention** through Home Assistant
- 🎯 **Smart error detection** with meaningful status reporting
- 📊 **Integration with Energy Dashboard** for comprehensive monitoring

## 🏗️ Architecture & Technical Excellence

### Environment Detection System
```python
Environment detected: Platform: Linux, Python: (3, 13), Docker: False, HassIO: False, BLE: BlueZ
```

BluPow automatically detects:
- **Platform**: Linux/Windows/macOS with specific optimizations
- **Installation Type**: Docker/HassIO/Core/Manual with appropriate handling
- **BLE Backend**: BlueZ/WinRT/CoreBluetooth with optimal configuration
- **Container Environment**: Docker networking and permission considerations
- **Python Version**: Compatibility verification and feature adaptation

### Intelligent Connection Management
- **Progressive Retry Logic**: 3 attempts with exponential backoff
- **Environment-Aware Timeouts**: 20-30s scaling based on detected environment
- **Device-Specific Strategies**: ESP32 devices get 5+3*attempt second delays
- **Graceful Degradation**: Meaningful error messages with automatic recovery

### Modern API Implementation
```python
# Modern service discovery with backward compatibility
services = client.services if hasattr(client, 'services') else await client.get_services()
```

- **Future-Proof Design**: Uses latest Bleak APIs with fallbacks
- **No Deprecation Warnings**: Clean implementation without FutureWarnings
- **Comprehensive Error Handling**: Every operation wrapped in intelligent try-catch
- **Resource Management**: Proper connection lifecycle management

## 🔧 Troubleshooting & Support

### Common Issues & Solutions

#### Device Not Found
```log
No backend with an available connection slot that can reach address
```
**Solution**: Ensure your Renogy device is:
- Powered on and discoverable
- Not connected to another device/app
- Within Bluetooth range (typically 10 meters)

#### Permission Issues (Linux)
```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER
# Restart required
```

#### Container Networking (Docker)
BluPow automatically detects Docker environments and applies appropriate networking configurations.

### Debug Logging
Enable comprehensive logging for troubleshooting:
```yaml
logger:
  logs:
    custom_components.blupow: debug
```

### Getting Help
- 📖 Check the [HANDOVER.md](HANDOVER.md) for detailed technical information
- 🐛 Review [BUGFIXES_SUMMARY.md](BUGFIXES_SUMMARY.md) for resolved issues
- 💡 See [PROJECT_IDEOLOGY.md](PROJECT_IDEOLOGY.md) for design philosophy
- 🎯 Read [FINAL_SUCCESS_SUMMARY.md](FINAL_SUCCESS_SUMMARY.md) for achievement details

## 🎯 Project Philosophy

### "Assume Nothing, Detect Everything"
BluPow embodies a core philosophy of **proactive environment detection** rather than making assumptions:

1. **Environment Intelligence**: Automatically detects and adapts to any setup
2. **Universal Compatibility**: Works across all platforms and installation types
3. **Graceful Degradation**: Handles errors intelligently with meaningful feedback
4. **Future-Proof Architecture**: Designed to adapt to changes and updates
5. **Zero Configuration**: Intelligent defaults with automatic optimization

### Enterprise-Grade Reliability
- **Comprehensive Error Handling**: Every failure mode anticipated and handled
- **Intelligent Retry Logic**: Progressive strategies based on error type and environment
- **Detailed Logging**: DEBUG-level visibility for troubleshooting and monitoring
- **Automatic Recovery**: Self-healing connections with minimal user intervention

## 🚀 Performance & Efficiency

### Optimized Connection Strategies
- **Environment-Specific Timeouts**: 20s-30s scaling based on detected platform
- **Device-Type Awareness**: ESP32 vs DEFAULT device handling
- **Intelligent Delays**: Progressive timing strategies for optimal reliability
- **Resource Efficiency**: Minimal CPU and memory footprint

### Monitoring & Metrics
```log
Connection attempt 1/3 to C4:D3:6A:66:7E:D4 (device type: DEFAULT)
Waiting 3s before connection attempt (environment: Linux)
Finished fetching BluPow data in 11.007 seconds (success: True)
```

## 🔮 Future Roadmap

### Planned Enhancements
- 🏪 **HACS Integration**: Official HACS repository for easy installation
- 📱 **Mobile Notifications**: Critical alert system for battery/solar issues
- 📊 **Advanced Analytics**: Historical trend analysis and predictive insights
- 🔄 **Multi-Device Support**: Connect and monitor multiple Renogy controllers
- 🌐 **Cloud Integration**: Optional cloud backup and remote monitoring
- 🤖 **AI-Powered Insights**: Intelligent recommendations for optimal performance

### Continuous Improvement
- **Regular Updates**: Ongoing compatibility and feature enhancements
- **Community Feedback**: User-driven improvements and feature requests
- **Security Updates**: Proactive security monitoring and patches
- **Performance Optimization**: Continuous efficiency improvements

## 🤝 Contributing

We welcome contributions to make BluPow even better!

### Development Setup
```bash
git clone https://github.com/yourusername/blupow.git
cd blupow

# Set up development environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Contribution Guidelines
- 🐛 **Bug Reports**: Use the issue tracker with detailed information
- 💡 **Feature Requests**: Describe the use case and expected behavior
- 🔧 **Pull Requests**: Follow the existing code style and include tests
- 📖 **Documentation**: Help improve documentation and examples

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Home Assistant Community**: For the amazing platform and ecosystem
- **Bleak Library**: For excellent cross-platform Bluetooth Low Energy support
- **Renogy**: For creating innovative solar charge controllers
- **Open Source Community**: For inspiration and collaborative development

---

## 🎉 Success Story

BluPow represents a complete transformation from a basic BLE client to an **enterprise-grade, environment-aware integration**. Through the implementation of the **"assume nothing, detect everything"** philosophy, BluPow now provides:

- ✅ **Universal compatibility** across all Home Assistant installations
- ✅ **Intelligent environment detection** and automatic adaptation
- ✅ **Robust error handling** with comprehensive retry logic
- ✅ **Modern architecture** using future-proof APIs
- ✅ **Production-ready reliability** with enterprise-grade logging

**Transform your solar monitoring experience with BluPow!** 🌞⚡🔋

---

*Made with ❤️ for the Home Assistant and Solar Energy communities*
