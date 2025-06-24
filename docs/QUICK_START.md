# BluPow Quick Start Guide

This guide provides the fastest path to getting the BluPow integration up and running.

---

## 🚨 Core Environment Commands 🚨

**This is the single source of truth for managing the development environment.** All services are defined in a `docker-compose.yml` file located in the `~/opt/` directory, **one level above the project's git repository root.**

You **MUST** use these commands from the `~/opt/` directory to manage the lifecycle of the Home Assistant and BluPow Gateway containers.

### Start or Restart Environment
This is the standard command to bring up all services in a clean, detached state.
```bash
# From the ~/opt/ directory
docker compose up -d --build
```

### Stop Environment
This stops and removes all running containers defined in the compose file.
```bash
# From the ~/opt/ directory
docker compose down
```

### View Logs
To see the logs for a specific service (e.g., Home Assistant or the gateway):
```bash
# For Home Assistant
docker compose logs -f homeassistant

# For the BluPow Gateway
docker compose logs -f blupow-gateway
```
---

### Step 1: Run the BluPow Gateway

Ensure the BluPow Gateway container is running and connected to your MQTT broker. Refer to the `docker-compose.yaml` file in the root of the project for the recommended setup.

```yaml
services:
  blupow-gateway:
    container_name: blupow-gateway
    image: blupow-gateway:latest
    restart: unless-stopped
    privileged: true # Required for Bluetooth access
    networks:
      - blupow-net # Must be on the same network as your MQTT broker
    volumes:
      - /var/run/dbus:/var/run/dbus # For Bluetooth access
    environment:
      - MQTT_BROKER=blupow-mosquitto # Hostname of your MQTT broker
      # ... other environment variables
```

### Step 2: Add the Integration in Home Assistant

1.  If you have an old version of the BluPow integration, **delete it first** from **Settings > Devices & Services**.
2.  Go to **Settings > Devices & Services**.
3.  Click **+ ADD INTEGRATION**, search for "BluPow", and select it.

### Step 3: Add a Device

A menu will appear.

#### To Auto Discover:

1.  Select **Auto Discover Devices**.
2.  The system will scan for 10 seconds.
3.  Choose your device from the dropdown list.
4.  Select the correct **Device Type** and submit.

#### To Add Manually:

1.  Select **Add Device Manually**.
2.  Enter the **MAC Address** and select the **Device Type**.
3.  Submit the form.

### Step 4: Done!

The BluPow integration is now configured. The gateway will automatically find the new device and publish its sensors to Home Assistant via MQTT Discovery. Your sensors should appear shortly.

To manage devices later (add more or remove them), simply click **CONFIGURE** on the BluPow integration card.

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