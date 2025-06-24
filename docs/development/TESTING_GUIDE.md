# BluPow Gateway: Testing Guide

---

## 🧪 **Testing Philosophy**

Our testing strategy emphasizes a layered approach. Whenever possible, changes should be validated at the lowest possible level.

1.  **Unit Tests**: For pure logic (e.g., data parsing, utility functions) that has no external dependencies (like BLE or MQTT).
2.  **Integration Tests**: For testing a single component's interaction with others, such as a new device driver running within the gateway. This is the most common and important type of testing for this project.
3.  **End-to-End (E2E) Tests**: For verifying the entire system flow, from the device to the Home Assistant UI.

---

## 🔬 **Unit Testing with `pytest`**

Unit tests are the fastest and most reliable way to test isolated logic. They are located in the `tests/unit/` directory.

**Example**: Testing the `create_device` factory function in `DeviceManager`.

A unit test could be written to ensure that `create_device` returns the correct object type for a given input string, without ever needing to connect to a real device.

**To run unit tests:**
*(Coming Soon: We are building out our `pytest` suite. This section will be updated with commands.)*

---

## ⚙️ **Integration Testing: The Primary Workflow**

This is the most critical testing you will perform when adding a new device or changing an existing driver. The goal is to run the full gateway in Docker but use a dedicated, non-production device configuration file for your tests.

### **Step 1: Create a Test Configuration**

The gateway is hardcoded to look for a `devices.test.json` file inside the `blupow_gateway/tests/config/` directory. If it finds this file, it will **ignore** the production `devices.json` in the parent directory.

1.  If it doesn't exist, create a new test configuration file:
    ```bash
    touch blupow_gateway/tests/config/devices.test.json
    ```

2.  Add the configuration for the device you are testing. This file should be an empty JSON object `{}`, or an object containing the device(s) you want to test.

    **Example `devices.test.json`:**
    ```json
    {
      "D8:B6:73:BF:4F:75": {
        "type": "my_new_device",
        "config": {}
      }
    }
    ```

    > **Important**: `devices.test.json` is listed in `.gitignore`, so you can make changes without accidentally committing them.

### **Step 2: Run the Gateway**

Launch the gateway using the standard Docker Compose command from the `blupow_gateway` directory. Because `devices.test.json` exists, the gateway will automatically load *only* the devices you specified in it.

```bash
# From the blupow_gateway/ directory
docker compose up --build
```

### **Step 3: Verify the Behavior**

Observe the output to validate your changes.

1.  **Check the Gateway Logs**:
    ```bash
    # In a separate terminal, from the blupow_gateway/ directory
    docker compose logs -f
    ```
    Look for logs from your new driver. Check for connection errors, parsing errors, or successful polling messages.

2.  **Inspect MQTT Traffic**: Use a tool like MQTT Explorer to see the data being published.
    -   Verify that Home Assistant discovery messages are sent for your device's sensors under the `homeassistant/` topic.
    -   Verify that sensor state data is being published to the `blupow/YOUR_DEVICE_ADDRESS/state` topic.

This process allows you to test your driver in a live, running gateway environment without interfering with any production device configurations.

---

## ✅ **End-to-End (E2E) Testing**

E2E testing is the final validation step. It confirms that the entire system works as expected from the user's perspective.

After validating your driver with an integration test, you can perform an E2E test by:

1.  **Deleting or renaming** your `devices.test.json` file.
2.  Restarting the gateway. It will now load the standard `devices.json`.
3.  Using the Home Assistant UI to **discover and add** your new device type.
4.  Confirming that the device and all its sensors appear correctly in the Home Assistant dashboard and that they update with the correct values. 