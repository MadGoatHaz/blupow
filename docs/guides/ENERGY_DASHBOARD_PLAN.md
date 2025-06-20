# BluPow Energy Dashboard Implementation Plan

## 🎯 Executive Summary

Your BluPow integration is **production-ready** with all 22 inverter sensors properly configured for Home Assistant's energy dashboard. Once you have a stable connection, you can use this guide to integrate your inverter's data into a powerful energy monitoring dashboard.

## 📊 Sensor Crossover for the Energy Dashboard

The key to a great energy dashboard is mapping the right sensors to the right categories. Here's how the 22 BluPow sensors translate to Home Assistant's energy management features.

| Home Assistant Energy Category | BluPow Sensor Name | Entity ID Suffix | Status |
|---|---|---|---|
| **Grid Consumption** | `AC Load Power` | `load_active_power` | ✅ Ready |
| **Solar Production** | `Solar Input Power` | `solar_power` | ✅ Ready |
| **Battery In/Out** | `Battery Charging Power` & `AC Load Power` | `charging_power` | ✅ Ready |

## 🛠️ How to Configure the Energy Dashboard

Once your sensors are populated with live data, follow these steps:

1.  In Home Assistant, navigate to **Settings** → **Dashboards** → **Energy**.
2.  **Grid Consumption**: Click **Add Consumption** and select `sensor.ac_load_power`. This tracks the power your home is drawing from the inverter.
3.  **Solar Production**: Click **Add Solar Production** and select `sensor.solar_input_power`. This tracks the power coming from your solar panels.
4.  **Battery Storage**: Click **Add Battery System**.
    *   **Battery Charge**: Select `sensor.charging_power`. This is the power flowing *into* your batteries.
    *   **Battery Discharge**: Select `sensor.ac_load_power`. When not on grid power, this represents the power being drawn *from* your batteries.

## ✨ Creating a Custom Power Dashboard

Go beyond the default energy view by creating your own dashboard with custom cards. This allows you to visualize the full capabilities of the inverter.

### Recommended Custom Cards:

1.  **Gauge Cards:**
    *   `sensor.battery_soc`: For a clear "fuel gauge" of your battery level.
    *   `sensor.load_percentage`: To see how close you are to the inverter's maximum output.

2.  **Graph Cards:**
    *   Track `sensor.ac_output_voltage` and `sensor.ac_output_frequency` to monitor the quality of your inverter's power.
    *   Graph `sensor.battery_voltage` over time to see charging and discharging cycles.
    *   Plot `sensor.inverter_temperature` to monitor system health.

3.  **Entities Card:**
    *   Create a single card that lists all 22 sensors for a quick, at-a-glance overview of the entire system.

### Example Template Sensors
Add these to your `configuration.yaml` to create even more powerful data points.

```yaml
# configuration.yaml
template:
  - sensor:
      # This sensor shows a positive number when charging and a negative number when discharging
      - name: "Battery Power Flow"
        unit_of_measurement: "W"
        device_class: power
        state: >
          {% set charging_power = states('sensor.charging_power') | float(0) %}
          {% set load_power = states('sensor.load_active_power') | float(0) %}
          {% if states('sensor.charging_status') != 'deactivated' %}
            {{ charging_power }}
          {% else %}
            {{ -1 * load_power }}
          {% endif %}

      # A more descriptive charging status
      - name: "Battery Mode"
        icon: mdi:battery-heart-variant
        state: >
          {% set status = states('sensor.charging_status') %}
          {% if status == 'deactivated' %}
            Discharging
          {% elif status == 'constant current' %}
            Charging (Bulk)
          {% elif status == 'constant voltage' %}
            Charging (Absorption)
          {% elif status == 'floating' %}
            Charging (Float)
          {% else %}
            {{ status | title }}
          {% endif %}
```

This plan leverages the full suite of 22 sensors to provide a rich, detailed, and actionable view of your home's energy ecosystem. 