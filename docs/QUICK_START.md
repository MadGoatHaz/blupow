# ⚡ BluPow Quick Start Guide

Get your BluPow integration running in **less than 5 minutes**!

---

## 🎯 **What You Need**
- ✅ Home Assistant running
- ✅ HACS installed
- ✅ Your BluPow device MAC address

---

## 🚀 **3-Step Installation**

### **Step 1: Install via HACS**
1. **Open HACS** → **Integrations**
2. **Click "⋯"** → **Custom repositories**
3. **Add**: `https://github.com/MadGoatHaz/blupow`
4. **Search "BluPow"** → **Install**
5. **Restart Home Assistant**

### **Step 2: Add Integration**
1. **Settings** → **Devices & Services**
2. **"+ Add Integration"** → **Search "BluPow"**
3. **Enter MAC address**: `D8:B6:73:BF:4F:75` (or your device MAC)
4. **Submit**

### **Step 3: Verify**
- **Check**: Settings → Devices & Services → BluPow
- **You should see**: 17-20 sensors with real data
- **Test**: Create a simple dashboard card

---

## 🔍 **Find Your Device MAC**

### **Method 1: Phone App** (Easiest)
1. **Install** Bluetooth scanner app
2. **Look for**: `RIV1230` or `RNG-CTRL` devices
3. **Copy MAC address**

### **Method 2: Home Assistant**
1. **Settings** → **Devices & Services** → **Bluetooth**
2. **Find** your Renogy device
3. **Note MAC address**

---

## 📊 **Expected Results**

### **🔌 Inverter (RIV1230RCH-SPS)**
- **17 sensors**: AC I/O, battery, load monitoring
- **Example entities**:
  - `sensor.blupow_inverter_battery_voltage`
  - `sensor.blupow_inverter_load_power`
  - `sensor.blupow_inverter_battery_soc`

### **☀️ Controller (RNG-CTRL-RVR40)**
- **20 sensors**: Solar production, MPPT charging
- **Example entities**:
  - `sensor.blupow_controller_pv_power`
  - `sensor.blupow_controller_battery_current`
  - `sensor.blupow_controller_charging_status`

---

## 🚨 **Quick Troubleshooting**

### **Problem: Sensors show "Unavailable"**
```bash
# Run the fix script
python3 deploy_production_stability.py
```

### **Problem: Device not found**
- **Check** device is powered on and in range
- **Verify** MAC address is correct
- **Try** different Bluetooth scanner to confirm MAC

### **Problem: Duplicate sensors**
```bash
# Clean up duplicates
python3 cleanup_duplicate_sensors.py
# Then re-add integration via HA UI
```

---

## 🎨 **Create Your First Dashboard**

```yaml
# Dashboard card example
type: entities
title: "Solar Power System"
entities:
  - sensor.blupow_controller_pv_power
  - sensor.blupow_inverter_load_power
  - sensor.blupow_inverter_battery_voltage
  - sensor.blupow_inverter_battery_soc
```

---

## 📱 **Energy Dashboard Integration**

Your BluPow sensors automatically work with Home Assistant's Energy Dashboard:

1. **Settings** → **Energy** → **Configure**
2. **Solar production**: Add `sensor.blupow_controller_power_generation_today`
3. **Battery**: Add `sensor.blupow_inverter_charging_power`
4. **Grid consumption**: Add your grid sensors

---

## 🆘 **Need Help?**

- **📖 Full Guide**: [README.md](../README.md)
- **🔧 Installation**: [INSTALLATION.md](../INSTALLATION.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/MadGoatHaz/blupow/issues)
- **💬 Community**: [Home Assistant Forum](https://community.home-assistant.io)

---

**🎉 That's it! You're now monitoring your solar system like a pro!** ⚡🏠☀️ 