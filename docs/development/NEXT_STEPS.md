# Next Steps for BluPow Development

**Updated:** 2025-06-19
**Status:** **Data channel established!** We are now successfully receiving data frames from the Renogy device.

The primary blocker has been resolved. The development focus now shifts from establishing a connection to correctly interpreting and utilizing the data within Home Assistant.

---

## 1. ✅ ~~Establish a Reliable Data Channel~~ (Completed)

- **Original Problem:** The client was not receiving data, only Modbus "Acknowledge" frames.
- **Solution:** A multi-faceted approach involving robust data buffering, fixing the test suite, and, most critically, **using a specific Modbus Device ID (e.g., 1) instead of the broadcast address (255)** in the command frame.
- **Outcome:** The `BluPowClient` can now reliably connect and receive data packets.

## 2. Map Parsed Data to Home Assistant Sensors (Current Task)

- **Objective:** Integrate the data received from `BluPowClient` into the Home Assistant entity model.
- **Current State:** The client receives a data dictionary, but the values are `null`. This indicates the data frame is arriving but may not be correctly parsed or the device is in a state where it's not reporting values (e.g., no solar power at night).
- **Actions:**
    - **Investigate Null Values:**
        - Analyze the raw data buffer in `blupow_client.py` to see the actual byte array being returned.
        - Cross-reference the received bytes with the `cyrils/renogy-bt` and official Renogy Modbus documentation to ensure the parser is looking at the correct byte offsets for each value.
        - Test the device during different operational states (e.g., while charging, with a load) to see if values populate.
    - **Update `coordinator.py`:**
        - The `BluPowDataUpdateCoordinator` needs to be updated to correctly call `client.get_data()`.
        - The coordinator should handle the `null` or error states gracefully, making sensors `unavailable` if necessary.
    - **Update `sensor.py`:**
        - Ensure the `BluPowSensor` entities correctly reference the data provided by the coordinator.
        - Add any new sensors that are now available from the parsed data.
        - Implement correct `device_class`, `unit_of_measurement`, and `state_class` for each sensor to integrate properly with Home Assistant's UI and Energy Dashboard.

## 3. Refine Connection Management and Error Handling

- **Objective:** Make the integration robust and stable for long-term use.
- **Actions:**
    - **Connection Stability:** Implement a connection retry mechanism with backoff in `coordinator.py` if the device becomes unavailable.
    - **Error States:** Ensure that `BleakError` and other exceptions are caught gracefully and reported to the user through the UI.
    - **Configuration:** Allow the Modbus `device_id` to be configured in the `config_flow.py` UI instead of being hardcoded, as it may vary between devices.

## 4. Documentation and Cleanup

- **Objective:** Finalize the integration for a beta release.
- **Actions:**
    - Update the main `README.md` with the latest findings and a more accurate description of the connection process.
    - Add a "Troubleshooting" section for common issues like incorrect device IDs.
    - Remove any leftover debugging code and finalize code comments.
    - Create a pull request with all the changes for review.

# Next Steps: Data Parsing and Sensor Validation

## 1. Current State & Goal

**Current State**: The BluPow integration successfully connects to the Renogy device (`D8:B6:73:BF:4F:75`), and all 18 sensors are created in Home Assistant. However, most sensors report "Unknown" or an initial state like "offline".

**Primary Goal**: Implement the data parsing logic in `blupow_client.py` to correctly interpret the raw Bluetooth byte stream from the Renogy device and populate the sensors with real data.

**Evidence**:
- The `Model Number` is correctly identified as `RNG-CTRL-RVR40`. This proves that basic communication and some level of data parsing is working.
- Logs show the client sending a command and receiving a short notification, but the full data payload is not being processed.
  ```
  DEBUG (MainThread) [custom_components.blupow.blupow_client] Sending Modbus command: ff03010000072a10
  DEBUG (MainThread) [custom_components.blupow.blupow_client] 📨 Notification received: ff8305e0c3
  ```

---

## 2. Investigation and Development Plan

The core of the work will be in `blupow_client.py`. The received notification `ff8305e0c3` is likely a Modbus "acknowledge" or "exception" response, not the data itself. The data probably arrives in a subsequent packet.

### Step 1: Analyze the Renogy Bluetooth Protocol
- **Research**: The key to success is understanding the device's specific Modbus-over-Bluetooth protocol. The `README.md` mentions `cyrils/renogy-bt` as an inspiration—this GitHub repository is the best place to start looking for the protocol documentation.
- **Goal**: Find the register maps that define which bytes correspond to which values (e.g., that bytes 4-5 represent Battery Voltage).

### Step 2: Enhance the Data Reception Logic
- **File to Edit**: `blupow_client.py`.
- **Focus Area**: The Bluetooth notification handler method (likely named `_notification_handler` or similar).
- **Hypothesis**: The client needs to wait for and assemble multiple notification packets to get the full data frame.
- **Action**:
    1.  Modify the logic to buffer incoming data until a complete data frame (as defined by the protocol) is received. Look for start/end bytes or a length field in the packet.
    2.  Add extensive `_LOGGER.debug()` statements to print the raw byte arrays being received. This is critical for debugging.

### Step 3: Implement the Parsing Logic
- **File to Edit**: `blupow_client.py`.
- **Focus Area**: The method responsible for processing the complete data frame.
- **Action**:
    1.  Once you have a full data frame (e.g., `bytearray(b'...')`), use the protocol documentation from Step 1 to parse it.
    2.  This will involve slicing the byte array and using Python's `struct` module or simple byte manipulation (e.g., `int.from_bytes()`) to convert byte pairs into integers or floats.
    3.  Create a dictionary of parsed data (e.g., `{'battery_voltage': 13.5, 'solar_power': 150.0}`).
    4.  Ensure the data is returned to the `coordinator.py` so it can be passed to the sensors.

### Step 4: Test Iteratively
- Use the provided testing scripts to validate your changes without needing to restart Home Assistant every time.
- **Command**:
  ```bash
  # Run the full diagnostic suite from your workspace
  python3 tests/diagnostics/blupow_testing_suite.py
  ```
- Modify the test suite as needed to call your new parsing functions directly and print the output.

---

## 3. Goal State

All sensors for the Renogy device in Home Assistant should display correct, real-time numerical data, updating at the interval set by the coordinator. The "Unknown" state should be completely eliminated for all primary sensors. 