# BluPow Testing Guide

## Overview

This guide covers the comprehensive testing systems now integrated into BluPow, based on **cyrils/renogy-bt** patterns and protocols. These tools help you discover, test, and optimize your Renogy device connections.

## Quick Start

### For New Installations

1. **Quick Setup Assistant** (Recommended for beginners):
   ```bash
   python3 device_discovery_system.py
   ```
   Select option 5 (Quick Setup Assistant)

2. **Current Device Diagnostics** (If you have connection issues):
   ```bash
   python3 device_wake_system.py
   ```

## Testing Systems

### 1. Device Discovery System (`device_discovery_system.py`)

**Purpose**: Comprehensive device discovery using Cyril's renogy-bt patterns

**Features**:
- Automatically identifies Renogy devices by name patterns and UUIDs
- Tests connectivity and signal strength
- Provides hardware recommendations and MAC address selection
- Generates Home Assistant configuration suggestions

**Usage**:
```bash
python3 device_discovery_system.py
```

**What it detects**:
- **Charge Controllers**: BT-TH-*, ROVER*, WANDERER*, ADVENTURER*, RNG-CTRL*
- **Inverters**: BTRIC*, RIV*
- **Batteries**: RBT*, BATTERY*
- **DC Chargers**: RBC*, DCC*

**Output**: 
- Device compatibility scores (0-100)
- Signal strength analysis
- Connection test results
- Bluetooth proxy recommendations
- Home Assistant setup instructions

### 2. Device Wake System (`device_wake_system.py`)

**Purpose**: Specialized wake-up testing for "sleeping" devices

**Features**:
- Multiple wake-up strategies for power-saving devices
- Continuous monitoring for intermittent devices
- Bluetooth proxy optimization testing
- Deep sleep detection and handling

**Usage**:
```bash
python3 device_wake_system.py
```

**Test Modes**:
1. **Quick test** (~5 minutes) - All strategies
2. **Extended monitoring** (15 minutes) - Continuous scan
3. **Full comprehensive test** - All strategies + monitoring

**Wake Strategies**:
- **Burst Wake**: Rapid consecutive scans
- **Deep Sleep Wake**: Extended monitoring with wake signals
- **Proxy Assisted**: Testing through different Bluetooth proxies

## Device Identification Patterns

Based on **cyrils/renogy-bt** research:

### Supported Device Types

| Device Type | Name Patterns | Typical Models | Priority |
|-------------|---------------|----------------|----------|
| **Charge Controller** | `BT-TH-*`, `ROVER*`, `WANDERER*`, `ADVENTURER*`, `RNG-CTRL*` | RNG-CTRL-RVR40, ROVER-20A, ROVER-40A | High |
| **Inverter** | `BTRIC*`, `RIV*` | RIV1230RCH-SPS, RIV4835CSH1S | Medium |
| **Battery** | `RBT*`, `BATTERY*` | RBT100LFP12S-G, RBT100LFP12-BT | Medium |
| **DC Charger** | `RBC*`, `DCC*` | RBC50D1S-G1, DCC30S, DCC50S | Low |

### Bluetooth UUIDs (from Cyril's patterns)

- **Primary Service**: `0000ffd0-0000-1000-8000-00805f9b34fb`
- **RX Service**: `0000fff0-0000-1000-8000-00805f9b34fb`
- **TX Characteristic**: `0000ffd1-0000-1000-8000-00805f9b34fb`
- **RX Characteristic**: `0000fff1-0000-1000-8000-00805f9b34fb`
- **Manufacturer ID**: `0x7DE0`

## Bluetooth Proxy Optimization

### Known Proxies (Your Setup)

| Proxy Name | IP Address | Status | Signal Improvement |
|------------|------------|--------|--------------------|
| esp32-bluetooth-proxy-2105e4 | 192.168.51.151 | Active | +10 dB (tested) |
| proxy-2 | 192.168.51.207 | Available | TBD |
| proxy-3 | 192.168.51.109 | Available | TBD |

### Proxy Testing

The systems automatically test connectivity through different proxies to recommend the best option for your setup.

