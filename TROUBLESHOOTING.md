# BluPow Integration Troubleshooting Guide

## Current Issue Summary

**Problem**: BluPow sensors showing "Unknown" values and integration failing to connect.

**Root Cause**: The solar charger device (`C4:D3:6A:66:7E:D4` / `BT-TH-6A667ED4`) is **not discoverable** via Bluetooth scan.

## Diagnostic Results

✅ **Bluetooth adapter working**: System Bluetooth is functional  
✅ **Integration code working**: The integration starts up correctly  
✅ **Bluetooth scan working**: Can discover 15+ other devices  
❌ **Target device missing**: Solar charger not found in scan  

## Why This Happens

The error "No backend with an available connection slot" is misleading. The real issue is that Home Assistant finds the device address in its internal database (from when it was previously discovered), but when it tries to connect, the device is no longer advertising/discoverable.

## Troubleshooting Steps

### 1. Solar Charger Device Issues

**Check device power and status:**
- Ensure solar charger is powered ON
- Check if device has battery power or solar input
- Look for LED indicators showing the device is active
- Try powering the device off and on again

**Check device mode:**
- Some solar chargers need to be put in "pairing mode" 
- Check if there's a button combination to enable Bluetooth advertising
- Consult device manual for Bluetooth setup instructions

### 2. Range and Interference

**Distance check:**
- Move the solar charger within 5 meters of your Home Assistant device
- Ensure there are no thick walls or metal objects between devices
- Try moving to a different location

**Interference check:**
- Turn off other Bluetooth devices temporarily
- Check for WiFi interference (2.4GHz overlap)
- Move away from other electronics

### 3. Device Connection State

**Check if device is connected elsewhere:**
- Look for mobile apps that might be connected to the device
- Check if device is paired with a phone or tablet
- Disconnect from any other applications

### 4. Bluetooth System Reset

If device should be discoverable but isn't found:

```bash
# Reset Bluetooth adapter
sudo hciconfig hci0 reset

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Clear Bluetooth cache (if needed)
sudo rm -rf /var/lib/bluetooth/*/cache/
sudo systemctl restart bluetooth
```

### 5. Home Assistant Specific

**Clear device cache:**
1. Go to Settings → Devices & Services → Integrations
2. Find BluPow integration
3. Click "..." → Delete integration
4. Restart Home Assistant
5. Re-add the integration

**Check Bluetooth integration:**
1. Ensure Home Assistant Bluetooth integration is enabled
2. Check for conflicts with other Bluetooth integrations
3. Review Home Assistant logs for Bluetooth errors

## Testing Tools

### Quick Device Scan
Run this to check if your device is discoverable:

```bash
cd /path/to/blupow
python3 simple_test.py
```

### Manual Bluetooth Scan
```bash
# Command line scan
bluetoothctl scan on
# Wait 30 seconds, look for your device
# Press Ctrl+C to stop
```

### Check for Connection Conflicts
```bash
# See what's using Bluetooth
lsof | grep bluetooth
ps aux | grep blue
```

## Expected Behavior When Working

When the device is properly discoverable, you should see:
1. Device appears in scan as "BT-TH-6A667ED4" 
2. Connection succeeds
3. Services and characteristics are discovered
4. Data starts flowing to Home Assistant sensors

## Common Solar Charger Bluetooth Patterns

Many solar charge controllers:
- Only advertise when NOT connected to another device
- Have a "pairing window" that times out
- Need to be in a specific operating mode to enable Bluetooth
- Require manual activation of Bluetooth advertising

## Next Steps

1. **Primary focus**: Get the device discoverable again
   - Check device manual for Bluetooth activation
   - Try different power states
   - Look for pairing mode instructions

2. **If device becomes discoverable**: The integration should work immediately

3. **If still no luck**: Check if this is a compatible device or if firmware updates are needed

## Logs to Check

In Home Assistant logs, look for:
- `"Found BLE device: BT-TH-6A667ED4"` ← This means device was found
- `"No backend with an available connection slot"` ← This means device disappeared

## Device Information

- **Expected Name**: BT-TH-6A667ED4
- **MAC Address**: C4:D3:6A:66:7E:D4
- **Type**: Solar charge controller/battery monitor
- **Protocol**: Bluetooth Low Energy (BLE)

---

**Last Updated**: Based on diagnostic results from actual testing 