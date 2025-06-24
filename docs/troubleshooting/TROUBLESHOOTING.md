# BluPow Troubleshooting Guide

This guide is the definitive resource for diagnosing and resolving issues with the BluPow integration.

## Is It the Integration or the Connection?

**The most common source of issues is the Bluetooth (BLE) connection between the host machine and the device, NOT the integration code itself.** The BluPow integration is designed to be stable and handle connection errors gracefully. If your sensors show as "Unknown" or "Unavailable" in Home Assistant, it is almost always a symptom of an underlying connectivity problem.

---

## 🛠️ Step 1: Run the End-to-End Verification Script

Before anything else, run the `verify_connection.py` script from the project's root directory. This script bypasses Home Assistant and attempts to connect directly to your device. It is the single fastest way to diagnose your connection status.

```bash
python3 scripts/diagnostics/verify_connection.py
```

*   **If this script succeeds:** You will see a printout of your device's live data. This means the hardware and BLE connection are working. The issue is likely with Home Assistant's configuration or the MQTT broker.
*   **If this script fails:** The problem is with the Bluetooth connection itself. Proceed to the troubleshooting steps below.

---

## 🚨 Problem: Connection Failures & "Unavailable" Sensors

If the verification script fails or your sensors are unavailable in Home Assistant, work through these solutions in order.

### Solution 1: The Inverter Power Cycle (90% Success Rate)

Renogy devices, especially inverters, can enter a deep sleep state where their Bluetooth module becomes unresponsive. A hard reset is the most common fix.

1.  **Power Down**: Completely power off the device.
2.  **Wait**: Leave it off for at least 60 seconds to ensure a full reset.
3.  **Power Up**: Turn the device back on.
4.  **Wait Again**: Allow 2 minutes for the device's systems to fully initialize before attempting to connect.
5.  **Re-run Verification**: Execute the verification script again.

### Solution 2: Container & Host Bluetooth Issues

If the gateway is running in a Docker container, security policies (like AppArmor) are the next most common cause of connection failure.

#### How to Diagnose
Check your logs for specific permission denied errors.

```bash
# Check Home Assistant logs for D-Bus errors
docker logs homeassistant | grep -i "dbus"

# Check system logs for AppArmor denials
sudo dmesg | grep -i "apparmor" | grep -i "denied"
```
If you see errors like `[org.freedesktop.DBus.Error.AccessDenied]` or `apparmor="DENIED"`, you have a container security issue.

#### How to Fix (Choose One)

These solutions modify the `docker-compose.yml` file for your Home Assistant container.

1.  **Privileged Mode (Easy, Less Secure)**: Gives the container full access to all host devices.
    ```yaml
    services:
      homeassistant:
        # ...
        privileged: true
        network_mode: host
        volumes:
          - /path/to/your/config:/config
          - /run/dbus:/run/dbus:ro
    ```
2.  **Specific Device Access (Recommended Balance)**: Grants access only to the necessary Bluetooth hardware.
    ```yaml
    services:
      homeassistant:
        # ...
        network_mode: host
        cap_add:
          - NET_ADMIN
          - NET_RAW
        devices:
          - /dev/hci0:/dev/hci0 # Verify path of your BT adapter
        volumes:
          - /path/to/your/config:/config
          - /run/dbus:/run/dbus:ro
    ```
3.  **Custom AppArmor Profile (Most Secure)**: This involves creating a custom security profile to grant the container the exact permissions it needs. For full instructions, see the original guide content in the project's `git` history.

After applying a fix, restart the container: `docker-compose up -d --force-recreate homeassistant`.

### Solution 3: Check for Competing Connections
Ensure your device is not actively connected to another application, such as the Renogy DC Home app on a phone or tablet. Bluetooth devices typically only allow one connection at a time.

---

## 🏗️ Legacy Issue: `already_configured` Error

**Status**: ✅ **RESOLVED**

In past versions, an `already_configured` error could occur when adding the integration. This was caused by orphaned configuration entries. This has been permanently fixed in the current version and should no longer occur.

By following this guide, you should be able to resolve most issues and get your 22 inverter sensors reporting live data into Home Assistant. 