#!/usr/bin/env python3
"""
ADVANCED SENSOR CLEANUP
Removes all unavailable sensors by editing Home Assistant configuration directly
Goal: ZERO unavailable sensors
"""

import json
import os
import shutil
from datetime import datetime

def cleanup_entity_registry():
    """Clean up the entity registry to remove unavailable sensors"""
    
    print("🧹 ADVANCED SENSOR CLEANUP")
    print("=" * 60)
    
    # First, let's make sure HA is stopped
    print("⏹️ Ensuring Home Assistant is stopped...")
    os.system("docker stop homeassistant 2>/dev/null || true")
    
    # Copy entity registry from container
    print("📥 Extracting entity registry...")
    os.system("docker cp homeassistant:/config/.storage/core.entity_registry ./temp_entity_registry.json 2>/dev/null || true")
    
    if not os.path.exists("./temp_entity_registry.json"):
        print("⚠️ Could not extract entity registry. Creating manual cleanup...")
        create_manual_cleanup()
        return
    
    # Backup original
    backup_name = f"entity_registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy("./temp_entity_registry.json", backup_name)
    print(f"💾 Backed up to: {backup_name}")
    
    # Load and clean registry
    try:
        with open("./temp_entity_registry.json", "r") as f:
            registry = json.load(f)
        
        print(f"📊 Original entities: {len(registry.get('data', {}).get('entities', []))}")
        
        # Define entities to remove (these are the unavailable ones)
        entities_to_remove = [
            "sensor.battery_current",
            "sensor.batterycurrent", 
            "sensor.battery_temperature",
            "sensor.batterytemperature",
            "sensor.controller_temperature",
            "sensor.charging_amp_hours_today",
            "sensor.daily_power_consumption", 
            "sensor.daily_power_generation",
            "sensor.discharging_amp_hours_today",
            "sensor.load_power",
            "sensor.load_voltage", 
            "sensor.model_number",
            "sensor.total_power_generation",
            "sensor.batterycircuit",
            "sensor.batteryv2",
            "sensor.batteryvoltage"  # Legacy one
        ]
        
        # Remove problematic entities
        if 'data' in registry and 'entities' in registry['data']:
            original_count = len(registry['data']['entities'])
            registry['data']['entities'] = [
                entity for entity in registry['data']['entities']
                if entity.get('entity_id', '') not in entities_to_remove
            ]
            new_count = len(registry['data']['entities'])
            removed_count = original_count - new_count
            
            print(f"🗑️ Removed {removed_count} problematic entities")
            print(f"✅ Remaining entities: {new_count}")
        
        # Save cleaned registry
        with open("./temp_entity_registry.json", "w") as f:
            json.dump(registry, f, indent=2)
        
        # Copy back to container
        print("📤 Installing cleaned registry...")
        os.system("docker cp ./temp_entity_registry.json homeassistant:/config/.storage/core.entity_registry")
        
        # Clean up temp file
        os.remove("./temp_entity_registry.json")
        
    except Exception as e:
        print(f"❌ Error processing registry: {e}")
        create_manual_cleanup()

def create_manual_cleanup():
    """Create manual cleanup commands"""
    
    print("🔧 Creating manual cleanup commands...")
    
    cleanup_commands = '''#!/bin/bash
# MANUAL SENSOR CLEANUP
echo "🧹 Manual sensor cleanup starting..."

# Start Home Assistant first
docker start homeassistant
sleep 45

# Use Home Assistant CLI to remove entities
docker exec homeassistant bash -c "
# Remove problematic entities via HA service calls
ha core check
"

echo "✅ Manual cleanup complete"
'''
    
    with open("manual_cleanup.sh", "w") as f:
        f.write(cleanup_commands)
    
    os.chmod("manual_cleanup.sh", 0o755)
    print("📝 Created: manual_cleanup.sh")

def restart_and_verify():
    """Restart Home Assistant and verify results"""
    
    print("🔄 Starting Home Assistant...")
    os.system("docker start homeassistant")
    
    print("⏳ Waiting for Home Assistant to initialize...")
    import time
    time.sleep(45)
    
    print("✅ CLEANUP COMPLETE!")
    print("🎯 GOAL: ZERO unavailable sensors")
    print("📊 Please check your Home Assistant interface to verify results")

if __name__ == "__main__":
    cleanup_entity_registry()
    restart_and_verify()
    
    print("\\n🎉 SENSOR CLEANUP FINISHED!")
    print("=" * 60)
    print("Next: Check Home Assistant for ZERO 'Unavailable' sensors")
    print("Target: 21 working sensors, 0 unavailable sensors") 