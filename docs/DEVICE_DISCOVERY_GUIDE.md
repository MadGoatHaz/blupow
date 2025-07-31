# BluPow Device Discovery

Device discovery is a core feature of the BluPow integration, designed to make setup as simple as possible. This document explains how it works.

## Discovery within the User Interface

The primary method for device discovery is handled directly within the Home Assistant user interface during the integration setup process.

### How it Works:

1.  When you add the BluPow integration for the first time, you are presented with a menu.
2.  If you select **"Auto Discover Devices"**, the Home Assistant integration initiates a Bluetooth Low Energy (BLE) scan with a 15-second timeout and up to 3 retry attempts if no devices are found initially.
3.  This scan looks for nearby devices that are broadcasting names commonly associated with Renogy products (e.g., containing "Renogy" or "BT-TH").
4.  A list of these discovered devices is then presented to you in a dropdown menu.
5.  When you select a device and confirm its type, the integration sends an `add_device` command to the BluPow Gateway via MQTT.

This UI-driven approach provides immediate feedback and allows for a simple, one-click setup for most users.

## MQTT Discovery

The second type of discovery is **MQTT Discovery**, which is a Home Assistant standard. This is how sensor entities are automatically created.

### How it Works:

1.  After a device has been added to the BluPow Gateway (either through auto-discovery or manual entry in the UI), the gateway will connect to it and poll it for data.
2.  The gateway then determines all the available sensors for that device based on its type.
3.  For each sensor, the gateway publishes a special "config" message to a specific MQTT topic. For example:
    `homeassistant/sensor/blupow_D8B673BF4F75_battery_voltage/config`
4.  This config message is a JSON payload containing all the information Home Assistant needs to create the entity, such as its name (`Battery Voltage`), unit of measurement (`V`), device class (`voltage`), and the state topic to listen on for value updates.
5.  Home Assistant's main MQTT integration is always listening for these messages. When it sees a new config payload, it automatically creates the corresponding sensor entity in the device registry.

This process means that the `custom_components/blupow` integration **does not create any entities itself**. It only provides the UI to tell the gateway *what* to monitor. The gateway and the standard Home Assistant MQTT integration handle the rest.

## Supported Device Types

### 1. INVERTER DEVICES
**Example**: RIV1230RCH-SPS (Built-in BLE)
- **MAC Address Pattern**: D8:B6:73:BF:4F:75
- **Device ID**: 32 (standard for inverters)
- **Primary Function**: AC power conversion and battery management
- **Key Characteristics**:
  - AC Input/Output monitoring
  - Battery voltage and charging status
  - Load power measurement
  - Minimal solar data (pass-through only)
  - Temperature monitoring

### 2. CHARGE CONTROLLER DEVICES  
**Example**: RNG-CTRL-RVR40 (Rover/Wanderer Series)
- **MAC Address Pattern**: C4:D3:6A:66:7E:D4
- **Device ID**: 96/97 (standard for controllers)
- **Primary Function**: Solar MPPT charging and battery management
- **Key Characteristics**:
  - Solar panel voltage/current/power monitoring
  - Battery charging optimization
  - Daily/total generation statistics
  - Controller temperature monitoring
  - NO AC input/output capabilities

## Device Data Structure Differences

### INVERTER DATA STRUCTURE (RIV1230RCH-SPS)
```python
{
    'model': 'RIV1230RCH-SPS',
    'device_id': 32,
    'input_voltage': 124.9,      # AC Input Voltage
    'input_current': 2.2,        # AC Input Current  
    'input_frequency': 59.97,    # AC Input Frequency
    'output_voltage': 124.9,     # AC Output Voltage
    'output_current': 1.19,      # AC Output Current
    'output_frequency': 59.97,   # AC Output Frequency
    'battery_voltage': 14.4,     # Battery Voltage
    'battery_percentage': 100,   # Battery SOC
    'charging_current': 0.7,     # Battery Charging Current
    'charging_status': 'deactivated',  # Charging Mode
    'charging_power': 10,        # Charging Power
    'load_active_power': 108,    # AC Load Power
    'load_apparent_power': 150,  # AC Apparent Power
    'load_current': 1.2,         # Load Current
    'load_percentage': 5,        # Load Percentage
    'line_charging_current': 0.0, # Line Charging Current
    'solar_voltage': 0.0,        # Solar Pass-through (minimal)
    'solar_current': 0.0,        # Solar Pass-through (minimal)
    'solar_power': 0,            # Solar Pass-through (minimal)
    'temperature': 30.0          # Inverter Temperature
}
```

