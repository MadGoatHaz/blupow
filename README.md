# 🔋 BluPow - Renogy Device Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![GitHub Sponsors][sponsors-shield]][sponsors]
[![PayPal Donation][paypal-shield]][paypal]

**The most comprehensive Home Assistant integration for Renogy BluPow devices! 🚀**

Transform your solar power system into a smart, monitored powerhouse with real-time data, beautiful dashboards, and intelligent automation possibilities.

<div align="center">
<img src="BluPow.png" alt="BluPow Integration" width="300"/>
</div>

## ✨ **What Makes BluPow Great?**

🎯 **Plug & Play**: Just add your device MAC address and you're monitoring immediately  
📊 **Rich Data**: 17+ sensors for inverters, 20+ for charge controllers  
🔄 **Rock Solid**: Built-in fallbacks, health monitoring, and automatic recovery  
🎨 **Beautiful UI**: Clean sensors with proper icons, units, and device classes  
🛠️ **Smart Tools**: Comprehensive scripts for deployment, testing, and maintenance  
⚡ **Real-Time**: 30-second updates keep you informed of every change  

---

## 🚀 **Quick Start**

### **Option 1: HACS Installation (Recommended)**
1. **Install HACS** if you haven't already
2. **Add this repository** to HACS custom repositories
3. **Search "BluPow"** in HACS and install
4. **Restart Home Assistant**
5. **Add Integration**: Settings → Devices & Services → Add Integration → BluPow
6. **Enter your device details** and enjoy!

### **Option 2: Manual Installation**
1. **Download** this repository
2. **Copy** the `blupow` folder to `config/custom_components/`
3. **Restart Home Assistant**
4. **Add Integration**: Settings → Devices & Services → Add Integration → BluPow

---

## 📊 **Supported Devices & Sensors**

### **🔌 RIV1230RCH-SPS Inverter** (`XX:XX:XX:XX:XX:XX`)
Perfect for monitoring your AC power system, battery management, and load consumption.

**17 Real-Time Sensors:**
| Sensor | Description | Example |
|--------|-------------|---------|
| 🔌 **AC Input Voltage** | Grid power voltage | 124.9 V |
| ⚡ **AC Input Current** | Grid power draw | 2.20 A |
| 📶 **AC Input Frequency** | Grid frequency | 59.97 Hz |
| 🔌 **AC Output Voltage** | Inverter output voltage | 124.9 V |
| ⚡ **AC Output Current** | Load current | 3.20 A |
| 📶 **AC Output Frequency** | Output frequency | 59.97 Hz |
| ⚡ **Load Power** | Active AC load | 400 W |
| 📊 **Load Apparent Power** | Total apparent load | 420 VA |
| 📈 **Load Percentage** | Inverter load % | 33% |
| 🔋 **Battery Voltage** | DC battery voltage | 14.40 V |
| ⚡ **Battery Current** | Charge/discharge current | +15.0 A |
| 📊 **Battery SOC** | State of charge | 95% |
| 🔄 **Charging Status** | Current charge mode | bulk_charge |
| ⚡ **Charging Power** | Battery charging power | 216 W |
| 🔌 **Line Charging Current** | AC charging current | 12.0 A |
| ☀️ **Solar Input** | Solar panels (if connected) | 0 W |
| 🌡️ **Temperature** | Inverter temperature | 35°C |

### **☀️ RNG-CTRL-RVR40 Controller** (`YY:YY:YY:YY:YY:YY`)
Ideal for monitoring solar production, MPPT charging, and DC load management.

**20 Real-Time Sensors:**
| Category | Sensors | Description |
|----------|---------|-------------|
| **☀️ Solar Production** | PV Voltage, Current, Power | Monitor solar panel performance |
| **🔋 Battery Management** | Voltage, Current, SOC, Temperature | Complete battery health tracking |
| **⚡ MPPT Charging** | Status, Power, Max Power Today | Advanced charge algorithm monitoring |
| **📊 Energy Statistics** | Daily/Total Generation & Consumption | Track your energy production history |
| **🔌 DC Load Control** | Load Voltage, Current, Power, Status | Monitor 12V DC loads |
| **🌡️ System Health** | Controller Temperature, Battery Type | System health and configuration |

---

## 🎨 **Beautiful Home Assistant Integration**

### **🏠 Device Cards**
Each device appears as a separate, properly identified device:
- **BluPow Inverter** (RIV1230RCH-SPS) - `XX:XX:XX:XX:XX:XX`
- **BluPow Solar Controller** (RNG-CTRL-RVR40) - `YY:YY:YY:YY:YY:YY`

### **📊 Smart Entity Naming**
```
sensor.blupow_inverter_battery_voltage      # 14.40 V
sensor.blupow_inverter_load_power           # 400 W
sensor.blupow_controller_pv_power           # 179 W
sensor.blupow_controller_battery_soc        # 95%
```

