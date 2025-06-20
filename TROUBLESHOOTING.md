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

We have a built-in diagnostic tool to help you. Run it from your Home Assistant's terminal or a terminal with access to the codebase:

```bash
python3 blupow_testing_suite.py
```

When prompted, select option `6` for **Current Device Diagnostics**.

The tool will tell you if the device is visible and if it can connect.

### ⚙️ Step 2: Common Causes & Solutions

If the diagnostic tool fails, here are the likely reasons why:

| Cause                                   | Solution                                                                                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
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

## When to Seek Help

Contact support if:
1. The diagnostic tool never finds the device, and you have tried all solutions in this guide.
2. The diagnostic tool finds the device, but connection tests always fail.
3. Connection works but data is incorrect. 