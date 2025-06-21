#!/usr/bin/env python3
"""
DEFINITIVE HOME ASSISTANT SENSOR VERIFICATION TEST
Tests BluPow sensors from Home Assistant's perspective via REST API
Must show REAL DATA, not "Unavailable" for all 18 sensors
"""

import requests
import json
import time
import sys
from datetime import datetime

# Home Assistant connection
HA_URL = "http://localhost:8123"
HA_TOKEN = None  # Will try without token first (local access)

# All BluPow sensors that MUST work
REQUIRED_SENSORS = [
    "sensor.blupow_battery_current",
    "sensor.blupow_battery_soc", 
    "sensor.blupow_battery_temperature",
    "sensor.blupow_battery_voltage",
    "sensor.blupow_charging_amp_hours_today",
    "sensor.blupow_charging_status",
    "sensor.blupow_controller_temperature", 
    "sensor.blupow_daily_power_consumption",
    "sensor.blupow_daily_power_generation",
    "sensor.blupow_discharging_amp_hours_today",
    "sensor.blupow_load_current",
    "sensor.blupow_load_power",
    "sensor.blupow_load_voltage",
    "sensor.blupow_model_number",
    "sensor.blupow_solar_current",
    "sensor.blupow_solar_power", 
    "sensor.blupow_solar_voltage",
    "sensor.blupow_total_power_generation"
]

def test_ha_api_access():
    """Test if we can access Home Assistant API"""
    try:
        headers = {}
        if HA_TOKEN:
            headers["Authorization"] = f"Bearer {HA_TOKEN}"
            
        response = requests.get(f"{HA_URL}/api/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Home Assistant API accessible")
            return True
        else:
            print(f"❌ HA API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot access HA API: {e}")
        return False

def get_sensor_state(entity_id):
    """Get sensor state from Home Assistant"""
    try:
        headers = {}
        if HA_TOKEN:
            headers["Authorization"] = f"Bearer {HA_TOKEN}"
            
        response = requests.get(f"{HA_URL}/api/states/{entity_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Error getting {entity_id}: {e}")
        return None

def check_all_sensors():
    """Check all BluPow sensors and return results"""
    print(f"\n🔍 CHECKING ALL BLUPOW SENSORS - {datetime.now()}")
    print("=" * 80)
    
    results = {
        'total_sensors': len(REQUIRED_SENSORS),
        'available_sensors': 0,
        'unavailable_sensors': 0,
        'missing_sensors': 0,
        'sensor_details': {},
        'success': False
    }
    
    for sensor in REQUIRED_SENSORS:
        state_data = get_sensor_state(sensor)
        
        if state_data is None:
            print(f"❌ {sensor}: MISSING/NOT FOUND")
            results['missing_sensors'] += 1
            results['sensor_details'][sensor] = {'status': 'MISSING', 'state': None}
        else:
            state = state_data.get('state', 'unknown')
            attributes = state_data.get('attributes', {})
            
            if state.lower() in ['unavailable', 'unknown', 'none']:
                print(f"❌ {sensor}: {state.upper()}")
                results['unavailable_sensors'] += 1
                results['sensor_details'][sensor] = {'status': 'UNAVAILABLE', 'state': state}
            else:
                print(f"✅ {sensor}: {state} {attributes.get('unit_of_measurement', '')}")
                results['available_sensors'] += 1
                results['sensor_details'][sensor] = {
                    'status': 'AVAILABLE', 
                    'state': state,
                    'unit': attributes.get('unit_of_measurement', ''),
                    'friendly_name': attributes.get('friendly_name', '')
                }
    
    # Calculate success
    results['success'] = (results['available_sensors'] == results['total_sensors'])
    
    print("\n📊 SENSOR STATUS SUMMARY")
    print("=" * 40)
    print(f"Total Sensors: {results['total_sensors']}")
    print(f"✅ Available: {results['available_sensors']}")
    print(f"❌ Unavailable: {results['unavailable_sensors']}")
    print(f"❓ Missing: {results['missing_sensors']}")
    print(f"Success Rate: {(results['available_sensors']/results['total_sensors']*100):.1f}%")
    
    if results['success']:
        print("\n🎉 SUCCESS: ALL SENSORS SHOWING REAL DATA!")
    else:
        print(f"\n💥 FAILURE: {results['unavailable_sensors'] + results['missing_sensors']} sensors not working!")
    
    return results

def continuous_monitoring(duration_minutes=10):
    """Monitor sensors continuously for specified duration"""
    print(f"\n🔄 STARTING {duration_minutes}-MINUTE CONTINUOUS MONITORING")
    print("=" * 60)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    check_interval = 30  # Check every 30 seconds
    
    consecutive_successes = 0
    total_checks = 0
    
    while time.time() < end_time:
        total_checks += 1
        results = check_all_sensors()
        
        if results['success']:
            consecutive_successes += 1
            print(f"✅ Check {total_checks}: SUCCESS ({consecutive_successes} consecutive)")
        else:
            consecutive_successes = 0
            print(f"❌ Check {total_checks}: FAILED (reset consecutive count)")
        
        remaining_time = int((end_time - time.time()) / 60)
        print(f"⏱️ {remaining_time} minutes remaining...")
        
        if time.time() < end_time:
            time.sleep(check_interval)
    
    print(f"\n📈 MONITORING COMPLETE")
    print(f"Total Checks: {total_checks}")
    print(f"Consecutive Successes: {consecutive_successes}")
    
    if consecutive_successes >= (duration_minutes * 2):  # At least 2 checks per minute
        print("🎉 CONTINUOUS SUCCESS ACHIEVED!")
        return True
    else:
        print("💥 CONTINUOUS SUCCESS NOT ACHIEVED!")
        return False

def main():
    print("🚀 BLUPOW HOME ASSISTANT SENSOR VERIFICATION TEST")
    print("=" * 80)
    print("This test verifies BluPow sensors work from Home Assistant's perspective")
    print("All sensors must show REAL DATA, not 'Unavailable'")
    print("=" * 80)
    
    # Test HA API access
    if not test_ha_api_access():
        print("💥 CRITICAL: Cannot access Home Assistant API!")
        sys.exit(1)
    
    # Initial sensor check
    initial_results = check_all_sensors()
    
    if not initial_results['success']:
        print("\n💥 INITIAL CHECK FAILED - SENSORS NOT WORKING!")
        print("Fix required before continuous monitoring can begin.")
        
        # Save failure report
        with open('sensor_failure_report.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'test_type': 'initial_check',
                'results': initial_results
            }, f, indent=2)
        
        return False
    
    print("\n✅ INITIAL CHECK PASSED - STARTING CONTINUOUS MONITORING")
    
    # Continuous monitoring
    success = continuous_monitoring(10)
    
    # Final report
    final_results = check_all_sensors()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'complete_verification',
        'initial_results': initial_results,
        'final_results': final_results,
        'continuous_success': success,
        'overall_success': success and final_results['success']
    }
    
    with open('final_sensor_verification_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    if report['overall_success']:
        print("\n🎉🎉🎉 COMPLETE SUCCESS! BLUPOW SENSORS WORKING PERFECTLY! 🎉🎉🎉")
        return True
    else:
        print("\n💥💥💥 FAILURE! SENSORS STILL NOT WORKING CORRECTLY! 💥💥💥")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 