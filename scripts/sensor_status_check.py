#!/usr/bin/env python3
"""
BluPow Sensor Status Checker
Check current sensor states and identify issues
"""

import requests
import json
import sys
from datetime import datetime

def check_sensor_status():
    """Check the current status of all BluPow sensors"""
    
    # Home Assistant API details
    ha_url = "http://localhost:8123"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4ZGU5YjNhMDU4ZGU0NDc4OWRjOTQ1ZTU1MzlkNjYwOCIsImlhdCI6MTczNDc3MzA1NCwiZXhwIjoyMDUwMTMzMDU0fQ.4bLMGKoWTdmVYLgmSCgEGDRKLnKHyaF_KeZcOGVxsQE"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get all states
        response = requests.get(f"{ha_url}/api/states", headers=headers, timeout=10)
        
        if response.status_code == 200:
            states = response.json()
            
            # Filter BluPow sensors
            blupow_sensors = [s for s in states if 'blupow' in s.get('entity_id', '').lower()]
            
            print(f"=== BLUPOW SENSOR STATUS CHECK ===")
            print(f"Time: {datetime.now()}")
            print(f"Total BluPow sensors found: {len(blupow_sensors)}")
            print()
            
            # Group by device
            inverter_sensors = []
            controller_sensors = []
            unknown_sensors = []
            
            for sensor in blupow_sensors:
                entity_id = sensor.get('entity_id', '')
                unique_id = sensor.get('attributes', {}).get('unique_id', '')
                
                if 'D8B673BF4F75' in unique_id or 'D8:B6:73:BF:4F:75' in str(sensor):
                    inverter_sensors.append(sensor)
                elif 'C4D36A667ED4' in unique_id or 'C4:D3:6A:66:7E:D4' in str(sensor):
                    controller_sensors.append(sensor)
                else:
                    unknown_sensors.append(sensor)
            
            print(f"INVERTER SENSORS (D8:B6:73:BF:4F:75): {len(inverter_sensors)}")
            unavailable_inverter = 0
            for sensor in inverter_sensors:
                state = sensor.get('state', 'unknown')
                unit = sensor.get('attributes', {}).get('unit_of_measurement', '')
                if state in ['unavailable', 'unknown']:
                    unavailable_inverter += 1
                    print(f"  ❌ {sensor['entity_id']}: {state}")
                else:
                    print(f"  ✅ {sensor['entity_id']}: {state} {unit}")
            
            print()
            print(f"CONTROLLER SENSORS (C4:D3:6A:66:7E:D4): {len(controller_sensors)}")
            unavailable_controller = 0
            for sensor in controller_sensors:
                state = sensor.get('state', 'unknown')
                unit = sensor.get('attributes', {}).get('unit_of_measurement', '')
                if state in ['unavailable', 'unknown']:
                    unavailable_controller += 1
                    print(f"  ❌ {sensor['entity_id']}: {state}")
                else:
                    print(f"  ✅ {sensor['entity_id']}: {state} {unit}")
            
            if unknown_sensors:
                print()
                print(f"UNKNOWN/ORPHANED SENSORS: {len(unknown_sensors)}")
                for sensor in unknown_sensors:
                    state = sensor.get('state', 'unknown')
                    print(f"  ⚠️  {sensor['entity_id']}: {state}")
            
            print()
            print(f"=== SUMMARY ===")
            print(f"Inverter unavailable: {unavailable_inverter}/{len(inverter_sensors)}")
            print(f"Controller unavailable: {unavailable_controller}/{len(controller_sensors)}")
            print(f"Unknown sensors: {len(unknown_sensors)}")
            
            if unavailable_inverter + unavailable_controller + len(unknown_sensors) == 0:
                print("🎉 ALL SENSORS ARE WORKING!")
            else:
                print("❌ ISSUES DETECTED - Need to fix sensor problems")
                
            return {
                'total': len(blupow_sensors),
                'inverter_total': len(inverter_sensors),
                'inverter_unavailable': unavailable_inverter,
                'controller_total': len(controller_sensors),
                'controller_unavailable': unavailable_controller,
                'unknown': len(unknown_sensors)
            }
                
        else:
            print(f"❌ Failed to get HA states: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking sensor status: {e}")
        return None

if __name__ == "__main__":
    result = check_sensor_status()
    if result:
        # Exit with error code if there are issues
        if result['inverter_unavailable'] + result['controller_unavailable'] + result['unknown'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    else:
        sys.exit(2) 