import os
import requests
import sys

# --- Configuration ---
# Load credentials securely from environment variables
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

# A list of sensor entities you want to verify.
# Add your sensor IDs to this list.
SENSORS_TO_VERIFY = [
    # Example: "sensor.living_room_temperature",
    # Example: "binary_sensor.front_door_contact",
]

# --- Script ---

def print_usage():
    """Prints the script's usage instructions."""
    print("Usage: python verify_ha_sensors.py")
    print("\nThis script verifies that a predefined list of Home Assistant sensors exist and have a state.")
    print("\nRequired environment variables:")
    print("  HA_URL:   The full URL for your Home Assistant instance (e.g., http://192.168.1.100:8123)")
    print("  HA_TOKEN: A long-lived access token generated from your Home Assistant profile page.")

def main():
    """Main function to verify sensors."""
    if not HA_URL or not HA_TOKEN:
        print("Error: HA_URL and HA_TOKEN environment variables must be set.", file=sys.stderr)
        print_usage()
        sys.exit(1)

    if not SENSORS_TO_VERIFY:
        print("Warning: No sensors are listed in SENSORS_TO_VERIFY. The script will do nothing.", file=sys.stderr)
        print("Please edit the script to add your sensor entities.")
        sys.exit(0)

    print(f"Verifying sensors against Home Assistant instance at {HA_URL}...")

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    all_sensors_ok = True
    for sensor_id in SENSORS_TO_VERIFY:
        url = f"{HA_URL}/api/states/{sensor_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                state = response.json().get("state", "N/A")
                print(f"  [OK] Found sensor '{sensor_id}' with state: {state}")
            elif response.status_code == 404:
                print(f"  [FAIL] Sensor '{sensor_id}' not found.")
                all_sensors_ok = False
            else:
                print(f"  [FAIL] Sensor '{sensor_id}' returned status code: {response.status_code}")
                all_sensors_ok = False
        except requests.exceptions.RequestException as e:
            print(f"  [FAIL] Could not connect to Home Assistant for sensor '{sensor_id}': {e}", file=sys.stderr)
            all_sensors_ok = False
            # Exit early if we can't connect to HA at all
            break
    
    print("\nVerification complete.")
    if all_sensors_ok:
        print("Result: All specified sensors were found.")
        sys.exit(0)
    else:
        print("Result: One or more specified sensors were not found.")
        sys.exit(1)

if __name__ == "__main__":
    main() 