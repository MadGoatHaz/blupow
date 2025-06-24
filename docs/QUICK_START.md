# BluPow Gateway: Quick Start Guide

This guide provides the fastest path to getting the BluPow Gateway and its corresponding Home Assistant integration running using Docker.

**Audience**: This guide is intended for developers or advanced users who are running the gateway from a cloned version of this repository.
**Prerequisites**: You must have a working Docker and Docker Compose environment, a Bluetooth adapter, and a running MQTT broker.

---

## 🚀 **3-Step Setup**

This is the single source of truth for running the development/local environment.

### **Step 1: Configure the Environment**

First, clone the repository to the machine that has Bluetooth and will run the gateway.

```bash
git clone https://github.com/MadGoatHaz/blupow.git
cd blupow/
```

Next, navigate to the `blupow_gateway` directory and create your environment configuration file.

```bash
cd blupow_gateway/
cp .env.example .env
```

Now, **edit the `.env` file** with your favorite editor. You must set the `MQTT_BROKER_HOST` to the IP address of your MQTT broker. If your broker requires authentication, you must also set `MQTT_USER` and `MQTT_PASS`.

### **Step 2: Launch the Gateway**

With the environment configured, use Docker Compose to build and run the gateway container in the background.

```bash
# From the blupow_gateway/ directory
docker compose up -d --build
```

**What's happening?**
*   `--build`: This tells Docker Compose to build the gateway's Docker image from the `Dockerfile` in the current directory.
*   `-d`: This runs the container in "detached" mode, so it continues running in the background.

You can check the logs at any time to see what the gateway is doing:
```bash
docker compose logs -f
```

### **Step 3: Configure Home Assistant**

1.  **Copy the Integration**: Copy the `custom_components/blupow` directory from the repository root into your Home Assistant's `custom_components` folder.
2.  **Restart Home Assistant**: This is required for Home Assistant to recognize the new integration.
3.  **Add the Integration**:
    *   In Home Assistant, go to **Settings > Devices & Services**.
    *   Click **+ Add Integration** and search for **BluPow**.
    *   Select it. No further configuration is needed.
4.  **Add Your Devices**:
    *   Find the BluPow integration card and click **Configure**.
    *   Select **Auto Discover Devices**. The gateway will scan for nearby BLE devices.
    *   Choose your device from the list, select the correct **Device Type** (e.g., Renogy Controller), and click **Submit**.
    *   Done! Your device and its sensors will now appear in Home Assistant.

---

## Troubleshooting

-   **Device not found during discovery?**
    *   Check the gateway logs (`docker compose logs -f`) for any Bluetooth errors.
    -   Ensure your device is powered on and advertising.
    -   Make sure the gateway machine is within Bluetooth range of your device.
-   **Sensors are "Unavailable" in Home Assistant?**
    -   Use an MQTT exploration tool (like MQTT Explorer) to verify that the gateway is publishing data to the `blupow/.../state` topics.
    -   Verify that the gateway is publishing discovery messages to the `homeassistant/sensor/...` topics.
    -   Check the gateway logs for any polling errors after the device was added.

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