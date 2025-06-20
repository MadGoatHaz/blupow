# BluPow Integration - Troubleshooting Guide

This guide helps you resolve common issues with the BluPow integration. The integration code itself is stable and production-ready; most issues that arise are related to the Bluetooth connection between your Home Assistant device and the Renogy inverter.

## ✅ Step 1: Run the Verification Script

Before anything else, run the `verify_connection.py` script. It's the fastest way to diagnose your connection status.

```bash
# From the project root directory
python3 scripts/verify_connection.py
```
The script's output will tell you if you have a connection problem or if the issue lies elsewhere.

## 🚨 Common Problem: Connection Failures

If the verification script fails, you'll likely see one of these errors:
- `Failed to connect to the inverter.`
- `Connected to the inverter, but failed to read data.`
- `Error ESP_GATT_CONN_FAIL_ESTABLISH` in Home Assistant logs.

**Translation:** Your Home Assistant machine can see the inverter, but the inverter is refusing the connection.

### The Most Common Cause
The Renogy inverter's Bluetooth module often enters a deep sleep mode after a period of inactivity and won't accept new connections until it's reset.

### The Solution (90% Success Rate)
A hard reset of the inverter will almost always solve this issue.
1.  **Power Down:** Completely power off the Renogy RIV1230RCH-SPS inverter.
2.  **Wait:** Leave it powered off for at least 60 seconds to ensure all capacitors are discharged.
3.  **Power Up:** Turn the inverter back on.
4.  **Wait Again:** Allow 2 minutes for the inverter's systems and Bluetooth module to fully initialize.
5.  **Re-run Verification:** Execute `python3 scripts/verify_connection.py` again.

## 📊 Symptom: Sensors Show "Unavailable" in Home Assistant

This is the **expected and correct behavior** when Home Assistant cannot retrieve data from the inverter. It means the BluPow integration is working perfectly and handling the connection issue gracefully.

**Do not try to "fix" the integration.** The solution is to fix the underlying Bluetooth connection by following the steps above. Once `verify_connection.py` succeeds, your sensors will automatically start populating in Home Assistant.

## 🛠️ Advanced Troubleshooting

If a power cycle doesn't resolve the issue, consult the **[Bluetooth Connection Guide](BLUETOOTH_CONNECTION_GUIDE.md)** for more advanced steps, including:
- Checking for competing Bluetooth connections (e.g., the Renogy app on a phone).
- Verifying Bluetooth signal strength and range.
- Using system-level tools to debug the Bluetooth adapter.

## 🏗️ Legacy Issue: `already_configured` Error

**Status:** ✅ **RESOLVED**

In the past, you might have seen an `already_configured` error when trying to add the integration. This was caused by orphaned configuration entries during the project's "inverter discovery" phase.

**Solution:** This has been permanently fixed. However, if you ever suspect an issue with your configuration, you can run the cleanup script.
```bash
# This is for historical reference and should not be needed now.
python3 scripts/cleanup_integration.py
```

By following this guide, you should be able to resolve most issues and get your 22 inverter sensors reporting live data into Home Assistant. 