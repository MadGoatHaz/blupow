#!/usr/bin/env python3
"""
HOME ASSISTANT INTERNAL SENSOR TEST
Runs inside Home Assistant Docker container to test BluPow sensors
"""

import requests
import json
import sys
from datetime import datetime

def test_ha_sensors_internal():
    """Test sensors from inside Home Assistant container"""
    print("🔍 HOME ASSISTANT INTERNAL SENSOR TEST")
    print("=" * 60)
    print(f"Testing at {datetime.now()}")
    print()
    
    try:
        # Get all states from Home Assistant (internal access)
        print("📡 Querying Home Assistant API (internal)...")
        response = requests.get("http://localhost:8123/api/states", timeout=10)
        
        if response.status_code == 200:
            states = response.json()
            
            # Filter BluPow entities
            blupow_entities = []
            legacy_battery_entities = []
            
            for state in states:
                entity_id = state.get('entity_id', '')
                if 'blupow' in entity_id.lower():
                    blupow_entities.append(state)
                elif 'battery' in entity_id.lower() and 'blupow' not in entity_id.lower():
                    legacy_battery_entities.append(state)
            
            print(f"✅ Found {len(blupow_entities)} BluPow entities")
            print(f"⚠️ Found {len(legacy_battery_entities)} legacy battery entities")
            print()
            
            # Analyze BluPow sensor status
            working_sensors = []
            unavailable_sensors = []
            unknown_sensors = []
            
            for entity in blupow_entities:
                entity_id = entity['entity_id']
                state_value = entity['state']
                attributes = entity.get('attributes', {})
                unit = attributes.get('unit_of_measurement', '')
                friendly_name = attributes.get('friendly_name', entity_id)
                
                if state_value == 'unavailable':
                    unavailable_sensors.append({
                        'id': entity_id,
                        'name': friendly_name,
                        'state': state_value
                    })
                elif state_value == 'unknown':
                    unknown_sensors.append({
                        'id': entity_id,
                        'name': friendly_name,
                        'state': state_value
                    })
                else:
                    working_sensors.append({
                        'id': entity_id,
                        'name': friendly_name,
                        'state': state_value,
                        'unit': unit
                    })
            
            # Display results exactly like user sees
            print("🟢 WORKING BLUPOW SENSORS:")
            print("-" * 50)
            for sensor in working_sensors:
                print(f"  {sensor['name']}")
                print(f"  {sensor['state']} {sensor['unit']}")
            
            print(f"\n❌ UNAVAILABLE BLUPOW SENSORS ({len(unavailable_sensors)}):")
            print("-" * 50)
            for sensor in unavailable_sensors:
                print(f"  {sensor['name']}")
                print(f"  {sensor['state']}")
            
            if unknown_sensors:
                print(f"\n❓ UNKNOWN BLUPOW SENSORS ({len(unknown_sensors)}):")
                print("-" * 50)
                for sensor in unknown_sensors:
                    print(f"  {sensor['name']}")
                    print(f"  {sensor['state']}")
            
            # Show legacy sensors that might be conflicting
            if legacy_battery_entities:
                print(f"\n⚠️ LEGACY BATTERY SENSORS ({len(legacy_battery_entities)}):")
                print("-" * 50)
                for entity in legacy_battery_entities:
                    name = entity.get('attributes', {}).get('friendly_name', entity['entity_id'])
                    print(f"  {name} ({entity['entity_id']}): {entity['state']}")
            
            # Summary
            total_sensors = len(blupow_entities)
            working_count = len(working_sensors)
            unavailable_count = len(unavailable_sensors)
            unknown_count = len(unknown_sensors)
            
            print(f"\n📊 BLUPOW SENSOR SUMMARY:")
            print(f"Total BluPow Sensors: {total_sensors}")
            print(f"Working: {working_count} ({working_count/total_sensors*100:.1f}%)")
            print(f"Unavailable: {unavailable_count} ({unavailable_count/total_sensors*100:.1f}%)")
            print(f"Unknown: {unknown_count} ({unknown_count/total_sensors*100:.1f}%)")
            
            # Success criteria
            if unavailable_count == 0 and unknown_count == 0:
                print("\n🎉 SUCCESS: ALL BLUPOW SENSORS ARE WORKING!")
                return True
            else:
                print(f"\n❌ FAILURE: {unavailable_count + unknown_count} BluPow sensors still not working")
                
                # List the problematic sensors
                print("\n🔧 SENSORS THAT NEED FIXING:")
                for sensor in unavailable_sensors + unknown_sensors:
                    print(f"  - {sensor['name']} ({sensor['id']})")
                
                return False
                
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # This script is designed to run inside Home Assistant Docker container
    print("HOME ASSISTANT INTERNAL SENSOR TEST")
    print("This script must run inside the Home Assistant Docker container")
    print()
    
    success = test_ha_sensors_internal()
    sys.exit(0 if success else 1) 