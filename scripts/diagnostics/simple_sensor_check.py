#!/usr/bin/env python3
"""
Simple sensor check - see what BluPow sensors exist in Home Assistant
"""

import subprocess
import json

def check_ha_sensors():
    """Check what BluPow sensors exist in Home Assistant"""
    print("🔍 CHECKING BLUPOW SENSORS IN HOME ASSISTANT")
    print("=" * 60)
    
    try:
        # Get all entities from Home Assistant
        result = subprocess.run([
            'docker', 'exec', 'homeassistant', 
            'python', '-c', 
            '''
import json
import sqlite3
import os

# Connect to Home Assistant database
db_path = "/config/home-assistant_v2.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all BluPow entities
    cursor.execute("SELECT entity_id, state, attributes FROM states WHERE entity_id LIKE '%blupow%' ORDER BY entity_id")
    entities = cursor.fetchall()
    
    print(f"Found {len(entities)} BluPow entities:")
    for entity_id, state, attributes in entities:
        attrs = json.loads(attributes) if attributes else {}
        unit = attrs.get("unit_of_measurement", "")
        friendly_name = attrs.get("friendly_name", entity_id)
        print(f"  {entity_id}: {state} {unit} ({friendly_name})")
    
    conn.close()
else:
    print("Database not found")
            '''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"Error checking sensors: {e}")

if __name__ == "__main__":
    check_ha_sensors() 