# Verification Guide

This guide will walk you through the final steps to get your BluPow inverter integration running and see live data in Home Assistant. The codebase is now fully corrected for your Renogy inverter.

## 1. Run the Verification Script

A script has been created to perform a final end-to-end test. This script will:
1.  Connect to your inverter.
2.  Read all 22 data points.
3.  Display the live data in your terminal.
4.  Confirm that the integration is ready for Home Assistant.

To run the script, execute the following command from your project's root directory:

```bash
python3 scripts/verify_connection.py
```

## 2. Expected Output

If the connection is successful, you will see a real-time printout of your inverter's data, similar to this:

```
📊 INVERTER DATA SUMMARY:
------------------------------
Model: RIV1230RCH-SPS
Device ID: 255
Input Voltage: 124.9V
Output Voltage: 124.9V
Input Frequency: 60.0Hz
Output Frequency: 60.0Hz
Battery Voltage: 14.4V
Battery SOC: 100%
Load Power: 108.0W
Temperature: 30.0°C
Solar Voltage: 0.0V
Solar Current: 0.0A
```

## 3. Next Steps in Home Assistant

Once the verification script confirms that you are receiving live data, you can proceed with adding the integration in Home Assistant:

1.  **Go to Home Assistant**: Settings → Devices & Services
2.  **Add Integration**: Click "Add Integration"
3.  **Search BluPow**: The integration should now appear.
4.  **Configure Device**: Use MAC address `D8:B6:73:BF:4F:75`
5.  **Verify Sensors**: All 22 inverter sensors should appear and populate with live data.

This completes the process. Your inverter stats will now be pulled and updated in Home Assistant. 