### CHARGE CONTROLLER DATA STRUCTURE (RNG-CTRL-RVR40)
```python
{
    'model': 'RNG-CTRL-RVR40',
    'device_id': 96,
    'battery_voltage': 13.2,           # Battery Voltage
    'battery_percentage': 85,          # Battery SOC
    'charging_current': 8.5,           # Solar Charging Current
    'charging_status': 'bulk_charge',  # MPPT Charging Mode
    'charging_power': 112,             # Solar Charging Power
    'pv_voltage': 21.8,                # Solar Panel Voltage
    'pv_current': 5.1,                 # Solar Panel Current
    'pv_power': 112,                   # Solar Panel Power
    'controller_temperature': 25,      # Controller Temperature
    'daily_power_generation': 2.8,     # Daily kWh Generated
    'total_power_generation': 1247.5,  # Total kWh Generated
    'max_power_today': 125,            # Peak Power Today
    'daily_charge_ah': 45,             # Daily Amp Hours
    'charging_amp_hours_today': 45,    # Charging Amp Hours Today
    'load_current': 2.5,               # DC Load Current (if connected)
    'load_percentage': 15,             # DC Load Percentage
    # NO AC INPUT/OUTPUT FIELDS
    'input_voltage': 0,                # Controllers don't have AC input
    'input_current': 0,
    'output_voltage': 0,               # Controllers don't have AC output
    'output_current': 0
}
```

## Device Identification Logic

### MAC Address to Device Type Mapping
```python
DEVICE_TYPE_MAP = {
    "D8:B6:73:BF:4F:75": {
        "type": "INVERTER",
        "model": "RIV1230RCH-SPS", 
        "device_id": 32,
        "capabilities": ["AC_INPUT", "AC_OUTPUT", "BATTERY", "MINIMAL_SOLAR"]
    },
    "C4:D3:6A:66:7E:D4": {
        "type": "CHARGE_CONTROLLER",
        "model": "RNG-CTRL-RVR40",
        "device_id": 96,
        "capabilities": ["SOLAR_MPPT", "BATTERY", "DC_LOAD", "GENERATION_STATS"]
    }
}
```

### Device Capability Matrix
| Feature | Inverter (RIV1230RCH-SPS) | Controller (RNG-CTRL-RVR40) |
|---------|---------------------------|------------------------------|
| AC Input Monitoring | ✅ Primary Function | ❌ Not Available |
| AC Output Monitoring | ✅ Primary Function | ❌ Not Available |
| Solar MPPT | ❌ Pass-through Only | ✅ Primary Function |
| Battery Management | ✅ Charging/Monitoring | ✅ MPPT Charging |
| Load Monitoring | ✅ AC Load Power | ✅ DC Load Current |
| Generation Statistics | ❌ Limited | ✅ Daily/Total kWh |
| Temperature Monitoring | ✅ Inverter Temp | ✅ Controller Temp |

## Multi-Device Setup Methodology

### 1. Device Discovery Process
```python
# Automatic device type detection based on MAC address
def identify_device_type(mac_address: str) -> dict:
    if mac_address == "D8:B6:73:BF:4F:75":
        return DEVICE_TYPE_MAP["D8:B6:73:BF:4F:75"]
    elif mac_address == "C4:D3:6A:66:7E:D4":
        return DEVICE_TYPE_MAP["C4:D3:6A:66:7E:D4"]
    else:
        return {"type": "UNKNOWN", "model": "Unknown Device"}
```