## Troubleshooting Your Current Device

### Device: BTRIC134000035 (D8:B6:73:BF:4F:75)

Based on your logs showing "device not found":

1. **Run Wake-Up Testing**:
   ```bash
   python3 device_wake_system.py
   ```
   Choose option 1 (Quick test) or 3 (Full comprehensive)

2. **Common Causes**:
   - Device in power-saving mode
   - Connected to Renogy mobile app
   - Bluetooth interference
   - Device too far from Home Assistant

3. **Solutions**:
   - Try during active charging periods
   - Disconnect Renogy mobile app
   - Move Bluetooth proxy closer
   - Power cycle the device

## Integration with Home Assistant

### Enhanced Configuration Flow

The updated configuration flow now includes:

1. **Manual Entry** (traditional method)
2. **Automatic Discovery** (new feature)
   - Scans for devices using Cyril's patterns
   - Tests connectivity
   - Ranks devices by compatibility
   - Provides signal strength info

### Setup Process

1. **In Home Assistant**:
   - Go to Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search for "BluPow"
   - Choose "Use automatic device discovery" OR enter MAC manually

2. **With Discovery**:
   - System scans for 15 seconds
   - Shows ranked list of compatible devices
   - Displays connection status and signal strength
   - Select best device from recommendations

## File Outputs

### Discovery Results
- `blupow_discovery_results.json` - Detailed device information
- Includes device types, signal strengths, compatibility scores

### Wake Testing Results
- `device_wake_results.json` - Wake strategy test results
- Shows successful detection methods and timing

### Comprehensive Testing
- `blupow_test_results.json` - Complete test suite results
- Combined analysis from all testing systems

## Best Practices

### 1. Device Detection
- Run discovery during device active periods (charging/load)
- Ensure device isn't connected to mobile apps
- Test multiple times if device intermittent

### 2. Signal Optimization
- Use discovery system to identify best MAC address
- Consider Bluetooth proxy placement
- Monitor signal strength trends

### 3. Connection Reliability
- Test wake-up strategies for problematic devices
- Configure appropriate update intervals
- Enable diagnostic logging if needed

## Command Reference

### Quick Commands

```bash
# Quick device discovery (15 seconds)
python3 device_discovery_system.py

# Wake up sleeping device
python3 device_wake_system.py

# Test current device connectivity
python3 device_wake_system.py
# Choose option 6 (Current Device Diagnostics)

# Full comprehensive analysis
python3 device_discovery_system.py
# Choose option 4 (Comprehensive Analysis)
```

### For Your Specific Issue

Your device `D8:B6:73:BF:4F:75` is showing as offline. Try:

1. **Immediate diagnostics**:
   ```bash
   python3 device_wake_system.py
   ```
   Choose option 1 (Quick test)

2. **If still not found, extended monitoring**:
   ```bash
   python3 device_wake_system.py
   ```
   Choose option 2 (Extended monitoring)

## Advanced Usage

### Integration with Existing Tests

The new systems work alongside your existing test files:
- `simple_test.py` - Basic functionality
- `connection_test.py` - Connection diagnostics
- `proxy_test.py` - Proxy connectivity

### Customization

You can modify the device patterns in `device_discovery_system.py`:
```python
RENOGY_DEVICE_PATTERNS = {
    'charge_controller': {
        'patterns': ['BT-TH-', 'ROVER', 'WANDERER', 'ADVENTURER', 'RNG-CTRL'],
        # Add your specific patterns here
    }
}
```

## Next Steps

1. **Test your current setup**:
   ```bash
   python3 device_wake_system.py
   ```

2. **If device found, integrate with Home Assistant**:
   - Use enhanced configuration flow
   - Select device from discovery results

3. **If device still not found**:
   - Check device power and Bluetooth activation
   - Try different proxy positions
   - Consider device firmware updates

## Support

The testing systems provide detailed logs and recommendations. Check the output JSON files for complete diagnostic information.

For device-specific issues, the wake system provides targeted troubleshooting steps based on your exact device model and connection patterns. 