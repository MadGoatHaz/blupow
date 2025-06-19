# Renogy Rover (BluPow)
![Project Logo](BluPow.png)

**A modern, powerful, and modular Home Assistant integration for Renogy Bluetooth-enabled devices.**

BluPow is a Home Assistant integration designed to seamlessly connect with and control your Renogy Bluetooth-enabled devices. Built from the ground up with the entire Home Assistant ecosystem in mind, BluPow provides robust, local, and real-time access to your solar and power systems.

## Key Features

- **🔌 Native Home Assistant Experience**: Designed for full HACS integration, providing a seamless setup and user experience directly within your HA dashboard.
- **📡 Multi-Device Support**: A modular architecture allows for the easy addition of new devices. The initial focus includes the Renogy REGO series and popular Solar Charge Controllers.
- **🔐 Local First Communication**: All communication happens directly between your Home Assistant instance and your devices via Bluetooth LE. No cloud, no internet, no dependencies.
- **📊 Rich Data & Control**: Go beyond simple monitoring. BluPow aims to expose every available metric and control function, enabling complex automations and detailed energy tracking.
- **🚀 Built for Performance**: Utilizes modern Python asyncio and Home Assistant's native Bluetooth stack for efficient and reliable communication.

## Compatibility

This integration is being actively developed to support a growing list of Renogy devices.

| Device Model                               | Status      | Notes                                                    |
| ------------------------------------------ | ----------- | -------------------------------------------------------- |
| **Solar Charge Controllers**               |             |                                                          |
| Rover Series (e.g., BT-TH module)          | In Progress | Initial connection and model number read successful.     |
| **REGO Series**                            |             |                                                          |
| REGO Charge Inverter (RIV1230RCH-SPS)      | Planned     | Primary development target.                              |
| ...More to come                            | Planned     |                                                          |

## Installation

**Note:** This integration is currently in active development. Manual installation is required.

1.  Copy the `custom_components/blupow` directory from this repository into the `custom_components` directory of your Home Assistant configuration folder.
2.  Restart Home Assistant.
3.  Go to **Settings > Devices & Services** and click **+ Add Integration** to add BluPow.

## Troubleshooting

### Connection Fails in Docker Environment

If the integration discovers your device but fails to connect with an error like `Failed to connect` or `ESP_GATT_CONN_FAIL_ESTABLISH`, it likely means the Home Assistant container does not have sufficient permission to control the host's Bluetooth hardware. This is common when using Docker Compose.

To fix this, you need to grant the container access to the host's `bluetooth` group.

1.  **Find the Bluetooth Group ID (GID)** on your host machine by running:
    ```bash
    getent group bluetooth
    ```
    The output will look like `bluetooth:x:107:`. Note the number (e.g., `107`).

2.  **Edit your `docker-compose.yaml`** and add the `group_add` key to your `homeassistant` service, using the GID you found:
    ```yaml
    services:
      homeassistant:
        # ... your other settings
        group_add:
          - '107'  # <-- Replace 107 with your actual Bluetooth GID
        # ... your other settings
    ```
    *Note: If you are not using `network_mode: host`, you may also need to add the following to your `homeassistant` service:*
    ```yaml
    devices:
      - /dev/bus/usb:/dev/bus/usb
    ```

3.  **Recreate the container** to apply the changes:
    ```bash
    docker compose down && docker compose up -d
    ```

## Contributing

Contributions are highly welcome! Please feel free to open an issue or pull request.
