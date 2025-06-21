# 📦 BluPow Installation Guide

Complete step-by-step installation instructions for the BluPow Home Assistant integration.

---

## 🚀 **Method 1: HACS Installation (Recommended)**

### **Prerequisites**
- ✅ Home Assistant OS/Supervised/Container/Core
- ✅ HACS installed and configured  
- ✅ Bluetooth adapter available to Home Assistant
- ✅ Your BluPow device MAC address

### **Step 1: Add Custom Repository**
1. **Open HACS** in Home Assistant
2. Click **"Integrations"**
3. Click the **three dots (⋯)** in the top right
4. Select **"Custom repositories"**
5. **Add Repository**:
   - **Repository**: `https://github.com/MadGoatHaz/blupow`
   - **Category**: `Integration`
6. Click **"Add"**

### **Step 2: Install BluPow Integration**
1. **Search** for "BluPow" in HACS integrations
2. Click **"BluPow - Renogy Device Integration"**
3. Click **"Download"**
4. **Restart Home Assistant**

### **Step 3: Add Integration**
1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"** (bottom right)
3. Search for **"BluPow"**
4. **Enter your device information**:
   - **MAC Address**: Your device MAC (e.g., `XX:XX:XX:XX:XX:XX`)
   - **Device Name**: Descriptive name (e.g., "Solar Inverter")
5. Click **"Submit"**

### **Step 4: Verify Installation**
- Check **Devices & Services** → **BluPow**
- You should see your device with 17-20 sensors
- All sensors should show real data (not "unavailable")

---

## 🛠️ **Method 2: Manual Installation**

### **Prerequisites**
- ✅ SSH/Terminal access to Home Assistant
- ✅ File system access to `/config` directory

### **Step 1: Download Integration**
```bash
# Navigate to custom components directory
cd /config/custom_components

# Download the integration
git clone https://github.com/MadGoatHaz/blupow.git

# Or download and extract manually
wget https://github.com/MadGoatHaz/blupow/archive/main.zip
unzip main.zip
mv blupow-main blupow
```

### **Step 2: Verify File Structure**
```
/config/custom_components/blupow/
├── __init__.py
├── manifest.json
├── config_flow.py
├── coordinator.py
├── sensor.py
├── blupow_client.py
├── const.py
├── strings.json
└── translations/
    └── en.json
```

### **Step 3: Restart Home Assistant**
```bash
# Restart Home Assistant
# Method depends on your installation type
docker restart homeassistant  # Docker
systemctl restart home-assistant  # Systemd
```

### **Step 4: Add Integration**
Follow **Step 3** from the HACS method above.

---

## 🔍 **Finding Your Device MAC Address**

### **Method 1: Bluetooth Scanner**
```bash
# Use the built-in discovery script
python3 scripts/blupow_device_discovery.py
```

### **Method 2: Phone App**
1. Install a **Bluetooth scanner app** on your phone
2. Look for devices starting with:
   - `RIV1230` (Inverters)
   - `RNG-CTRL` (Controllers)  
   - `BT-TH` (Alternative naming)

### **Method 3: Home Assistant Bluetooth**
1. **Settings** → **Devices & Services** → **Bluetooth**
2. Look for **discovered devices**
3. Find your Renogy device

### **Method 4: Manual Discovery**
```bash
# Linux/macOS terminal
hcitool scan
bluetoothctl scan on

# Look for MAC addresses like:
# XX:XX:XX:XX:XX:XX - RIV1230RCH-SPS  
# YY:YY:YY:YY:YY:YY - RNG-CTRL-RVR40
```

---

## ⚙️ **Configuration Options**

### **Basic Configuration**
No YAML configuration required! The integration automatically:
- ✅ Discovers appropriate sensors for your device type
- ✅ Sets up proper device classes and units  
- ✅ Configures 30-second update intervals
- ✅ Handles connection management and fallbacks

### **Optional YAML Configuration**
```yaml
# configuration.yaml (optional customization)
blupow:
  update_interval: 30  # Update frequency in seconds (default: 30)
  
# Example: Custom update interval
blupow:
  update_interval: 15  # Faster updates (more Bluetooth traffic)
```

