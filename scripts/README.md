# Home Assistant Utility Scripts

This directory contains scripts for interacting with a Home Assistant instance.

## Secure Configuration

**DO NOT hardcode your credentials (URL or token) in these scripts.**

These scripts are designed to be configured securely through environment variables. Before running them, you must set the following two variables in your terminal session:

1.  `HA_URL`: The full URL for your Home Assistant instance.
    -   Example: `export HA_URL="http://192.168.1.123:8123"`
2.  `HA_TOKEN`: A Long-Lived Access Token.
    -   You can generate one of these from your Home Assistant profile page.
    -   Example: `export HA_TOKEN="ey...your...long...token...here..."`

## Scripts

### `verify_ha_sensors.py`

This script connects to Home Assistant and verifies that a list of specified sensors exists.

**Usage:**

1.  Edit the `SENSORS_TO_VERIFY` list within the script to include the `entity_id` of each sensor you want to check.
2.  Set the environment variables as described above.
3.  Run the script: `python verify_ha_sensors.py`

### `sensor_status_check.py`

This script checks the state of specified sensors against healthy conditions that you define.

**Usage:**

1.  Edit the `SENSORS_TO_CHECK` dictionary within the script. For each sensor, you can define a check type (`is_available`, `exact_state`, `numeric_range`) and the required values. See the examples in the script for details.
2.  Set the environment variables as described above.
3.  Run the script: `python sensor_status_check.py` 