### **🎯 Proper Device Classes**
- ⚡ **Power sensors** → Energy dashboard integration
- 🔋 **Battery sensors** → Battery monitoring cards  
- 🌡️ **Temperature sensors** → Climate monitoring
- 📊 **Energy sensors** → Historical tracking

---

## 🛠️ **Advanced Features**

### **🔄 Dynamic State Management**
The integration intelligently adapts to real-world conditions:

**🌙 Night Mode (Inverter)**
- Battery discharging to power AC loads
- No solar input
- Grid input minimal/off

**☀️ Day Mode (Charging)**  
- Grid charging batteries
- AC passthrough active
- Solar charging (if connected)

**⚡ Peak Solar (Controller)**
- Maximum MPPT power tracking
- Bulk/absorption charging  
- High PV voltage/current

### **🛡️ Built-in Reliability**
- **🔄 Automatic Fallbacks**: Multiple data sources ensure continuous operation
- **💚 Health Monitoring**: Built-in performance tracking and reporting
- **🔧 Self-Recovery**: Automatic retry logic and connection management
- **📊 Data Validation**: Smart filtering prevents invalid sensor readings

### **🎯 Smart Availability Logic**
- **Simple & Reliable**: Available when data exists and coordinator succeeds
- **No False Unavailable**: Eliminates "unavailable" sensor states
- **Quick Recovery**: Fast restoration after temporary connection issues

---

## 🔧 **Configuration**

### **Basic Setup**
```yaml
# Home Assistant will automatically discover and configure sensors
# No manual YAML configuration required!
```

### **Optional: Custom Update Intervals**
```yaml
# In configuration.yaml (optional)
blupow:
  update_interval: 30  # seconds (default: 30)
```

### **Template Sensors (Optional Enhancement)**
Create calculated sensors for enhanced monitoring:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Solar Efficiency"
        unit_of_measurement: "%"
        state: >
          {% set pv_power = states('sensor.blupow_controller_pv_power') | float %}
          {% set max_power = states('sensor.blupow_controller_max_charging_power_today') | float %}
          {% if max_power > 0 %}
            {{ ((pv_power / max_power) * 100) | round(1) }}
          {% else %}
            0
          {% endif %}
        
      - name: "Battery Health"
        state: >
          {% set voltage = states('sensor.blupow_inverter_battery_voltage') | float %}
          {% set soc = states('sensor.blupow_inverter_battery_soc') | float %}
          {% if voltage > 13.0 and soc > 80 %}
            Excellent
          {% elif voltage > 12.5 and soc > 50 %}
            Good
          {% elif voltage > 12.0 and soc > 20 %}
            Fair
          {% else %}
            Needs Attention
          {% endif %}
```

---

## 📈 **Dashboard Examples**

### **🎯 Energy Overview Card**
```yaml
# ui-lovelace.yaml
type: entities
title: "BluPow Energy System"
entities:
  - sensor.blupow_controller_pv_power
  - sensor.blupow_inverter_load_power  
  - sensor.blupow_inverter_battery_voltage
  - sensor.blupow_inverter_battery_soc
  - sensor.blupow_controller_charging_status
```

### **📊 Power Flow Card**
```yaml
type: picture-elements
image: /local/solar_system_diagram.png
elements:
  - type: state-label
    entity: sensor.blupow_controller_pv_power
    top: 20%
    left: 20%
  - type: state-label  
    entity: sensor.blupow_inverter_battery_soc
    top: 50%
    left: 50%
  - type: state-label
    entity: sensor.blupow_inverter_load_power
    top: 80%
    left: 80%
```

### **⚡ Energy Dashboard Integration**
BluPow sensors automatically integrate with Home Assistant's Energy Dashboard:
- **Solar Production**: `sensor.blupow_controller_power_generation_today`
- **Battery Charge**: `sensor.blupow_inverter_charging_power`  
- **Home Consumption**: `sensor.blupow_inverter_load_power`

---

## 🚨 **Troubleshooting**

### **🔍 Quick Diagnosis**
```bash
# Check integration health
python3 scripts/quick_integration_test.py

# Comprehensive system test
python3 scripts/comprehensive_integration_test.py
```

### **❌ Common Issues & Solutions**

**Problem: Sensors show "Unavailable"**
```bash
# Solution: Deploy stability fixes
python3 deploy_production_stability.py
```

**Problem: Device not connecting**
```bash
# Solution: Test Bluetooth connectivity
python3 scripts/bluetooth_connection_fix.py
python3 scripts/direct_device_test.py
```

**Problem: Duplicate sensors**
```bash
# Solution: Clean up and re-add integration
python3 cleanup_duplicate_sensors.py
# Then re-add integration via HA UI
```

### **🔧 Advanced Diagnostics**
```bash
# Health monitoring
python3 scripts/health_monitor.py