### **Integration Options**
When adding the integration, you can configure:
- **MAC Address**: Your device's Bluetooth MAC
- **Device Name**: Friendly name for Home Assistant
- **Update Interval**: How often to poll the device (optional)

---

## 🎯 **Device-Specific Setup**

### **🔌 Inverter (RIV1230RCH-SPS)**
- **MAC Pattern**: Usually starts with `D8:B6:73:BF:`
- **Expected Sensors**: 17 sensors for AC monitoring, battery management
- **Use Case**: Home backup power, AC load monitoring

**Typical MAC**: `XX:XX:XX:XX:XX:XX`

### **☀️ Controller (RNG-CTRL-RVR40)**  
- **MAC Pattern**: Usually starts with `C4:D3:6A:66:`
- **Expected Sensors**: 20 sensors for solar production, MPPT charging
- **Use Case**: Solar system monitoring, battery charging control

**Typical MAC**: `YY:YY:YY:YY:YY:YY`

---

## 🚨 **Troubleshooting Installation**

### **Problem: Integration Not Found**
```bash
# Verify files are in correct location
ls -la /config/custom_components/blupow/

# Check Home Assistant logs
docker logs homeassistant | grep blupow
```

### **Problem: Sensors Show "Unavailable"**
```bash
# Run stability fix
python3 deploy_production_stability.py

# Test device connectivity
python3 scripts/direct_device_test.py
```

### **Problem: Device Not Connecting**
1. **Check Bluetooth**: Ensure device is in range and powered
2. **Verify MAC**: Use discovery tools to confirm MAC address
3. **Check Conflicts**: Ensure no other apps are connected to device

### **Problem: Duplicate Sensors**
```bash
# Clean up duplicate entities
python3 cleanup_duplicate_sensors.py

# Re-add integration via Home Assistant UI
```

---

## ✅ **Verification Steps**

### **1. Check Integration Status**
```bash
# Quick health check
python3 scripts/quick_integration_test.py
```

### **2. Verify Sensors**
- **Go to**: Settings → Devices & Services → BluPow
- **Check**: All sensors show real values (not "unavailable")
- **Verify**: Device info shows correct model and MAC

### **3. Test Dashboard Integration**
- **Create** a simple dashboard card with BluPow sensors
- **Verify** values update every 30 seconds
- **Check** Energy Dashboard integration (if applicable)

---

## 🎉 **Post-Installation**

### **🏠 Add to Dashboard**
Create beautiful energy monitoring dashboards with your new sensors!

### **⚡ Energy Dashboard**
BluPow sensors automatically integrate with Home Assistant's Energy Dashboard for solar production and consumption tracking.

### **🤖 Automation Ideas**
- **Low Battery Alerts**: Notify when SOC < 20%
- **Solar Production Tracking**: Log peak production times
- **Load Balancing**: Manage high-power devices based on battery level
- **Backup Power Monitoring**: Track runtime during outages

---

## 📚 **Next Steps**

1. **[Dashboard Examples](docs/DASHBOARD_EXAMPLES.md)** - Beautiful UI layouts
2. **[Automation Guide](docs/AUTOMATION_GUIDE.md)** - Smart home integration
3. **[Energy Dashboard Setup](docs/ENERGY_DASHBOARD.md)** - Track your solar production
4. **[Troubleshooting](docs/troubleshooting/TROUBLESHOOTING.md)** - Common issues and solutions

---

**🎯 Installation Complete! Your BluPow device is now fully integrated with Home Assistant!** ✨

---

## 📞 **Support & Contact**

### **Developer**
- **Garrett Hazlett** ([@MadGoatHaz](https://github.com/MadGoatHaz))
- **Email**: ghazlett@gmail.com

### **Support Development**
- **[GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)** - Monthly sponsorship
- **[PayPal Donation](https://www.paypal.com/donate/?business=SYVNJAZPAC23S&no_recurring=0&currency_code=USD)** - One-time donation

### **Get Help**
- **Issues**: [GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)
- **Email**: ghazlett@gmail.com 