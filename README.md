# 🔋 BluPow: Universal Renogy Bluetooth Integration

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Compatible-blue.svg)](https://www.home-assistant.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

> **Enterprise-grade Home Assistant integration for Renogy solar charge controllers with universal compatibility and intelligent environment detection.**

## 🎯 Project Overview

BluPow is a Home Assistant integration for monitoring Renogy devices via Bluetooth. It has evolved into a sophisticated, environment-aware system that embodies the **"assume nothing, detect everything"** philosophy.

### Key Features
-   **Universal Compatibility**: Works seamlessly across Docker, HassIO, Core, and manual installations.
-   **Environment Intelligence**: Automatically detects and adapts to any environment.
-   **Real-time Monitoring**: Provides a full suite of sensors for Renogy devices.
-   **Robust Error Handling**: Implements intelligent retry logic and graceful failure.
-   **ESPHome Proxy Support**: Natively supports ESPHome Bluetooth proxies for extended range.

## 🚀 Quick Start

**Automated Installation (Recommended):**
```bash
# Clone or download the integration
git clone <your-repository-url> blupow
cd blupow

# Run the intelligent deployment script
./deploy.sh
```

The deployment script automatically:
- 🔍 **Detects** your Home Assistant installation type (Docker/OS/Core)
- 📁 **Locates** your configuration directory
- 💾 **Backs up** existing installations
- 📋 **Deploys** with proper permissions
- 🔄 **Offers** to restart Home Assistant

**Manual Installation:**
If you prefer manual installation, see the [complete installation guide](DOCUMENTATION.md#installation) in the documentation.

## 📚 Full Documentation

This README provides a brief overview. For detailed information on installation, configuration, troubleshooting, and the project's development history, please see the complete guide:

### **[📄 Read the Full Documentation](./DOCUMENTATION.md)**

The full documentation is the **single source of truth** for this project and contains critical information for both users and developers.

## 📦 Installation

The recommended installation method is the automated deployment script. Full details and manual instructions are in the main documentation.

## ⚙️ Configuration

1.  Navigate to **Settings** → **Devices & Services**.
2.  Click **Add Integration** and search for **"BluPow"**.
3.  Enter the MAC address of your **Renogy device**.

For troubleshooting and advanced setup, please consult the [full documentation](./DOCUMENTATION.md).

## ❤️ Support This Project

If you find BluPow useful, please consider supporting its development.

-   **[Sponsor on GitHub](https://github.com/sponsors/MadGoatHaz)**
-   **[Send a tip via PayPal](https://paypal.me/garretthazlett)**