# Complete diagnostics
python3 scripts/diagnostics.py

# Home Assistant integration recovery
python3 scripts/integration_recovery.py
```

---

## 🛠️ **Development & Contribution**

### **🧪 Testing Your Changes**
```bash
# Quick integration test
python3 scripts/quick_integration_test.py

# Full test suite
python3 scripts/comprehensive_integration_test.py

# Validate all components
python3 scripts/validate_integration.py
```

### **🚀 Deployment**
```bash
# Deploy to Home Assistant
python3 deploy_production_stability.py

# Deploy specific fixes
python3 scripts/deploy_production_fix.py
```

### **📁 Project Structure**
```
blupow/
├── 🔌 Core Integration
│   ├── __init__.py              # Integration setup
│   ├── manifest.json            # Integration manifest
│   ├── config_flow.py           # Configuration UI
│   ├── coordinator.py           # Data coordination
│   ├── sensor.py                # Sensor definitions
│   ├── blupow_client.py         # Device communication
│   └── const.py                 # Constants & sensors
├── 🛠️ Tools & Scripts
│   ├── scripts/                 # Deployment & testing tools
│   ├── deploy_*.py              # Deployment scripts
│   └── cleanup_*.py             # Maintenance scripts
├── 📚 Documentation
│   ├── docs/                    # Comprehensive guides
│   ├── README.md                # This file
│   └── SENSOR_FIX_SUMMARY.md    # Recent fixes
└── 🎨 Assets
    ├── brand/                   # HACS assets
    └── BluPow.png               # Integration logo
```

### **🤝 Contributing**
1. **Fork** the repository
2. **Create** a feature branch
3. **Test** your changes with the included tools
4. **Submit** a pull request

---

## 🆘 **Support**

### **📖 Documentation**
- **[Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - Deep dive into how it works
- **[Device Discovery Guide](docs/DEVICE_DISCOVERY_GUIDE.md)** - Finding your device MAC
- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)** - Advanced setup
- **[Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING.md)** - Common issues

### **🐛 Issues & Feature Requests**
- **[GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)** - Report bugs or request features
- **[Discussions](https://github.com/MadGoatHaz/blupow/discussions)** - Community support

### **💬 Community**
- **Home Assistant Community Forum** - [BluPow Integration Thread]
- **Discord** - Join the Home Assistant community

---



---

## 🙏 **Acknowledgments**

- **[Cyril](https://github.com/cyrils)** for the foundational [renogy-bt](https://github.com/cyrils/renogy-bt) library that makes this integration possible
- **Renogy** for creating excellent solar equipment
- **Home Assistant** community for the amazing platform
- **Contributors** who helped make this integration possible
- **Beta testers** who provided valuable feedback

## 📜 **License & Attribution**

This project is licensed under **GPL-3.0** in compliance with the [renogy-bt](https://github.com/cyrils/renogy-bt) library it's based on.

**Based on:** [renogy-bt by Cyril](https://github.com/cyrils/renogy-bt) (GPL-3.0)  
**Integration by:** Garrett Hazlett ([@MadGoatHaz](https://github.com/MadGoatHaz))

---

## ☕ **Support Development**

If this integration has saved you time and enhanced your solar monitoring experience, consider supporting development:

### **💖 Support Options**
- **[GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)** - Monthly sponsorship
- **[PayPal Donation](https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD)** - One-time donation

### **📧 Contact & Support**
- **Developer**: Garrett Hazlett ([@MadGoatHaz](https://github.com/MadGoatHaz))
- **Email**: ghazlett@gmail.com
- **Support**: ghazlett@gmail.com

---

**🎉 Happy Solar Monitoring! ☀️⚡🏠**

*Transform your Renogy BluPow devices into smart, monitored components of your Home Assistant ecosystem!*

---

<!-- Badges -->
[releases-shield]: https://img.shields.io/github/release/MadGoatHaz/blupow.svg?style=for-the-badge
[releases]: https://github.com/MadGoatHaz/blupow/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/MadGoatHaz/blupow.svg?style=for-the-badge  
[commits]: https://github.com/MadGoatHaz/blupow/commits/main
[license-shield]: https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Garrett%20Hazlett%20%40MadGoatHaz-blue.svg?style=for-the-badge
[sponsors-shield]: https://img.shields.io/badge/GitHub-Sponsors-ff69b4.svg?style=for-the-badge
[sponsors]: https://github.com/sponsors/MadGoatHaz
[paypal-shield]: https://img.shields.io/badge/PayPal-Donate-blue.svg?style=for-the-badge
[paypal]: https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD 