# 📦 BluPow Installation Guide

This guide provides step-by-step instructions for installing the BluPow Home Assistant integration using the new containerized architecture.

---

## Architecture Overview

The BluPow integration uses a modern, robust architecture consisting of three main components:

1.  **BluPow Gateway**: A dedicated Docker container that handles all Bluetooth communication with your Renogy devices.
2.  **MQTT Broker**: A dedicated Mosquitto MQTT broker, also in a Docker container, that acts as a message bus.
3.  **Home Assistant Integration**: The custom component within Home Assistant that listens for MQTT messages and creates sensors.

This decoupled system is significantly more stable and reliable than older methods. The installer script automates the setup of this entire stack.

## Prerequisites

Before you begin, ensure you have the following installed and configured on your system (the machine that will run the gateway, e.g., your Home Assistant server or a Raspberry Pi):

-   **Git**: To clone the repository.
-   **Docker**: The containerization engine.
-   **Docker Compose**: For managing multi-container applications.
-   **Bluetooth**: A working Bluetooth adapter on the host machine.
-   **User Permissions**: Your user account must have permission to run `docker` commands without `sudo`.

---

## 🚀 Installation Steps

### Step 1: Clone the Repository

Open a terminal on your host machine and clone the BluPow project.

```bash
git clone https://github.com/MadGoatHaz/blupow.git
cd blupow
```

### Step 2: Run the Interactive Installer

The `install.sh` script is the heart of the setup process. It will guide you through creating the containers, networks, and configuration files.

```bash
./scripts/install.sh
```

### Step 3: Choose an Installation Method

The installer will present you with two options:

*   **1) Quick Install (Recommended)**: This is the preferred method for 99% of users. It will automatically:
    *   Create a dedicated Docker network (`blupow-net`).
    *   Create and run a managed Mosquitto MQTT broker (`blupow-mosquitto`).
    *   Create and run the BluPow Gateway container (`blupow-gateway`).
    *   Configure the gateway to use the managed broker.

*   **2) Custom Install (Advanced)**: This option is for advanced users who want to use their own existing MQTT broker. You will be prompted to enter the hostname/IP address, port, username, and password for your broker.

**For the best experience, please choose Option 1.**

### Step 4: Configure Your Devices

After the installer completes, you need to tell the gateway which devices to connect to.

1.  **Find your device's MAC address**. You can use a Bluetooth scanning app on your phone or a command-line tool like `bluetoothctl scan on`.
2.  **Open the device configuration file**: This file is located at `~/blupow_config/devices.json`.
3.  **Add your device(s)** to the JSON file.

**Example `devices.json`:**
```json
{
  "devices": [
    {
      "mac": "D8:B6:73:BF:4F:75",
      "device_profile": "renogy_inverter",
      "friendly_name": "My Renogy Inverter"
    }
  ]
}
```

*   `mac`: The Bluetooth MAC address of your device.
*   `device_profile`: The name of the Python file in `blupow_gateway/app/devices` that matches your device (e.g., `renogy_inverter`).
*   `friendly_name`: A name that will be used in Home Assistant.

4.  **Restart the gateway** for the changes to take effect:
    ```bash
    docker restart blupow-gateway
    ```

### Step 5: Add the Integration in Home Assistant

1.  Make sure you have the main **MQTT Integration** installed and configured in Home Assistant. If you used the "Quick Install", you must configure the HA MQTT integration to connect to the BluPow broker.
    *   **Broker**: The IP address of the machine running the BluPow containers.
    *   **Port**: `1883`
    *   No username or password is required.
2.  In Home Assistant, go to **Settings > Devices & Services**.
3.  Click **+ Add Integration** and search for **BluPow**.
4.  The integration should be found. It doesn't require any configuration in the UI, as it works entirely via MQTT discovery.

---

## ✅ Verifying the Installation

If your sensors aren't appearing, follow these steps to diagnose the issue:

1.  **Check the Docker Containers**:
    ```bash
    docker ps
    ```
    You should see `blupow-gateway` and `blupow-mosquitto` with a status of `Up`.

2.  **Check the Gateway Logs**:
    ```bash
    docker logs blupow-gateway
    ```
    Look for messages indicating it has connected to your device and is publishing data.

3.  **Monitor MQTT Traffic**:
    Use the provided `mqtt_viewer.py` script to see the raw data being published by the gateway.
    ```bash
    python3 scripts/mqtt_viewer.py
    ```
    If you see data here, the gateway is working. The problem is likely with the connection between Home Assistant and the MQTT broker.

---

## 🔄 Upgrading

To upgrade to the latest version:

1.  Navigate to the `blupow` directory.
2.  Pull the latest changes from GitHub:
    ```bash
    git pull
    ```
3.  Re-run the installer. It will rebuild the gateway container with the latest code.
    ```bash
    ./scripts/install.sh
    ```

---

## 🚨 Troubleshooting

-   **Permission Denied when running `install.sh`**:
    Run `chmod +x scripts/install.sh`.
-   **Containers fail to start**:
    Check the logs for each container (`docker logs <container_name>`) for specific error messages. This is often due to an incorrectly configured `devices.json` or issues with the host's Bluetooth service.
-   **"Sensors Unknown" in Home Assistant**:
    This usually means Home Assistant is not receiving data from the MQTT broker.
    *   Use the `mqtt_viewer.py` script to confirm data is being published.
    *   Double-check your Home Assistant MQTT integration configuration. Ensure the broker IP address is correct and there are no firewall rules blocking port 1883.