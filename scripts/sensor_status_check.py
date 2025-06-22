import os
import requests
import sys

# --- Configuration ---
# Load credentials securely from environment variables
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

# A dictionary of sensors to check and their expected 'healthy' states.
# Add your sensor IDs as keys and their expected state (or a list of states) as values.
SENSORS_TO_CHECK = {
    # Example 1: Check if a sensor is simply available (not 'unavailable' or 'unknown')
    # "sensor.office_humidity": {"check": "is_available"},
    
    # Example 2: Check for an exact state match
    # "binary_sensor.garage_door_is_closed": {"check": "exact_state", "healthy_states": ["on"]},
    
    # Example 3: Check that a numeric sensor is within a specific range
    # "sensor.freezer_temperature": {"check": "numeric_range", "min": -25, "max": -15},
}

# --- Script ---

def print_usage():
    """Prints the script's usage instructions."""
    print("Usage: python sensor_status_check.py")
    print("\nThis script checks the status of predefined Home Assistant sensors against expected values.")
    print("\nRequired environment variables:")
    print("  HA_URL:   The full URL for your Home Assistant instance (e.g., http://192.168.1.100:8123)")
    print("  HA_TOKEN: A long-lived access token generated from your Home Assistant profile page.")

def check_sensor_state(sensor_id, config, current_state):
    """Checks a sensor's state against its configuration."""
    check_type = config.get("check")

    if check_type == "is_available":
        if current_state not in ["unavailable", "unknown"]:
            return True, f"is available with state '{current_state}'"
        else:
            return False, f"is unavailable or unknown ('{current_state}')"

    elif check_type == "exact_state":
        healthy_states = config.get("healthy_states", [])
        if current_state in healthy_states:
            return True, f"state is '{current_state}' (which is a healthy state)"
        else:
            return False, f"state is '{current_state}' (expected one of: {healthy_states})"

    elif check_type == "numeric_range":
        min_val, max_val = config.get("min"), config.get("max")
        try:
            numeric_state = float(current_state)
            if min_val <= numeric_state <= max_val:
                return True, f"value {numeric_state} is within range [{min_val}, {max_val}]"
            else:
                return False, f"value {numeric_state} is outside range [{min_val}, {max_val}]"
        except (ValueError, TypeError):
            return False, f"state '{current_state}' is not a valid number"
            
    else:
        return False, f"has an unknown check type: '{check_type}'"


def main():
    """Main function to check sensor statuses."""
    if not HA_URL or not HA_TOKEN:
        print("Error: HA_URL and HA_TOKEN environment variables must be set.", file=sys.stderr)
        print_usage()
        sys.exit(1)

    if not SENSORS_TO_CHECK:
        print("Warning: No sensors are listed in SENSORS_TO_CHECK. The script will do nothing.", file=sys.stderr)
        print("Please edit the script to add your sensor entities and their check configurations.")
        sys.exit(0)

    print(f"Checking sensor statuses on {HA_URL}...")

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    overall_status_ok = True
    for sensor_id, config in SENSORS_TO_CHECK.items():
        url = f"{HA_URL}/api/states/{sensor_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                current_state = response.json().get("state")
                is_healthy, reason = check_sensor_state(sensor_id, config, current_state)
                if is_healthy:
                    print(f"  [OK] '{sensor_id}': {reason}")
                else:
                    print(f"  [FAIL] '{sensor_id}': {reason}")
                    overall_status_ok = False
            elif response.status_code == 404:
                print(f"  [FAIL] '{sensor_id}': Sensor not found.")
                overall_status_ok = False
            else:
                print(f"  [FAIL] '{sensor_id}': API returned status code {response.status_code}")
                overall_status_ok = False

        except requests.exceptions.RequestException as e:
            print(f"  [FAIL] Could not connect to Home Assistant for sensor '{sensor_id}': {e}", file=sys.stderr)
            overall_status_ok = False
            break

    print("\nStatus check complete.")
    if overall_status_ok:
        print("Result: All checked sensors are healthy.")
        sys.exit(0)
    else:
        print("Result: One or more sensors reported an unhealthy status.")
        sys.exit(1)

if __name__ == "__main__":
    main() 