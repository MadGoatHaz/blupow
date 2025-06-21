# Developer Guide

This guide provides instructions for setting up a development environment for the BluPow integration.

## Prerequisites

- Python 3.9+
- Docker & Docker Compose
- A running Home Assistant instance
- A supported Renogy Bluetooth device

## Local Development Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd blupow
    ```

2.  **Set up a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Link to Home Assistant**:
    To test the integration locally, you can symlink the `custom_components/blupow` directory into your Home Assistant `custom_components` directory.

    ```bash
    ln -s $(pwd) /path/to/your/ha/config/custom_components/blupow
    ```

## Running Tests

The project includes a suite of unit and integration tests.

```bash
# To be implemented
pytest
```

## Code Structure

-   `blupow_client.py`: Handles all Bluetooth communication with the device.
-   `coordinator.py`: The Home Assistant DataUpdateCoordinator, which manages polling and data updates.
-   `sensor.py`: Defines the sensor entities that are created in Home Assistant.
-   `config_flow.py`: Manages the user configuration flow from the UI.
-   `const.py`: Contains constants used throughout the integration. 