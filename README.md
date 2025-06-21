<div align="center">

# BluPow - Renogy Device Integration for Home Assistant

</div>

<div align="center">

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![Project Maintenance][maintenance-shield]][maintenance-url]
[![GitHub Sponsors][sponsors-shield]][sponsors]
[![PayPal Donation][paypal-shield]][paypal]

</div>

**Professional Home Assistant integration for Renogy BluPow devices.**

Monitor your solar power system with real-time data, automated dashboards, and seamless Home Assistant integration.

</div>

<div align="center">
<img src="BluPow.png" alt="BluPow Integration" width="300"/>
</div>

## Features

• **Effortless Setup** - Add your device MAC address and start monitoring immediately  
• **Comprehensive Data** - Complete sensor coverage for inverters and charge controllers  
• **Reliable Operation** - Automatic reconnection and intelligent error handling  
• **Professional UI** - Clean sensors with proper device classes and units  
• **Energy Dashboard** - Native integration with Home Assistant's energy tracking  

---

## Quick Start

### HACS Installation (Recommended)
1. **Install HACS** if not already installed
2. **Add Repository** - Add this repository to HACS custom repositories  
3. **Search & Install** - Find "BluPow" in HACS and install
4. **Restart** Home Assistant
5. **Add Integration** - Go to Settings → Devices & Services → Add Integration → BluPow
6. **Configure** - Enter your device MAC address

### Manual Installation
1. **Download** this repository
2. **Copy Files** - Copy the `blupow` folder to `config/custom_components/`
3. **Restart** Home Assistant
4. **Add Integration** - Go to Settings → Devices & Services

---

## Supported Devices

This integration works with Renogy devices that use Bluetooth modules:

• **Inverters** - RIV1230RCH-SPS and similar models  
• **Charge Controllers** - RNG-CTRL-RVR40, Rover, Wanderer series  
• **Requirements** - Device must have BT-1 or BT-2 Bluetooth module

**Sensor Coverage:**
• **Inverters** - 17 sensors covering AC input/output, battery management, load monitoring
• **Controllers** - 20 sensors covering solar production, MPPT charging, energy statistics

Each device appears as a separate entity in Home Assistant with appropriate device classes for energy dashboard integration.

---

## Home Assistant Integration

### Device Organization
Each Renogy device appears as a distinct device in Home Assistant with:
• **Proper Identification** - Device model and hardware information
• **Logical Grouping** - Sensors organized by function
• **Consistent Naming** - Clear entity naming (`sensor.blupow_[device_type]_[sensor]`)

### Energy Dashboard Integration
Sensors automatically integrate with Home Assistant's energy dashboard:
• **Solar Production** - Daily and total energy generation
• **Battery Monitoring** - State of charge and power flow  
• **Load Tracking** - AC consumption and load management

### Automation Ready
All sensors include proper device classes enabling:
• **Energy Monitoring** - Automated energy tracking
• **Battery Alerts** - Low battery notifications
• **Load Management** - Solar production-based automation
• **System Integration** - Works with other Home Assistant energy devices

---

## Advanced Features

### Intelligent Data Management
The integration handles real-world solar system variations:

**Dynamic State Adaptation**: Automatically adjusts to day/night cycles, charging states, and load conditions without manual configuration.

**Connection Resilience**: Implements retry logic and automatic reconnection when Bluetooth connections are interrupted. No manual intervention required for temporary connectivity issues.

**Data Validation**: Filters invalid readings and prevents sensor state corruption. Maintains sensor availability during brief communication gaps.

### Device-Specific Optimization
**Inverter Focus**: Prioritizes AC monitoring, battery management, and load tracking. Handles grid-tie and off-grid operational modes.

**Controller Focus**: Emphasizes solar production monitoring, MPPT efficiency tracking, and charge algorithm status. Adapts to different battery types and charging profiles.

### Background Processing
**Non-Blocking Operation**: Data collection runs independently without affecting Home Assistant responsiveness.

