# BluPow Bluetooth Connection Troubleshooting Guide

## Current Issue Summary

The BluPow integration is **working correctly** - all 22 sensors are loading successfully in Home Assistant. However, the Bluetooth connection to the Renogy device (MAC: `D8:B6:73:BF:4F:75`) is failing with these errors:

- `No backend with an available connection slot that can reach address D8:B6:73:BF:4F:75 was found`
- `Error ESP_GATT_CONN_FAIL_ESTABLISH while connecting: Connection failed to establish`
- `Timeout waiting for connect response while connecting to D8:B6:73:BF:4F:75`

## Integration Status ✅

**The good news**: The integration itself is working perfectly:
- All 22 inverter sensors are imported
- Integration loads without errors
- Sensors show as "unavailable" (correct behavior when device is disconnected)
- No code issues or crashes

## Troubleshooting Steps

### 1. Run Diagnostic Scripts

First, run our diagnostic tools to identify the exact issue:

```bash
# From the Home Assistant machine
cd /home/madgoat/opt/Projects/blupow

# Check system-level Bluetooth
python3 scripts/bluetooth_system_check.py

# Check device-specific connection
python3 scripts/bluetooth_diagnostic.py
```

### 2. Check Device Status

#### Physical Device Checks:
- ✅ **Power**: Ensure the Renogy RIV1230RCH-SPS inverter is powered on
- ✅ **Range**: Move within 3-5 meters of the device
- ✅ **Other Connections**: Disconnect from Renogy mobile app if connected
- ✅ **Reset**: Try power cycling the inverter (turn off, wait 30 seconds, turn on)

#### Device Information:
- **Device Name**: BTRIC134000035 (Bluetooth Remote for Inverter Charger)
- **MAC Address**: D8:B6:73:BF:4F:75
- **Device Type**: Renogy RIV1230RCH-SPS Pure Sine Wave Inverter Charger

### 3. Home Assistant Environment Checks

#### If Running Home Assistant OS (Supervised):
```bash
# Check if Bluetooth integration is enabled
ha core logs | grep -i bluetooth

# Check Bluetooth adapter status
bluetoothctl list
```

#### If Running in Docker Container:
```bash
# Check if Bluetooth is passed through
docker exec homeassistant ls -la /dev/hci*

# Check container privileges
docker inspect homeassistant | grep -i privileged
```

### 4. Common Solutions

#### Solution 1: Enable Bluetooth Integration
1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Bluetooth** and add it
4. Restart Home Assistant

#### Solution 2: Container Bluetooth Configuration
If running in Docker, you may need to configure Bluetooth access:

```yaml
# docker-compose.yml
services:
  homeassistant:
    # ... other config ...
    privileged: true
    devices:
      - /dev/hci0:/dev/hci0
    volumes:
      - /run/dbus:/run/dbus:ro
```

#### Solution 3: Bluetooth Proxy Setup
For supervised installations, consider using an ESP32 Bluetooth proxy:
1. Flash an ESP32 with ESPHome Bluetooth proxy firmware
2. Add it to Home Assistant
3. Place it near the Renogy device

### 5. Manual Connection Test

Try connecting manually to verify the device is working:

```bash
# Scan for the device
bluetoothctl scan on
# Wait for BTRIC134000035 to appear

# Try to connect
bluetoothctl connect D8:B6:73:BF:4F:75
```

### 6. Check Renogy Device Settings

Some Renogy devices have Bluetooth settings that need to be enabled:
1. Check if there's a Bluetooth setting on the device display
2. Ensure Bluetooth is enabled in device settings
3. Some devices have a pairing timeout - may need to re-enable

## Error Analysis

### "No backend with an available connection slot"
- **Cause**: Bluetooth adapter not accessible to Home Assistant
- **Solution**: Check Bluetooth integration is enabled, verify container permissions

### "ESP_GATT_CONN_FAIL_ESTABLISH"
- **Cause**: Device is busy, out of range, or powered off
- **Solution**: Ensure device is on, in range, and not connected elsewhere

### "Timeout waiting for connect response"
- **Cause**: Device not responding to connection requests
- **Solution**: Check device power, restart device, verify Bluetooth is enabled

## Verification Steps

Once connection is working, you should see:

1. **In Home Assistant logs**:
   ```
   [custom_components.blupow.blupow_client] ✅ Connected to Renogy device
   [custom_components.blupow.coordinator] Received data: {'model': 'RIV1230RCH-SPS', ...}
   ```

2. **In Device Dashboard**:
   - All sensors showing real values instead of "Unavailable"
   - Connection status showing "Connected"
   - Live data updates every 30 seconds

3. **Expected Data Values**:
   - AC Input Voltage: ~120V (when grid connected)
   - AC Output Voltage: ~120V (when inverting)
   - Battery Percentage: 0-100%
   - Load Active Power: Current power consumption
   - Inverter Model: "RIV1230RCH-SPS"

## Advanced Troubleshooting

### Enable Debug Logging
Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.blupow: debug
    custom_components.blupow.blupow_client: debug
    custom_components.blupow.coordinator: debug
```

### Manual Bluetooth Reset
```bash
# Reset Bluetooth stack
sudo systemctl stop bluetooth
sudo systemctl start bluetooth

# Or reset specific adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

### Check for Interference
- Move away from WiFi routers, microwaves
- Try different times of day
- Check for other Bluetooth devices causing interference

## Next Steps

1. **Run the diagnostic scripts** to identify the specific issue
2. **Follow the solutions** based on your Home Assistant setup type
3. **Verify device status** and proximity
4. **Test manual connection** to confirm device is responsive
5. **Contact for support** if issues persist with diagnostic results

## Success Indicators

When working correctly, you'll see:
- All 22 sensors with real data (not "Unavailable")
- Regular log entries showing successful data updates
- Ability to use sensors in automations and energy dashboard
- Connection status showing "Connected" in device info

The integration is ready and waiting - we just need to establish the Bluetooth connection! 