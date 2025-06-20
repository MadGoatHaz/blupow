# BluPow Integration Troubleshooting Guide

This guide helps you solve common issues with the BluPow integration. Please read the sections below to diagnose your problem.

---

## Problem 1: Device Not Found in Scan

This is the most common issue for new setups. Your Home Assistant log will show messages like:

```
WARNING (MainThread) [custom_components.blupow.blupow_client] ⚠️ Device D8:B6:73:BF:4F:75 not found in scan
WARNING (MainThread) [custom_components.blupow.coordinator] Device D8:B6:73:BF:4F:75 is not available
```

This means your Home Assistant instance cannot "see" the Renogy device via Bluetooth.

### ✅ Step 1: Run the Diagnostic Tool

We have a built-in diagnostic tool to help you. Run it from your Home Assistant's terminal or a terminal with access to the codebase.

**Note**: This script must be run in an environment where the Home Assistant packages are installed. If you are using Home Assistant OS or a supervised installation, use the "Terminal & SSH" add-on.

```bash
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/blupow_testing_suite.py
```

When prompted, select option `6` for **Current Device Diagnostics**.

The tool will tell you if the device is visible and if it can connect.

### 🔒 Step 2: Check for Container Security Issues (NEW)

**If you see AppArmor/DBus errors like:**
```
[org.freedesktop.DBus.Error.AccessDenied] An AppArmor policy prevents this sender from sending this message to this recipient
```

This indicates a **container security restriction** preventing Bluetooth access. This is common in Docker-based Home Assistant installations.

**Solutions:**
1. **Use Home Assistant OS/Supervised**: These have proper Bluetooth integration built-in
2. **Docker Privileged Mode**: Add `--privileged` to your Docker run command (security risk)
3. **Docker Device Access**: Add `--device /dev/bus/usb` and appropriate Bluetooth devices
4. **Host Network Mode**: Use `--network host` in Docker (reduces container isolation)

**For Docker Compose users**, add to your `docker-compose.yml`:
```yaml
services:
  homeassistant:
    privileged: true
    # OR specific device access:
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
      - /dev/bus/usb:/dev/bus/usb
    network_mode: host
```

### ⚙️ Step 3: Common Causes & Solutions

If the diagnostic tool fails, here are the likely reasons why:

| Cause                                   | Solution                                                                                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Container Security (AppArmor)**       | See Step 2 above - modify Docker configuration for Bluetooth access                                                                                                           |
| **Device is Off**                       | Ensure your Renogy charge controller or device has power. Check the physical display.                                                                                          |
| **Bluetooth is Off/Asleep**             | Some Renogy devices have a power-saving mode that disables Bluetooth. Try connecting during peak sun hours when the device is most active.                                       |
| **Device is Paired Elsewhere**          | Your Renogy device can only connect to **one** thing at a time. **Disconnect the official Renogy app on your phone** or any other device that might be connected to it.         |
| **Out of Range**                        | Bluetooth has a limited range. Move your Home Assistant device (or Bluetooth proxy) closer to the Renogy device. Physical barriers like concrete and metal walls reduce range.    |
| **Incorrect MAC Address**               | Double-check that the MAC address you entered in the BluPow integration configuration in Home Assistant is correct.                                                              |
| **Host Bluetooth Issues**               | Your computer or Raspberry Pi's Bluetooth adapter might be malfunctioning. Try restarting the Bluetooth service or the entire host machine.                                      |

---

## Problem 2: Connection Fails (Device is Found)

If the diagnostic tool **finds** your device but **cannot connect**, or your logs show errors like `ESP_GATT_CONN_FAIL_ESTABLISH`, it means there's a problem establishing a stable connection.

### 1. Immediate Actions

**Check Device Status:**
```bash
# Run the connection diagnostics
python3 connection_test.py
```

**Verify Bluetooth Service:**
```bash
# Check Bluetooth status
sudo systemctl status bluetooth
sudo hciconfig -a
```

**Check for Interference:**
- Look for other devices trying to connect to the Renogy device
- Temporarily disable other Bluetooth devices
- Check WiFi channel conflicts (2.4GHz band)

### 2. Device-Specific Solutions

**Renogy Device Power Management:**
- The device may be in deep sleep mode
- Try connecting during different times of day
- Power cycle the device if possible.
- Check if device has a "pairing mode" or "Bluetooth enable" setting

**Signal Strength Optimization:**
- Your ESPHome proxies should help with range
- Move closer to test if distance is the issue
- Check for physical obstructions (metal, concrete walls)

### 3. Home Assistant Bluetooth Optimization

**Restart Bluetooth Integration:**
1. Go to Settings → Devices & Services
2. Find "Bluetooth" integration
3. Click "..." → Reload

