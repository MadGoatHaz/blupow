<div align="center">

# BluPow - Renogy Device Integration for Home Assistant

</div>

<div align="center">

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![Project Maintenance][maintenance-shield]][maintenance-url]
[![GitHub Sponsors][sponsors-shield]][sponsors]

**A professional Home Assistant integration for Renogy devices.**

</div>

<div align="center">
<img src="BluPow.png" alt="BluPow Integration" width="300"/>
</div>

## Key Features

-   **Robust Communication**: A dedicated gateway handles all Bluetooth Low Energy (BLE) communication, providing a stable and reliable connection to your devices.
-   **Modern Architecture**: The gateway is a standalone Docker container that communicates with Home Assistant via MQTT, ensuring HA stability.
-   **MQTT Discovery**: Uses Home Assistant's native MQTT discovery for seamless and automatic entity creation.
-   **UI-Driven Configuration**: Add and remove your Renogy devices directly from the Home Assistant UI. No more manual YAML or JSON file editing!
-   **Extensible**: The driver-based architecture makes it easy to add support for new Modbus-over-BLE devices.
-   **Supports**:
    -   Renogy Charge Controllers (e.g., Rover series)
    -   Renogy Inverters
    -   Can be extended to other generic Modbus devices.

---

## How It Works

This integration uses a modern, decoupled architecture to ensure stability and performance. It consists of two main parts:

1.  **The BluPow Gateway (`blupow_gateway`)**: A Python application, designed to be run as a Docker container. It connects directly to your Renogy devices via Bluetooth, polls them for data, and publishes the data to an MQTT broker. It also listens for commands from Home Assistant (e.g., to add/remove devices).
2.  **The Home Assistant Integration (`custom_components/blupow`)**: A lightweight "branding" integration that runs inside Home Assistant. It provides the UI configuration flow for adding devices and relies on MQTT Discovery to automatically create all the sensors.

This separation means that the often-unstable Bluetooth communication is handled outside of Home Assistant, preventing integration crashes from impacting your HA instance.

---

## Installation & Setup

Setup requires a running MQTT broker and Docker.

1.  **Prerequisites**:
    *   An MQTT Broker (like the official Mosquitto addon) must be installed and running in Home Assistant.
    *   Docker and Docker Compose must be installed on a machine that has a working Bluetooth adapter and is within range of your Renogy devices. This can be the same machine as Home Assistant OS.

2.  **Run the Gateway**:
    *   Clone this repository to the machine that will run the gateway.
    *   Navigate to the `blupow_gateway` directory.
    *   Create a `.env` file and configure your `MQTT_BROKER` IP address and credentials.
    *   Run the gateway using Docker Compose:
        ```bash
        docker compose up -d --build
        ```

3.  **Add the Integration in Home Assistant**:
    *   Copy the `custom_components/blupow` directory into your Home Assistant `custom_components` folder.
    *   Restart Home Assistant.
    *   Go to **Settings > Devices & Services**.
    *   Click **+ Add Integration** and search for **BluPow**.
    *   The integration will be added without any further configuration steps.

4.  **Add Your Devices**:
    *   Once the BluPow integration is added, click **"Configure"** on the integration card.
    *   You will be prompted to enter the Bluetooth MAC Address and select the device type for your Renogy device.
    *   The gateway will then automatically discover and publish the device and its sensors to Home Assistant.

---

## Troubleshooting

-   **Sensors are "Unknown"**:
    *   Check the gateway logs: `docker logs blupow_gateway-gateway-1`. Look for Bluetooth connection errors or other issues.
    *   Use an MQTT exploration tool (like MQTT Explorer) to connect to your broker. Verify that topics under `homeassistant/sensor/blupow_...` are being created and that `blupow/.../state` topics are receiving data.
-   **Device not found during polling?** Ensure your Renogy device is powered on and within Bluetooth range of the machine running the gateway.

---

## Support

### Documentation
- **[Project Genesis and AI Protocol](docs/PROJECT_GENESIS_AND_AI_PROTOCOL.md)** - The single source of truth for architecture, workflow, and AI/developer onboarding. **START HERE.**
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development and contribution guidelines.

### Getting Help
- **[GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)** - Bug reports and feature requests.
- **[GitHub Discussions](https://github.com/MadGoatHaz/blupow/discussions)** - Community support and questions.

---

## License & Philosophy

This project is licensed under the **MIT License**.

-   **Stability First**: The primary goal is to provide a stable, "it-just-works" experience.
-   **Professionalism**: We aim to build a reliable, robust tool for the community.
-   **Community Driven**: This project thrives on community contributions.

---

## Support Development

If this integration is useful for you, please consider showing your support!

- **[GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)** - The best way to support ongoing development.

**Maintainer**: [@MadGoatHaz](https://github.com/MadGoatHaz)

---

<!-- Badges -->
[releases-shield]: https://img.shields.io/github/release/MadGoatHaz/blupow.svg?style=for-the-badge
[releases]: https://github.com/MadGoatHaz/blupow/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/MadGoatHaz/blupow.svg?style=for-the-badge
[commits]: https://github.com/MadGoatHaz/blupow/commits/main
[license-shield]: https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-@MadGoatHaz-blue.svg?style=for-the-badge
[maintenance-url]: https://github.com/MadGoatHaz
[sponsors-shield]: https://img.shields.io/badge/GitHub-Sponsors-ff69b4.svg?style=for-the-badge
[sponsors]: https://github.com/sponsors/MadGoatHaz 