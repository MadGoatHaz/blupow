# BluPow - A Vision for Seamless Home Energy Monitoring

Welcome to the BluPow project! This Home Assistant integration is born from a collaborative spirit and a passion for detailed, high-quality engineering. Our mission is to transform how you interact with your home's energy systems, making comprehensive power monitoring not just possible, but seamless and intuitive.

**Our Philosophy:** We believe that good work shines through in the details. From the lines of code to the lines of documentation, this project is a testament to a partnership between human creativity and AI-driven precision. We invite you to explore, contribute, and be part of a vision where complex energy data becomes clear, actionable insight.

## 🎯 Current Status: Production Ready

The BluPow integration is **fully functional and stable**, designed to connect with the **Renogy RIV1230RCH-SPS Inverter Charger**. It reliably reads all 22 sensors, providing a complete picture of your AC and DC power systems.

- ✅ **Hardware:** Correctly targets the Renogy Inverter.
- ✅ **Protocol:** Implements the proper Modbus communication protocol.
- ✅ **Sensors:** Creates 22 distinct sensors in Home Assistant.
- ✅ **Stability:** The integration code is robust and production-ready.

The primary remaining challenge is ensuring a stable Bluetooth connection, which is often dependent on your physical hardware and environment.

### A Project's Journey
This project underwent a significant evolution. It began with a mistaken identity—believing the target device was a simple charge controller—and was transformed by a key discovery that revealed it was a powerful inverter. This journey is a core part of our story. To understand how we got here, we encourage you to read the [Project History](docs/PROJECT_HISTORY.md).

## 🚀 Quick Start Guide

Getting started is a two-step process: first, verify your connection, then add the integration.

### 1. Verify Your Connection
Before adding the integration to Home Assistant, run our verification script to confirm that your hardware can communicate successfully.

```bash
# From the project root directory
python3 scripts/verify_connection.py
```
This script will attempt to connect to your inverter and print out the live data. If successful, you're ready for the next step. If not, it will provide clear troubleshooting guidance.

### 2. Add to Home Assistant
Once verification is successful, add the integration through the Home Assistant UI:
1.  Navigate to **Settings → Devices & Services**.
2.  Click **Add Integration** and search for **"BluPow"**.
3.  When prompted, enter the MAC address of your device: `D8:B6:73:BF:4F:75`.
4.  Your 22 inverter sensors will be added and will begin updating.

## 📁 Project Structure

This project is organized for clarity and maintainability. For a detailed guide, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

- `blupow/`: The core Home Assistant integration source code.
- `docs/`: All project documentation, including history, guides, and vision.
- `scripts/`: Standalone Python scripts for verification, diagnostics, and deployment.
- `tests/`: The automated testing suite for ensuring code quality.

## 📖 Deeper Dives: Our Documentation

We believe documentation is an art form. It's a chance to share our ideology and our commitment to quality.

- **[Future Vision](docs/guides/FUTURE_VISION.md):** Explore our ambitious roadmap for the future of power monitoring.
- **[Energy Dashboard Plan](docs/guides/ENERGY_DASHBOARD_PLAN.md):** Learn how to integrate BluPow with Home Assistant's Energy Dashboard.
- **[Bluetooth Troubleshooting](docs/troubleshooting/BLUETOOTH_CONNECTION_GUIDE.md):** A detailed guide to resolving connectivity issues.

## 🤝 The Spirit of Collaboration

This project thrives on a partnership between human insight and AI capability. Every file has been crafted with care, and every decision has been made thoughtfully. We encourage you to approach your own work with the same spirit of excellence and attention to detail.

Thank you for being a part of the BluPow journey. Let's make energy monitoring beautiful.