### 2. Sensor Entity Mapping
```python
# Each device type gets different sensors in Home Assistant
INVERTER_SENSORS = [
    "input_voltage", "input_current", "input_frequency",
    "output_voltage", "output_current", "output_frequency", 
    "load_active_power", "load_apparent_power", "load_percentage",
    "battery_voltage", "battery_percentage", "charging_current",
    "temperature"
]

CONTROLLER_SENSORS = [
    "pv_voltage", "pv_current", "pv_power",
    "battery_voltage", "battery_percentage", "charging_current",
    "daily_power_generation", "total_power_generation",
    "controller_temperature", "charging_status"
]
```

### 3. Polling Strategy Differences
- **Inverters**: Real-time AC monitoring, frequent battery updates
- **Controllers**: Solar generation focus, daily statistics, MPPT optimization

## Critical Implementation Notes

### ⚠️ DEVICE CONFUSION PREVENTION
1. **Never mix device data structures** - Inverters and controllers have completely different sensor sets
2. **Maintain unique device IDs** - Use proper device_id values (32 for inverters, 96/97 for controllers)
3. **Respect device capabilities** - Don't request AC data from controllers or detailed solar data from inverters
4. **Use proper naming conventions** - Device names should clearly indicate type and model

### ✅ WORKING DEVICE PRESERVATION
- **D8:B6:73:BF:4F:75 (RIV1230RCH-SPS)**: This device is currently working and must maintain its exact data structure
- **Device ID 32**: Standard for Renogy inverters
- **AC Focus**: This device's primary function is AC power management

### 🔧 NEW DEVICE INTEGRATION
- **C4:D3:6A:66:7E:D4 (RNG-CTRL-RVR40)**: New charge controller with solar MPPT focus
- **Device ID 96/97**: Standard for Renogy charge controllers  
- **Solar Focus**: This device's primary function is solar power optimization

## Home Assistant Entity Organization

### Device 1: BluPow Inverter (D8:B6:73:BF:4F:75)
```yaml
Device Name: "BluPow RIV1230RCH-SPS Inverter"
Entities: 22 sensors
Primary Sensors:
  - sensor.blupow_inverter_ac_input_voltage
  - sensor.blupow_inverter_ac_output_power  
  - sensor.blupow_inverter_battery_voltage
  - sensor.blupow_inverter_load_percentage
```

### Device 2: BluPow Controller (C4:D3:6A:66:7E:D4)  
```yaml
Device Name: "BluPow RNG-CTRL-RVR40 Controller"
Entities: 22 sensors
Primary Sensors:
  - sensor.blupow_controller_solar_power
  - sensor.blupow_controller_battery_voltage
  - sensor.blupow_controller_daily_generation
  - sensor.blupow_controller_charging_current
```

## Troubleshooting Multi-Device Issues

### Common Problems:
1. **Device Type Confusion**: Check MAC address mapping
2. **Missing Sensors**: Verify device capabilities matrix
3. **Data Conflicts**: Ensure unique device IDs
4. **Polling Errors**: Check device-specific communication protocols

### Verification Commands:
```bash
# Check device identification
python3 scripts/multi_device_investigation.py

# Verify sensor mapping  
python3 scripts/device_configuration_manager.py

# Test individual device communication
python3 scripts/direct_device_test.py --mac D8:B6:73:BF:4F:75
python3 scripts/direct_device_test.py --mac C4:D3:6A:66:7E:D4
```

## References
- [Renogy BT Library](https://github.com/cyrils/renogy-bt) - Official device communication protocols
- [Device Compatibility Matrix](https://github.com/cyrils/renogy-bt#compatibility) - Supported device types
- [Home Assistant Integration Guide](../IMPLEMENTATION_GUIDE.md) - HA-specific setup instructions 