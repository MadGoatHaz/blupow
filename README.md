# BluPow Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Integrate BluPow and Renogy BLE-enabled devices into Home Assistant.

This integration uses a standalone gateway container to provide robust and reliable communication with your devices, and leverages MQTT for seamless integration with Home Assistant.

## Key Features

-   **Robust Communication**: A dedicated gateway handles all Bluetooth communication, avoiding common stability issues with direct hardware access from Home Assistant.
-   **Simple Setup**: A guided installer script handles all the complex setup for you. The recommended **Quick Install** option automatically deploys a managed, containerized Mosquitto MQTT broker, making the entire system self-contained.
-   **MQTT Discovery**: Uses Home Assistant's native MQTT discovery for seamless entity creation.
-   **Extensible**: Easily add support for new devices by creating a new device profile.
-   **Supports**:
    -   Renogy Inverters (e.g., RIV1230RCH-SPS)
    -   Renogy Charge Controllers (e.g., RNG-CTRL-RVR40)

## Quick Start Installation

This integration requires a running MQTT broker. The installer can set one up for you, which is the recommended method.

1.  **Prerequisites**:
    *   Docker and Docker Compose must be installed on your system.
    *   Your user must have permission to run `docker` commands.
    *   A working Bluetooth adapter on the host machine.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/blupow.git
    cd blupow
    ```

3.  **Run the Installer**:
    The interactive installer will guide you through the process. It can automatically create a dedicated, managed MQTT broker for you, which is the recommended approach.
    ```bash
    ./scripts/install.sh
    ```
    Follow the prompts. Choose **Option 1 (Quick Install)** unless you are an advanced user with a specific need to use your own existing MQTT broker.

4.  **Add the Integration in Home Assistant**:
    *   In Home Assistant, go to **Settings > Devices & Services**.
    *   Click **+ Add Integration** and search for **BluPow**.
    *   The configuration flow will guide you the rest of the way. If you used the "Quick Install", the integration should be able to find the broker automatically.

## How It Works

This project's architecture ensures stability by isolating the Bluetooth communication from Home Assistant. It consists of three containerized components working together:

1.  **The Gateway (`blupow-gateway`)**: A standalone Docker container that connects directly to your Renogy devices via Bluetooth. It polls for data and publishes it to the MQTT broker.
2.  **The MQTT Broker (`blupow-mosquitto`)**: A containerized Mosquitto broker, automatically configured and managed by the `install.sh` script. It acts as the central message bus.
3.  **The Home Assistant Integration (`custom_components/blupow`)**: The integration itself, which runs inside Home Assistant. It listens to the MQTT broker for data from the gateway and creates the corresponding sensors.

These components communicate over a dedicated Docker network (`blupow-net`), ensuring reliable and isolated message passing. This decoupled design is significantly more stable than trying to manage Bluetooth connections from within Home Assistant directly.

## Troubleshooting

-   **Sensors are "Unknown"**:
    *   First, check the gateway logs: `docker logs blupow-gateway`. Look for connection errors or other issues.
    *   Use an MQTT client to inspect the topics. The `scripts/mqtt_viewer.py` tool is provided for this. Verify that data is being published by the gateway.
-   **Containers not starting?** Run `docker ps -a` to see the status of all containers. Check the logs for the failing container, e.g., `docker logs blupow-mosquitto`.
-   **Device not found?** Ensure your Renogy device is powered on and within Bluetooth range of your Home Assistant machine.

## License & Attribution

This project is licensed under **GPL-3.0** in compliance with the [renogy-bt](https://github.com/cyrils/renogy-bt) library used by the MQTT gateway.

**Based on:** [renogy-bt by Cyril](https://github.com/cyrils/renogy-bt) (GPL-3.0)
**Integration by:** [@MadGoatHaz](https://github.com/MadGoatHaz)

---
<!-- Badges -->
[releases-shield]: https://img.shields.io/github/release/MadGoatHaz/blupow.svg?style=for-the-badge
[releases]: https://github.com/MadGoatHaz/blupow/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/MadGoatHaz/blupow.svg?style=for-the-badge
[commits]: https://github.com/MadGoatHaz/blupow/commits/main
[license-shield]: https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-@MadGoatHaz-blue.svg?style=for-the-badge
[maintenance-url]: https://github.com/MadGoatHaz
[sponsors-shield]: https://img.shields.io/badge/GitHub-Sponsors-ff69b4.svg?style=for-the-badge
[sponsors]: https://github.com/sponsors/MadGoatHaz
[paypal-shield]: https://img.shields.io/badge/PayPal-Donate-blue.svg?style=for-the-badge
[paypal]: https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD 