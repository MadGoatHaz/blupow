#!/usr/bin/env python3
"""
Fix BluPow Sensor Mess
Remove legacy sensors and fix mapping issues
"""

import json
import os
import shutil
from datetime import datetime

def fix_sensor_mess():
    """Fix the sensor mess by cleaning up legacy sensors"""
    
    print("=== FIXING BLUPOW SENSOR MESS ===")
    print(f"Time: {datetime.now()}")
    
    # 1. Remove legacy sensors from entity registry
    entity_registry_path = "/var/lib/docker/volumes/homeassistant_config/_data/.storage/core.entity_registry"
    
    if os.path.exists(entity_registry_path):
        print("📁 Found entity registry, backing up...")
        
        # Create backup
        backup_path = f"backups/entity_registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("backups", exist_ok=True)
        shutil.copy2(entity_registry_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        
        # Load and clean registry
        with open(entity_registry_path, 'r') as f:
            registry = json.load(f)
        
        # Legacy sensors to remove
        legacy_sensors = [
            'sensor.batterycurrent',
            'sensor.batterycircuit', 
            'sensor.batteryv2',
            'sensor.batteryvoltage',
            'sensor.battery_soc',
            'sensor.battery_current',
            'sensor.battery_temperature',
            'sensor.charging_amp_hours_today',
            'sensor.controller_temperature',
            'sensor.daily_power_consumption',
            'sensor.daily_power_generation',
            'sensor.discharging_amp_hours_today',
            'sensor.load_power',
            'sensor.load_voltage',
            'sensor.model_number',
            'sensor.total_power_generation'
        ]
        
        original_count = len(registry.get('data', {}).get('entities', []))
        
        # Remove legacy entities
        entities = registry.get('data', {}).get('entities', [])
        entities_to_keep = []
        
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            if entity_id not in legacy_sensors:
                entities_to_keep.append(entity)
            else:
                print(f"🗑️  Removing legacy sensor: {entity_id}")
        
        registry['data']['entities'] = entities_to_keep
        
        # Save cleaned registry
        with open(entity_registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        removed_count = original_count - len(entities_to_keep)
        print(f"✅ Removed {removed_count} legacy sensors from entity registry")
        
    else:
        print("⚠️  Entity registry not found, skipping cleanup")
    
    # 2. Fix template sensors in configuration.yaml
    config_yaml_path = "/var/lib/docker/volumes/homeassistant_config/_data/configuration.yaml"
    
    if os.path.exists(config_yaml_path):
        print("📁 Found configuration.yaml, checking for template sensors...")
        
        with open(config_yaml_path, 'r') as f:
            config_content = f.read()
        
        # Check for problematic template sensors
        if 'sensor.batteryvoltage' in config_content:
            print("⚠️  Found reference to sensor.batteryvoltage in configuration.yaml")
            print("   Manual fix needed: Update templates to use sensor.blupow_battery_voltage")
        
        if 'sensor.batterycurrent' in config_content:
            print("⚠️  Found reference to sensor.batterycurrent in configuration.yaml") 
            print("   Manual fix needed: Update templates to use sensor.blupow_battery_charging_current")
    
    # 3. Create sensor mapping guide
    mapping_guide = {
        "legacy_to_new_mapping": {
            "sensor.batteryvoltage": "sensor.blupow_battery_voltage (D8:B6:73:BF:4F:75)",
            "sensor.batterycurrent": "sensor.blupow_battery_charging_current (D8:B6:73:BF:4F:75)",
            "sensor.battery_soc": "sensor.blupow_battery_soc (both devices)",
            "sensor.battery_temperature": "sensor.blupow_battery_temperature (C4:D3:6A:66:7E:D4)",
            "sensor.solar_power": "sensor.blupow_pv_power (C4:D3:6A:66:7E:D4)",
            "sensor.load_power": "sensor.blupow_load_power (C4:D3:6A:66:7E:D4)"
        },
        "device_specific_sensors": {
            "inverter_D8B673BF4F75": [
                "ac_input_voltage", "ac_input_current", "ac_input_frequency",
                "ac_output_voltage", "ac_output_current", "ac_output_frequency", 
                "load_active_power", "load_apparent_power", "load_current", "load_percentage",
                "battery_voltage", "battery_soc", "charging_current", "charging_status", "charging_power",
                "line_charging_current", "solar_voltage", "solar_current", "solar_power",
                "inverter_temperature"
            ],
            "controller_C4D36A667ED4": [
                "pv_voltage", "pv_current", "pv_power",
                "battery_voltage", "battery_current", "battery_soc", "battery_temperature",
                "charging_status", "charging_power", "max_charging_power_today",
                "charging_amp_hours_today", "discharging_amp_hours_today",
                "power_generation_today", "power_consumption_today", "power_generation_total",
                "load_status", "load_voltage", "load_current", "load_power",
                "controller_temperature", "battery_type"
            ]
        }
    }
    
    with open("sensor_mapping_guide.json", 'w') as f:
        json.dump(mapping_guide, f, indent=2)
    
    print("✅ Created sensor_mapping_guide.json")
    
    print("\n=== NEXT STEPS ===")
    print("1. Restart Home Assistant to apply entity registry changes")
    print("2. Check configuration.yaml for legacy sensor references")
    print("3. Update any automations/templates to use new sensor names")
    print("4. Verify all sensors show proper values (not unavailable)")
    
    return True

if __name__ == "__main__":
    success = fix_sensor_mess()
    exit(0 if success else 1) 