**Check Bluetooth Adapter:**
```bash
# List Bluetooth adapters
hciconfig
# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

**Clear Bluetooth Cache:**
```bash
sudo systemctl stop bluetooth
sudo rm -rf /var/lib/bluetooth/*
sudo systemctl start bluetooth
```

### 4. ESPHome Proxy Optimization

Your logs may show proxies detected like:
- `esp32-bluetooth-proxy-2105e4` (192.168.51.151) - Primary
- `proxy-2` (192.168.51.207) - Secondary  
- `proxy-3` (192.168.51.109) - Tertiary

**Test Proxy Connectivity:**
```bash
# Test proxy connectivity
python3 proxy_test.py
```

**Proxy Troubleshooting:**
- Ensure proxies are close to the Renogy device
- Check proxy logs for connection attempts
- Consider temporarily disabling 2 proxies to reduce conflicts

### 5. Advanced Diagnostics

**Monitor Bluetooth Traffic:**
```bash
# Install btmon if not available
sudo apt update && sudo apt install bluez-tools

# Monitor Bluetooth activity
sudo btmon
```

**Check System Resources:**
```bash
# Check if system is overloaded
top
# Check memory usage
free -h
# Check Bluetooth processes
ps aux | grep blue
```

---

## Problem 3: Config Flow Could Not Be Loaded

If you see this error in the Home Assistant UI when trying to add the BluPow integration, it means there's a problem with the integration's setup files.

```
Config flow could not be loaded: {"message":"Invalid handler specified"}
```

This error is typically caused by one of two issues:

### Solution 1: Deploy the Latest Code

The most common cause is that the files in your Home Assistant `custom_components/blupow` directory are outdated. This can happen if you've pulled new changes from the repository but haven't copied them over to Home Assistant.

**Action:** Run the deployment script again to ensure Home Assistant is using the latest version of the integration.

```bash
# Deploy to Home Assistant
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Then, **restart Home Assistant** to apply the changes.

### Solution 2: Check for Syntax Errors

If deploying doesn't fix it, there might be a syntax error in one of the Python files, most likely `config_flow.py`.

The specific error `NameError: name 'callback' is not defined` was recently fixed. This was caused by a missing import in `config_flow.py`.

**Action:**
1.  Ensure you have the latest code from the repository.
2.  Manually inspect `config_flow.py` to ensure the following import is present at the top of the file:
    ```python
    from homeassistant.core import HomeAssistant, callback
    ```
3.  If you make any changes, re-run the deployment script and restart Home Assistant.

---

## Diagnostic Methodology (For Developers)

### How We Diagnosed the Container Issue

1. **Modified `deploy.sh`** to copy testing scripts into the container
2. **Fixed Python imports** to use absolute paths: `custom_components.blupow.*`
3. **Set PYTHONPATH** when running: `env PYTHONPATH=/config python3 script.py`
4. **Discovered AppArmor restrictions** through systematic testing

### Running Tests in Container

```bash
# Deploy integration with testing tools
./deploy.sh

# Run comprehensive testing suite
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/blupow_testing_suite.py

# Quick device check
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/quick_test.py
```

---

## When to Seek Help

Contact support if:
1. The diagnostic tool never finds the device, and you have tried all solutions in this guide.
2. The diagnostic tool finds the device, but connection tests always fail.
3. Connection works but data is incorrect.

---

## 1. Installation & Setup Issues

### **Issue: "Config flow could not be loaded" error in Home Assistant.**

- **Symptom:** When adding the BluPow integration, Home Assistant displays a "Config flow could not be loaded" error, and logs show messages like `Setup failed for custom integration 'blupow': Unable to import component`.
- **Cause:** This is often due to Home Assistant's security features, particularly AppArmor, restricting Bluetooth access for the Docker container.
- **Solution:**
    1.  **Disable AppArmor for the Home Assistant Container:** The most reliable solution is to disable AppArmor specifically for the Home Assistant Docker container.
        -   **Command:** `sudo docker run ... --security-opt apparmor=unconfined ...`
        -   Refer to the `CONTAINER_SETUP_GUIDE.md` for the full `docker run` command.
    2.  **Verify Bluetooth Passthrough:** Ensure your host's Bluetooth adapter is correctly passed through to the container.

### **Issue: `ModuleNotFoundError: No module named 'custom_components.blupow.backup'`**

- **Symptom:** Home Assistant fails to start, and the logs show a `ModuleNotFoundError` for a `.backup` module.
- **Cause:** The `scripts/deploy.sh` script was creating backups inside the `custom_components` directory, which Home Assistant tries to load as a separate integration.
- **Solution:**
    1.  Update the `deploy.sh` script to the latest version. The backup location has been moved outside of the `custom_components` directory.
    2.  Manually remove any `blupow.backup.*` directories from your `/config/custom_components/` folder within the Home Assistant container or mapped volume.

---

## 2. Device Connectivity & Data Issues

### **Issue: Device Acknowledges Command but Sends No Data (Modbus Exception Code 5)**

- **Symptom:** The integration connects to the Renogy device, and logs indicate a command is sent. However, the only response received is a short byte array like `ff8305e0c3`. No data is parsed, and sensors do not update.
- **Analysis:** The response `ff8305e0c3` is a Modbus RTU Exception Frame.
    - `ff`: The broadcast address, indicating the response is from the device.
    - `83`: This is the function code `03` (Read Holding Registers) with the most significant bit set (`0x80 + 0x03`), which signals an exception.
    - `05`: This is the Exception Code, which means "Acknowledge". The device has accepted the request and is processing it, but it is not ready to respond with data. This can be misleading, as it often indicates a "busy" state or an issue with the command format.
- **Cause:** The Renogy device requires commands to be addressed to its specific **Modbus Device ID**, even in a single-device setup. Using the broadcast address (`0xFF` or `255`) causes the device to acknowledge the request but not return a data payload.
- **Solution:**
    1.  **Use a Specific Device ID:** The `blupow_client` has been updated to use a default device ID of `1`.
    2.  **Future Enhancement:** In upcoming versions, you will be able to configure this Device ID in the integration's setup wizard. Most Renogy devices use a default ID of `1`, `16`, or `17`. If you continue to have issues, you may need to find the specific ID for your device.

### **Issue: No Renogy devices are discovered.**

- **Symptom:** The integration fails to find your Renogy device, even though it is powered on and within range.

This guide provides solutions to common issues encountered during the setup and operation of the BluPow integration. 