**Efficient Polling**: Uses optimized 30-second intervals balancing data freshness with Bluetooth bandwidth conservation.

---

## Configuration

### Basic Setup
No YAML configuration required. The integration automatically:
• **Device Detection** - Identifies device type and configures appropriate sensors
• **Proper Classes** - Sets device classes and units of measurement  
• **Optimal Timing** - Establishes efficient update intervals
• **Connection Management** - Handles Bluetooth connectivity

### Optional Customization
```yaml
# configuration.yaml (optional)
blupow:
  update_interval: 30  # Update frequency in seconds
```

### Finding Your Device MAC Address
Use the built-in discovery script:
```bash
python3 scripts/blupow_device_discovery.py
```

Or check Home Assistant's Bluetooth integration for discovered devices.

---

## Troubleshooting

### Sensors Show "Unavailable"
**Check device power**: Ensure your Renogy device is powered on and within Bluetooth range.

**Restart integration**: Go to Settings → Devices & Services → BluPow → Configure → Reload.

**Verify MAC address**: Confirm the MAC address in your integration configuration matches your device.

### Device Not Found During Setup
**Enable Bluetooth**: Ensure Home Assistant's Bluetooth integration is enabled and working.

**Check range**: Move closer to the device during initial setup.

**Device discovery**: Use Settings → Devices & Services → Bluetooth to scan for nearby devices.

### Connection Drops Frequently
**Interference**: Check for other Bluetooth devices or WiFi interference near your setup.

**Power saving**: Some devices enter sleep mode. Try accessing the device with the Renogy app first to wake it up.

**Range**: Ensure stable Bluetooth range between Home Assistant and your device.

### Data Appears Incorrect
**Units**: Verify sensor units match your expectations (some values are scaled, e.g., voltage × 10).

**Device state**: Check if your device is in the expected operational state (charging, discharging, etc.).

**Comparison**: Compare readings with the official Renogy app to verify accuracy.

---

## Support

### Documentation
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development and contribution guidelines
- **[Technical Documentation](docs/)** - Complete technical reference

### Getting Help
- **[GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/MadGoatHaz/blupow/discussions)** - Community support and questions

---

## License & Attribution

This project is licensed under **GPL-3.0** in compliance with the [renogy-bt](https://github.com/cyrils/renogy-bt) library it's based on.

**Based on:** [renogy-bt by Cyril](https://github.com/cyrils/renogy-bt) (GPL-3.0)  
**Integration by:** [@MadGoatHaz](https://github.com/MadGoatHaz)

### Acknowledgments
- **[Cyril](https://github.com/cyrils)** for the foundational [renogy-bt](https://github.com/cyrils/renogy-bt) library
- **Renogy** for creating reliable solar equipment
- **Home Assistant** community for the platform and ecosystem
- **Contributors** who help improve this integration

---

## Support Development

If this integration has been useful for your solar monitoring setup:

- **[GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)** - Monthly sponsorship
- **[PayPal Donation](https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD)** - One-time donation

**Maintainer**: [@MadGoatHaz](https://github.com/MadGoatHaz)

---

<!-- Badges -->
[releases-shield]: https://img.shields.io/github/release/MadGoatHaz/blupow.svg?style=for-the-badge
[releases]: https://github.com/MadGoatHaz/blupow/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/MadGoatHaz/blupow.svg?style=for-the-badge  
[commits]: https://github.com/MadGoatHaz/blupow/commits/main
[license-shield]: https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-@MadGoatHaz-blue.svg?style=for-the-badge
[maintenance-url]: https://github.com/MadGoatHaz
[sponsors-shield]: https://img.shields.io/badge/GitHub-Sponsors-ff69b4.svg?style=for-the-badge
[sponsors]: https://github.com/sponsors/MadGoatHaz
[paypal-shield]: https://img.shields.io/badge/PayPal-Donate-blue.svg?style=for-the-badge
[paypal]: https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD 