# BluPow Integration: The Complete Guide

> **This document is the single source of truth for the BluPow Home Assistant integration. Please read this before making any changes. To maintain clarity, all future documentation updates should be made here.**

## Table of Contents
1.  [**Project Overview**](#-1-project-overview)
    *   [Core Features](#core-features)
    *   [Project Philosophy](#project-philosophy)
2.  [**User Guide**](#-2-user-guide)
    *   [Installation](#installation)
    *   [Configuration](#configuration)
    *   [Sensors](#sensors--data)
3.  [**Developer's Guide**](#-3-developers-guide)
    *   [**Critical Project History**](#critical-project-history-read-this-first)
    *   [Architecture & Design](#architecture--design)
    *   [Environment Detection](#environment-detection-system)
    *   [Connection Management](#intelligent-connection-management)
    *   [Deployment](#deployment)
    *   [How to Contribute](#how-to-contribute)
4.  [**Troubleshooting**](#-4-troubleshooting)
    *   ["Device Not Found" Errors](#device-not-found-errors)
    *   [Diagnosing with the Scanner Script](#diagnosing-with-the-scanner-script)
    *   [Permission & Environment Issues](#permission--environment-issues)
    *   [Common Issues & Solutions](#common-issues--solutions)

---

## 1. Project Overview

BluPow is a Home Assistant integration for monitoring Renogy devices via Bluetooth. It has evolved into a sophisticated, environment-aware system that embodies the **"assume nothing, detect everything"** philosophy.

### Core Features
-   **Universal Compatibility**: Works seamlessly across Docker, HassIO, Core, and manual installations on Linux, Windows, and macOS.
-   **Environment Intelligence**: Automatically detects the host environment and adapts its connection strategies.
-   **Real-time Monitoring**: Provides sensors for battery voltage/current/SOC/temperature, solar voltage/current/power, and more.
-   **Robust Error Handling**: Implements intelligent retry logic and graceful failure to ensure reliability.
-   **ESPHome Proxy Support**: Natively supports ESPHome Bluetooth proxies for extended range.
-   **Direct Connection**: Connects directly to Renogy devices **without** requiring Bluetooth pairing.

### Project Philosophy
-   **Assume Nothing, Detect Everything**: Proactively detect the environment rather than making assumptions.
-   **Graceful Degradation**: Fail gracefully and recover intelligently with clear, actionable error messages.
-   **Universal Compatibility**: A single codebase designed to work across all Home Assistant environments and platforms.
-   **Future-Proof Architecture**: Use modern APIs with fallbacks to ensure long-term stability.

---

## 2. User Guide

### Installation

BluPow offers multiple installation methods to accommodate different Home Assistant setups.

#### **🚀 Automated Deployment (Recommended)**

The easiest way to install BluPow is using the included automated deployment script. This script intelligently detects your Home Assistant installation type and handles the deployment accordingly.

**Quick Start:**
```bash
# Clone or download the BluPow integration
git clone <repository-url> blupow
cd blupow

# Run the automated deployment script
./deploy.sh
```

**What the script does:**
- **🔍 Auto-detects** your Home Assistant installation type (Docker, Home Assistant OS, Core)
- **📁 Locates** your Home Assistant configuration directory automatically
- **💾 Creates backups** of existing installations
- **📋 Copies** all necessary files with proper permissions
- **🔐 Sets** appropriate ownership for your environment
- **✅ Verifies** successful installation
- **🔄 Offers** to restart Home Assistant (Docker installations)

**Supported Installation Types:**
- **Docker**: Automatically detects container names and config paths
- **Home Assistant OS/Supervised**: Handles system-level permissions
- **Home Assistant Core**: Works with pip-based installations
- **Manual**: Prompts for custom paths if auto-detection fails

**Example Output:**
```
🚀 BluPow Integration Deployment Script
========================================
🔍 Detecting Home Assistant environment...
🐳 Detected: Docker Home Assistant at /home/user/opt/homeassistant/config
✅ Found Docker container: homeassistant

📋 Deployment Summary:
   Installation Type: docker
   Source directory: /home/user/blupow
   Target directory: /home/user/opt/homeassistant/config/custom_components/blupow
   Restart command: docker restart homeassistant

💾 Backing up existing installation...
📁 Creating new BluPow integration directory...
📋 Copying integration files...
🌐 Copying translations...
🔐 Setting proper permissions...
✅ Installation successful!
```

#### **📋 Manual Installation**

If you prefer manual installation or the automated script doesn't work for your setup:

1. **Locate your Home Assistant configuration directory** (contains `configuration.yaml`)
2. **Create the custom components directory** if it doesn't exist:
   ```bash
   mkdir -p <config_directory>/custom_components
   ```
3. **Copy the BluPow integration**:
   ```bash
   cp -r blupow <config_directory>/custom_components/
   ```
4. **Set proper permissions** (if needed):
   ```bash
   chown -R homeassistant:homeassistant <config_directory>/custom_components/blupow
   ```
5. **Restart Home Assistant**

### Configuration
1.  Navigate to **Settings** → **Devices & Services**.
2.  Click **Add Integration** and search for **"BluPow"**.
3.  Enter the MAC address of your Renogy device when prompted.

#### Optional: Enable Debug Logging
For detailed troubleshooting, add the following to your `configuration.yaml` and restart Home Assistant:
```yaml
logger:
  logs:
    custom_components.blupow: debug
```

### Sensors & Data
The integration provides a comprehensive set of sensors for monitoring your Renogy system, which are fully compatible with the Home Assistant Energy Dashboard.

---

## 3. Developer's Guide

### **Critical Project History (Read This First)**

This integration was originally developed to connect to a Renogy solar charge controller. However, during development, there was significant confusion, and the integration was incorrectly configured to connect to a **temperature and humidity sensor (`BT-TH-6A667ED4` at MAC `C4:D3:6A:66:7E:D4`)**.

This led to a series of misleading bug fixes and documentation, including attempts to "mock" energy data from the temperature sensor. This is the root cause of the "Could not find BLE device" errors.

**The integration is designed for RENOGY devices only.**

The last known **working Renogy device** from the test environment was an inverter with the MAC address **`D8:B6:73:BF:4F:75`**.

**Developer's Golden Rule:** Before making any changes, verify the target device is a compatible Renogy device and is discoverable by running the `simple_test.py` scanner script. **Do not add support for non-Renogy devices to this integration.**

### Architecture & Design
The integration is built with a modular design:
-   `__init__.py`: Handles the main integration setup and entry points.
-   `blupow_client.py`: The core client responsible for all BLE communication, connection logic, and data parsing.
-   `coordinator.py`: The Home Assistant DataUdpateCoordinator, which manages data fetching and updates.
-   `sensor.py`: Defines the sensor entities that are created in Home Assistant.
-   `config_flow.py`: Manages the user-facing configuration process.

### Environment Detection System
The client can detect:
-   **Platform**: Linux/Windows/macOS.
-   **Installation Type**: Docker/HassIO/Core/Manual.
-   **BLE Backend**: BlueZ/WinRT/CoreBluetooth.

This allows the integration to apply environment-specific optimizations, such as adjusting connection timeouts.

### Intelligent Connection Management
-   **Progressive Retry Logic**: 3 connection attempts with exponential backoff.
-   **Device-Specific Strategies**: ESP32 devices have a different, more patient retry strategy.
-   **Modern API Usage**: Uses the latest `bleak` APIs with fallbacks for older versions to prevent deprecation warnings.

### Deployment

The BluPow integration includes an intelligent deployment script (`deploy.sh`) that automatically handles installation across different Home Assistant environments.

#### **Deployment Script Architecture**

The script uses a multi-stage detection approach:

1. **Environment Detection**: Identifies Home Assistant installation type
   - Home Assistant OS/Supervised (`/usr/share/hassio`)
   - Docker installations (multiple common paths)
   - Home Assistant Core (pip-based installations)
   - Manual fallback (user-specified paths)

2. **Docker Container Detection**: For Docker installations
   - Searches for common container names (`homeassistant`, `home-assistant`, `hass`, `ha`)
   - Prompts user if auto-detection fails
   - Sets appropriate restart commands

3. **Permission Management**: Sets ownership based on environment
   - Home Assistant OS: `root:root`
   - Docker: Current user ownership
   - Core: `homeassistant:homeassistant` with fallback
   - Manual: Current user ownership

4. **Safety Features**:
   - **Automatic backups** with timestamps
   - **Permission verification** before deployment
   - **Installation validation** after deployment
   - **Graceful error handling** with helpful messages

#### **Customizing the Deployment Script**

To adapt the script for your environment:

**Adding New Detection Paths:**
```bash
# Add to DOCKER_PATHS array in detect_ha_environment()
DOCKER_PATHS=(
    "/your/custom/path/config"
    # ... existing paths
)
```

**Custom Container Names:**
```bash
# Add to CONTAINER_NAMES array in detect_docker_details()
CONTAINER_NAMES=("your-container-name" "homeassistant" "hass")
```

**Environment-Specific Ownership:**
```bash
# Add new case in set_proper_ownership()
"your-environment")
    chown -R your-user:your-group "$BLUPOW_DIR"
    ;;
```

#### **Running the Deployment Script**

**Basic Usage:**
```bash
./deploy.sh
```

**With Different Permissions:**
```bash
# For Home Assistant OS/Supervised
sudo ./deploy.sh

# For Docker with permission issues
sudo ./deploy.sh
```

**Script Output Levels:**
- **🔍 Detection**: Environment and path discovery
- **📋 Summary**: Pre-deployment confirmation
- **💾 Backup**: Existing installation backup
- **📁 Copy**: File deployment progress
- **🔐 Permissions**: Ownership and permission setting
- **✅ Verification**: Installation validation
- **🔄 Restart**: Optional Home Assistant restart

The script is designed to be **safe**, **intelligent**, and **adaptable** to virtually any Home Assistant setup.

### How to Contribute
1.  **Confirm the device is a compatible Renogy product.**
2.  Follow the existing design philosophy: "Assume nothing, detect everything."
3.  Ensure any new code is compatible across all platforms and environments.
4.  **Update this `DOCUMENTATION.md` file** with any changes to functionality, architecture, or troubleshooting steps. Do not create separate `.md` files.

---

## 4. Troubleshooting

### Common Issues & Solutions

#### **"'BluPowClient' object has no attribute '_device'" Error**

**Symptoms:**
```
ERROR [custom_components.blupow.coordinator] Failed to initialize BluPow coordinator: 'BluPowClient' object has no attribute '_device'
```

**Root Cause:** Mismatch between coordinator and client attribute names.

**Solution:** The coordinator should reference `client._ble_device`, not `client._device`.

**Fix Applied:** 
```python
# coordinator.py line 28
# WRONG:
self.ble_device = client._device if client else None

# CORRECT:
self.ble_device = client._ble_device if client else None
```

**Status:** ✅ **RESOLVED** - Fixed in current version.

#### **"Device Not Found" Errors**

**Symptoms:**
```
Could not find BLE device with address [MAC_ADDRESS]
```

**This is not a bug in the integration.** The integration is correctly reporting that the device is not advertising.

#### **Important Note on Pairing**
This integration uses a **direct connection** method inspired by the `cyrils/renogy-bt` library. **It does not use or require Bluetooth pairing.**

-   **DO NOT** pair the Renogy device with your Home Assistant host system in the Bluetooth settings.
-   If the device is already paired with the host, **unpair it**.
-   The integration only needs the device to be advertising. It will handle the connection directly. A paired state can interfere with the connection process.

The most common causes are:
1.  **The device is powered off or in a deep sleep state.**
2.  **The device's Bluetooth radio is disabled.**
3.  **The device is out of Bluetooth range.**
4.  **You are trying to connect to an incompatible (non-Renogy) device.**

### Diagnosing with the Scanner Script
The `simple_test.py` script is a dependency-free scanner that will show you all BLE devices visible to your system.

**Run the script from the command line:**
```bash
python3 simple_test.py
```

-   **If your device is NOT in the list:** The problem is with the device or its environment. Power cycle the device, check its Bluetooth settings, and ensure it is within range.
-   **If your device IS in the list:** The problem may be with the Home Assistant Bluetooth integration itself. Try restarting Home Assistant.

### Permission & Environment Issues
-   **Linux Permissions:** Ensure your Home Assistant user is in the `bluetooth` group.
    ```bash
    sudo usermod -a -G bluetooth $USER
    ```
-   **Docker Networking:** The integration should handle Docker networking automatically. If you have a unique setup, ensure the container has access to the host's Bluetooth adapter.
-   **System Bluetooth Service:** On Linux, you can try restarting the Bluetooth service.
    ```bash
    sudo systemctl restart bluetooth
    ``` 

## 🔧 Troubleshooting

### Integration Setup Issues

#### ✅ RESOLVED: "Invalid device info" Error
**Issue**: Entities not appearing due to invalid device info
**Status**: **FIXED** ✅
**Solution**: Updated device info creation to use identifiers when BLE device unavailable

#### ✅ RESOLVED: "No backend with an available connection slot"
**Issue**: Connection failures due to Bluetooth connection limits
**Status**: **IMPROVED** ✅
**Solution**: Added retry logic with exponential backoff and better connection cleanup

#### Current Status (June 19, 2025)
- ✅ **Integration loads successfully**
- ✅ **All 18 sensors created and visible in Home Assistant**
- ✅ **Device shows as "connecting" status (graceful fallback)**
- ⚠️ **Device discoverable but connection intermittent** (-88 dBm signal)

### Connection Issues

#### Device Not Connecting
If the device is discoverable but won't connect:

1. **Signal Strength**: Check RSSI value - should be > -85 dBm for reliable connection
2. **Power Cycle**: Turn the Renogy device off and on
3. **Bluetooth Stack**: Restart Home Assistant to clear Bluetooth connections
4. **Physical Distance**: Move Home Assistant host closer to device
5. **Interference**: Check for other Bluetooth devices causing interference

#### Device Not Discoverable
If the device doesn't appear in scans:

1. **Device Status**: Ensure Renogy device is powered on and operational
2. **Bluetooth Mode**: Some devices need to be in pairing/discovery mode
3. **Range**: Move closer to the device (within 10 meters)
4. **Multiple Scans**: Run scanner multiple times - devices may not always advertise

### Debug Commands

```bash
# Test device discovery and connectivity
cd /home/madgoat/opt/homeassistant/config/custom_components/blupow
python3 simple_test.py

# Check integration logs
docker logs homeassistant 2>&1 | grep -i blupow | tail -20

# Monitor connection attempts
docker logs homeassistant 2>&1 | grep -E "(Connection|connect)" | grep blupow
```

### Signal Strength Reference
- **-40 to -60 dBm**: Excellent (< 2 meters)
- **-60 to -75 dBm**: Good (2-8 meters)  
- **-75 to -85 dBm**: Fair (8-15 meters)
- **-85 to -95 dBm**: Poor (> 15 meters, unreliable)

### Recent Fixes Applied
- **Device Info**: Fixed invalid device info causing entity rejection
- **Connection Retry**: Added exponential backoff for connection slot issues  
- **Graceful Fallback**: Integration works even when device unreachable
- **Better Logging**: Improved diagnostic information
- **Connection Cleanup**: Proper cleanup of failed connections 

## 🌐 ESPHome Bluetooth Proxy Support

### Overview

The BluPow integration automatically supports **ESPHome Bluetooth Proxies** to extend Bluetooth range and improve connectivity. As documented in the [ESPHome Bluetooth Proxy guide](https://esphome.io/components/bluetooth_proxy.html), these proxies can significantly expand Home Assistant's Bluetooth reach.

### Benefits

- **Extended Range**: Reach devices up to 10+ meters from any proxy location
- **Fault Tolerance**: Multiple proxies provide redundant connectivity  
- **Automatic Integration**: Home Assistant automatically uses all available proxies
- **Active Connections**: Support for up to 3 simultaneous active connections per proxy

### Your Current Proxy Setup

**Proxy Details**:
- **Name**: `esp32-bluetooth-proxy-2105e4` (Bluetooth Proxy Testy)
- **IP Address**: `192.168.51.151`
- **MAC Address**: `A0:B7:65:21:05:E6`
- **Status**: ✅ Active with 3 connection slots
- **Configuration**: Uses [esphome/bluetooth-proxies](https://github.com/esphome/bluetooth-proxies) template

**Current Configuration**:
```yaml
substitutions:
  name: esp32-bluetooth-proxy-2105e4
  friendly_name: Bluetooth Proxy Testy
packages:
  esphome.bluetooth-proxy: github://esphome/bluetooth-proxies/esp32-generic/esp32-generic.yaml@main
```

### How It Works with BluPow

1. **Automatic Discovery**: Home Assistant's Bluetooth integration automatically uses your proxy
2. **Extended Range**: Your proxy can reach Renogy devices that the main system cannot
3. **Seamless Operation**: BluPow integration works transparently through the proxy
4. **Better Signal**: Proxy may provide stronger signal than built-in Bluetooth

### Testing Proxy Connectivity

To test if your proxy can reach the Renogy device:

```bash
# Check if proxy is active in Home Assistant logs
docker logs homeassistant 2>&1 | grep -i "bluetooth.*proxy"

# Monitor proxy connections
docker logs homeassistant 2>&1 | grep -i "esp32-bluetooth-proxy-2105e4"
```

### Optimizing Proxy Performance

Based on the [ESPHome documentation](https://esphome.io/components/bluetooth_proxy.html):

1. **Signal Strength**: Your proxy shows excellent WiFi signal (-48 dB)
2. **Active Connections**: Configured for 3 simultaneous connections
3. **Scan Parameters**: Uses optimized scanning (320ms interval, 30ms window)
4. **Raw Advertisements**: Enabled for maximum compatibility

### Troubleshooting with Proxy

If direct connection fails but proxy is available:

1. **Check Proxy Status**: Ensure proxy is online at `192.168.51.151`
2. **Proximity**: Verify proxy is closer to Renogy device than main system
3. **Connection Slots**: Monitor if all 3 connection slots are in use
4. **Range Test**: Move proxy closer to Renogy device if needed

### Multiple Proxy Setup

As mentioned in the [community discussion](https://community.home-assistant.io/t/beginner-help-with-esphome-bluetooth-proxy/459061), you can:

- Deploy multiple proxies for better coverage
- Each proxy provides 3 additional connection slots
- Home Assistant automatically load-balances across proxies
- Proxies provide fault-tolerant connectivity

### Current Status with Proxy

Your BluPow integration should automatically benefit from the proxy:
- **Proxy Location**: `192.168.51.151` 
- **Renogy Device**: `D8:B6:73:BF:4F:75` (BTRIC134000035)
- **Signal Improvement**: Proxy may provide better signal than -88 dBm direct connection 