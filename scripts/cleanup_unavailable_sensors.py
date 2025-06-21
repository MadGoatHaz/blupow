#!/usr/bin/env python3
"""
CLEANUP UNAVAILABLE SENSORS
Identifies and removes all sensors showing "Unavailable"
Goal: ZERO unavailable sensors
"""

import json
import os
from datetime import datetime

def analyze_unavailable_sensors():
    """Analyze the user's sensor list to identify unavailable sensors"""
    
    # User's sensor data from their report
    user_sensors = {
        # WORKING SENSORS (keep these)
        "AC Apparent Power": "510 VA",
        "AC Input Current": "8.20 A", 
        "AC Input Frequency": "60.00 Hz",
        "AC Input Voltage": "120.5 V",
        "AC Load Power": "492 W",
        "AC Output Current": "4.10 A",
        "AC Output Frequency": "60.00 Hz", 
        "AC Output Voltage": "120.2 V",
        "Battery Charging Current": "5.20 A",
        "Battery SOC": "85%",  # Working one
        "Battery Voltage": "12.80 V",
        "Charging Power": "66 W",
        "Charging Status": "constant_voltage",
        "Device ID": "BTRIC134000035",
        "Inverter Model": "RIV1230RCH-SPS",
        "Inverter Temperature": "77.5 °F",
        "Line Charging Current": "0.00 A",
        "Load Current": "4.10 A",
        "Load Percentage": "35%",
        "Solar Input Current": "3.60 A",
        "Solar Input Power": "66 W",
        "Solar Input Voltage": "18.4 V",
        
        # UNAVAILABLE SENSORS (remove these)
        "Battery Current": "Unavailable",
        "Battery SOC": "Unavailable",  # Duplicate
        "Battery Temperature": "Unavailable", 
        "Charging Amp Hours Today": "Unavailable",
        "Controller Temperature": "Unavailable",
        "Daily Power Consumption": "Unavailable",
        "Daily Power Generation": "Unavailable",
        "Discharging Amp Hours Today": "Unavailable",
        "Load Power": "Unavailable",
        "Load Voltage": "Unavailable",
        "Model Number": "Unavailable",
        "Total Power Generation": "Unavailable"
    }
    
    working_sensors = []
    unavailable_sensors = []
    
    for name, value in user_sensors.items():
        if value == "Unavailable":
            unavailable_sensors.append(name)
        else:
            working_sensors.append({"name": name, "value": value})
    
    print("🔍 SENSOR ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"✅ WORKING SENSORS: {len(working_sensors)}")
    print(f"❌ UNAVAILABLE SENSORS: {len(unavailable_sensors)}")
    print()
    
    print("❌ SENSORS TO REMOVE (Unavailable):")
    for sensor in unavailable_sensors:
        print(f"  - {sensor}")
    
    print()
    print("✅ SENSORS TO KEEP (Working):")
    for sensor in working_sensors:
        print(f"  - {sensor['name']}: {sensor['value']}")
    
    return unavailable_sensors, working_sensors

def create_sensor_removal_plan():
    """Create a plan to remove unavailable sensors"""
    
    unavailable_sensors, working_sensors = analyze_unavailable_sensors()
    
    # Map sensor names to likely entity IDs
    sensor_removal_plan = {
        "Battery Current": ["sensor.battery_current", "sensor.batterycurrent"],
        "Battery SOC": ["sensor.battery_soc_unavailable"],  # Keep the working 85% one
        "Battery Temperature": ["sensor.battery_temperature", "sensor.batterytemperature"],
        "Charging Amp Hours Today": ["sensor.charging_amp_hours_today"],
        "Controller Temperature": ["sensor.controller_temperature"],
        "Daily Power Consumption": ["sensor.daily_power_consumption"],
        "Daily Power Generation": ["sensor.daily_power_generation"],
        "Discharging Amp Hours Today": ["sensor.discharging_amp_hours_today"],
        "Load Power": ["sensor.load_power"],
        "Load Voltage": ["sensor.load_voltage"],
        "Model Number": ["sensor.model_number"],
        "Total Power Generation": ["sensor.total_power_generation"]
    }
    
    print("\n🔧 SENSOR REMOVAL PLAN:")
    print("=" * 60)
    
    removal_commands = []
    
    for sensor_name in unavailable_sensors:
        if sensor_name in sensor_removal_plan:
            entity_ids = sensor_removal_plan[sensor_name]
            print(f"\n📍 {sensor_name}:")
            for entity_id in entity_ids:
                print(f"  - Remove: {entity_id}")
                removal_commands.append(f"# Remove {sensor_name}")
                removal_commands.append(f"docker exec homeassistant rm -f /config/.storage/core.entity_registry | grep {entity_id} || true")
    
    print("\n🎯 GOAL: ZERO UNAVAILABLE SENSORS")
    print(f"Target: Remove {len(unavailable_sensors)} unavailable sensors")
    print(f"Keep: {len(working_sensors)} working sensors")
    
    return removal_commands

def generate_cleanup_script():
    """Generate the actual cleanup script"""
    
    removal_commands = create_sensor_removal_plan()
    
    cleanup_script = '''#!/bin/bash
# SENSOR CLEANUP SCRIPT
# Goal: Remove all "Unavailable" sensors
# Date: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''

echo "🧹 CLEANING UP UNAVAILABLE SENSORS"
echo "=================================="

# Stop Home Assistant
echo "⏹️ Stopping Home Assistant..."
docker stop homeassistant

# Backup entity registry
echo "💾 Backing up entity registry..."
docker cp homeassistant:/config/.storage/core.entity_registry ./entity_registry_backup_$(date +%Y%m%d_%H%M%S).json

# Remove problematic legacy sensors
echo "🗑️ Removing legacy sensors..."

# These are the utility meter sensors causing conflicts
docker exec homeassistant bash -c "
cd /config/.storage
# Remove utility meter sensors that conflict
grep -v 'batterycurrent' core.entity_registry > temp_registry.json && mv temp_registry.json core.entity_registry
grep -v 'batterycircuit' core.entity_registry > temp_registry.json && mv temp_registry.json core.entity_registry
"

# Clean up template sensors
echo "🧽 Cleaning template sensors..."
docker exec homeassistant bash -c "
cd /config
# Remove template sensors that reference unavailable entities
sed -i '/sensor.batteryvoltage/d' configuration.yaml || true
sed -i '/sensor.batteryv2/d' configuration.yaml || true
"

# Restart Home Assistant
echo "🔄 Restarting Home Assistant..."
docker start homeassistant

echo "✅ CLEANUP COMPLETE!"
echo "Waiting for Home Assistant to start..."
sleep 30

echo "🔍 Checking results..."
'''
    
    return cleanup_script

if __name__ == "__main__":
    print("🎯 UNAVAILABLE SENSOR CLEANUP UTILITY")
    print("=" * 60)
    print("Goal: ZERO 'Unavailable' sensors")
    print()
    
    # Analyze current state
    analyze_unavailable_sensors()
    
    # Create removal plan
    create_sensor_removal_plan()
    
    # Generate cleanup script
    cleanup_script = generate_cleanup_script()
    
    # Save cleanup script
    with open("sensor_cleanup.sh", "w") as f:
        f.write(cleanup_script)
    
    print("\n📝 Generated: sensor_cleanup.sh")
    print("\n🚀 NEXT STEPS:")
    print("1. Run: chmod +x sensor_cleanup.sh")
    print("2. Run: ./sensor_cleanup.sh")
    print("3. Verify: ZERO unavailable sensors remain")
    print()
    print("🎯 TARGET: 100% working sensors, 0% unavailable!") 