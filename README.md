# 🔋 BluPow: Universal Renogy Bluetooth Integration

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Compatible-blue.svg)](https://www.home-assistant.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Status-Configured-yellow.svg)](#)

> **Enterprise-grade Home Assistant integration for Renogy solar charge controllers with universal compatibility and intelligent environment detection.**

## 🎯 **PROJECT STATUS: DEVICE NOT FOUND** ❌

**Integration**: ✅ **CONFIGURED**  
**Connection**: ❌ **BLOCKED** (Device cannot be discovered)
**Last Updated**: June 19, 2025

---

## 📋 Quick Summary

This BluPow integration for Home Assistant is **correctly configured but currently non-operational**.

- ✅ The integration code is stable and includes 18 comprehensive sensors.
- ✅ All necessary configuration and error handling is in place.
- ❌ **The integration is blocked because the target Renogy device (`D8:B6:73:BF:4F:75`) cannot be found during Bluetooth scans.**

The immediate priority is to resolve the Bluetooth discovery issue.

---

## 🚨 Troubleshooting

If you are experiencing issues, please start with our comprehensive troubleshooting guide. It contains steps to diagnose and solve the most common problems.

**➡️ Read the Troubleshooting Guide: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)**

The first step in the guide is to run the diagnostic tool.

**Note**: This script must be run in an environment where the Home Assistant packages are installed. If you are using Home Assistant OS or a supervised installation, use the "Terminal & SSH" add-on.

```bash
python3 blupow_testing_suite.py
```
Select option `6` for **Current Device Diagnostics**.

---

## 🧪 Testing

This project includes a powerful suite of testing and diagnostic tools to help you identify and resolve issues.

| Script                      | Purpose                                                                        |
| --------------------------- | ------------------------------------------------------------------------------ |
| `blupow_testing_suite.py`   | **(Recommended)** A unified suite for discovery, diagnostics, and wake-up tests. |
| `connection_test.py`        | Performs a comprehensive connection test to a known device.                    |
| `proxy_test.py`             | Analyzes connectivity through your ESPHome Bluetooth proxies.                  |
| `quick_test.py`             | A very fast, simple check to see if the device is advertising.                 |
| `simple_test.py`            | A basic script for device discovery.                                           |


### Quick Start Commands

#### Deploy Integration
```bash
git clone https://github.com/your-repo/blupow.git
cd blupow
./deploy.sh  # Auto-detects environment and deploys
```

#### Diagnose Connection Issues
```bash
# Start with the main testing suite
python3 blupow_testing_suite.py

# Or run a specific, quick test
python3 quick_test.py
```

---

## 📁 **File Structure & Key Components**

### Core Integration Files
```
blupow/
├── __init__.py              # Integration setup
├── coordinator.py           # Data updates with retry logic  
├── sensor.py               # 18 sensor definitions
├── blupow_client.py        # Bluetooth client + proxy support
├── config_flow.py          # UI configuration
└── manifest.json           # Integration metadata
```

### Diagnostic & Testing Tools
```
├── blupow_testing_suite.py # Unified testing suite
├── device_discovery_system.py # Discovery logic for the suite
├── device_wake_system.py  # Wake-up logic for the suite
├── connection_test.py      # Comprehensive diagnostics
├── proxy_test.py           # Multi-proxy analysis  
├── simple_test.py          # Device discovery
└── deploy.sh               # Automated deployment
```

### Documentation
```
├── DOCUMENTATION.md        # Complete technical documentation
├── TROUBLESHOOTING.md      # Detailed troubleshooting guide
└── README.md               # This file
```

---

## 📞 **Getting Help**

If you have run the diagnostic tools and followed the troubleshooting guide without success, please open an issue on our GitHub repository. Include the logs from the testing suite and any relevant information from your Home Assistant logs.
