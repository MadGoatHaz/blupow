#!/usr/bin/env python3
"""
HOME ASSISTANT DEVICE SENSOR TEST
Tests BluPow sensors from Home Assistant's perspective via device API
Queries the exact same data the user sees at the device page
"""

import requests
import json
import sys
from datetime import datetime

# Home Assistant connection
HA_URL = "http://192.168.51.76:8123"
DEVICE_ID = "2d0c2125aecb0881fee8ed800867b6b9"

def test_ha_device_sensors():
    """Test sensors from Home Assistant device perspective"""
    print("🔍 HOME ASSISTANT DEVICE SENSOR TEST")
    print("=" * 60)
    print(f"Testing device: {DEVICE_ID}")
    print(f"URL: {HA_URL}/config/devices/device/{DEVICE_ID}")
    print()
    
    try:
        # Get all states from Home Assistant
        print("📡 Querying Home Assistant API...")
        response = requests.get(f"{HA_URL}/api/states", timeout=10)
        
        if response.status_code == 200:
            states = response.json()
            
            # Filter BluPow entities
            blupow_entities = []
            for state in states:
                entity_id = state.get('entity_id', '')
                if 'blupow' in entity_id.lower():
                    blupow_entities.append(state)
            
            print(f"✅ Found {len(blupow_entities)} BluPow entities")
            print()
            
            # Analyze sensor status
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
            
            # Display results
            print("🟢 WORKING SENSORS:")
            print("-" * 40)
            for sensor in working_sensors:
                print(f"  {sensor['name']}: {sensor['state']} {sensor['unit']}")
            
            print(f"\n❌ UNAVAILABLE SENSORS ({len(unavailable_sensors)}):")
            print("-" * 40)
            for sensor in unavailable_sensors:
                print(f"  {sensor['name']}: {sensor['state']}")
            
            if unknown_sensors:
                print(f"\n❓ UNKNOWN SENSORS ({len(unknown_sensors)}):")
                print("-" * 40)
                for sensor in unknown_sensors:
                    print(f"  {sensor['name']}: {sensor['state']}")
            
            # Summary
            total_sensors = len(blupow_entities)
            working_count = len(working_sensors)
            unavailable_count = len(unavailable_sensors)
            unknown_count = len(unknown_sensors)
            
            print(f"\n📊 SUMMARY:")
            print(f"Total BluPow Sensors: {total_sensors}")
            print(f"Working: {working_count} ({working_count/total_sensors*100:.1f}%)")
            print(f"Unavailable: {unavailable_count} ({unavailable_count/total_sensors*100:.1f}%)")
            print(f"Unknown: {unknown_count} ({unknown_count/total_sensors*100:.1f}%)")
            
            # Success criteria
            if unavailable_count == 0 and unknown_count == 0:
                print("\n🎉 SUCCESS: ALL SENSORS ARE WORKING!")
                return True
            else:
                print(f"\n❌ FAILURE: {unavailable_count + unknown_count} sensors still not working")
                return False
                
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_legacy_sensors():
    """Find legacy/duplicate sensors that might be conflicting"""
    try:
        print("\n🔍 CHECKING FOR LEGACY/DUPLICATE SENSORS...")
        response = requests.get(f"{HA_URL}/api/states", timeout=10)
        
        if response.status_code == 200:
            states = response.json()
            
            # Look for battery-related sensors that might conflict
            battery_sensors = []
            for state in states:
                entity_id = state.get('entity_id', '').lower()
                if 'battery' in entity_id and 'blupow' not in entity_id:
                    battery_sensors.append({
                        'id': state['entity_id'],
                        'state': state['state'],
                        'name': state.get('attributes', {}).get('friendly_name', state['entity_id'])
                    })
            
            if battery_sensors:
                print("⚠️ FOUND LEGACY BATTERY SENSORS:")
                for sensor in battery_sensors:
                    print(f"  {sensor['name']} ({sensor['id']}): {sensor['state']}")
                
        return battery_sensors
                
    except Exception as e:
        print(f"Error checking legacy sensors: {e}")
        return []

if __name__ == "__main__":
    print(f"Starting test at {datetime.now()}")
    
    # Test current sensor status
    success = test_ha_device_sensors()
    
    # Check for legacy sensors
    legacy_sensors = get_legacy_sensors()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 