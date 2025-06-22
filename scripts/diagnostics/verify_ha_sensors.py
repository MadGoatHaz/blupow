#!/usr/bin/env python3
"""
Verify BluPow sensors in Home Assistant
Test real data vs fake data and sensor availability
"""
import requests
import json
from datetime import datetime

def test_ha_sensors():
    """Test Home Assistant BluPow sensors"""
    ha_url = "http://localhost:8123"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI5ZGQwZjU4ZjUwNzM0ZTc4OGFhYmJkYzAzN2Y4ZTY3YyIsImlhdCI6MTczNDc5NjUzOCwiZXhwIjoyMDUwMTU2NTM4fQ.j7HYbfLGJhYHQSfRiKDECF6t3eXM3vVQm_H8SHYRWyc",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing BluPow sensors in Home Assistant")
    print("=" * 60)
    
    try:
        # Get all states
        response = requests.get(f"{ha_url}/api/states", headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to connect to Home Assistant: {response.status_code}")
            return
            
        states = response.json()
        
        # Filter BluPow sensors
        blupow_sensors = [s for s in states if s['entity_id'].startswith('sensor.') and 
                         ('blupow' in s['entity_id'].lower() or 
                          'inverter' in s['entity_id'].lower() or
                          'battery' in s['entity_id'].lower() or
                          'solar' in s['entity_id'].lower() or
                          'charging' in s['entity_id'].lower() or
                          'load' in s['entity_id'].lower() or
                          'ac_' in s['entity_id'].lower())]
        
        print(f"Found {len(blupow_sensors)} potential BluPow sensors")
        print()
        
        # Categorize sensors
        working_sensors = []
        unavailable_sensors = []
        unknown_sensors = []
        fake_data_sensors = []
        
        for sensor in blupow_sensors:
            entity_id = sensor['entity_id']
            state = sensor['state']
            last_changed = sensor.get('last_changed', '')
            last_updated = sensor.get('last_updated', '')
            attributes = sensor.get('attributes', {})
            
            # Check if sensor is working
            if state in ['unavailable', 'unknown']:
                if state == 'unavailable':
                    unavailable_sensors.append(entity_id)
                else:
                    unknown_sensors.append(entity_id)
            else:
                # Check for fake data patterns
                is_fake = False
                
                # Check for common fake values
                if isinstance(state, str):
                    try:
                        numeric_state = float(state)
                        # Check for suspiciously round numbers or fake patterns
                        if numeric_state in [123.0, 124.0, 125.0, 12.5, 13.2, 50.0, 100.0]:
                            is_fake = True
                    except ValueError:
                        # String states - check for fake patterns
                        if state in ['bulk_charge', 'constant current', 'RIV1230RCH-SPS']:
                            pass  # These might be real
                
                # Check if data is static (hasn't changed recently)
                if last_changed == last_updated and 'hours ago' in last_changed:
                    is_fake = True
                    
                if is_fake:
                    fake_data_sensors.append((entity_id, state))
                else:
                    working_sensors.append((entity_id, state, last_updated))
        
        # Report results
        print("📊 SENSOR STATUS SUMMARY")
        print("=" * 40)
        
        print(f"✅ Working sensors: {len(working_sensors)}")
        if working_sensors:
            for entity_id, state, last_updated in working_sensors[:10]:  # Show first 10
                print(f"   {entity_id}: {state} (updated: {last_updated[:19]})")
            if len(working_sensors) > 10:
                print(f"   ... and {len(working_sensors) - 10} more")
        
        print(f"\n❌ Unavailable sensors: {len(unavailable_sensors)}")
        if unavailable_sensors:
            for entity_id in unavailable_sensors[:5]:
                print(f"   {entity_id}")
            if len(unavailable_sensors) > 5:
                print(f"   ... and {len(unavailable_sensors) - 5} more")
        
        print(f"\n❓ Unknown sensors: {len(unknown_sensors)}")
        if unknown_sensors:
            for entity_id in unknown_sensors[:5]:
                print(f"   {entity_id}")
        
        print(f"\n🎭 Suspected fake data: {len(fake_data_sensors)}")
        if fake_data_sensors:
            for entity_id, state in fake_data_sensors[:5]:
                print(f"   {entity_id}: {state}")
        
        # Check for real-time data
        print("\n🔄 REAL-TIME DATA CHECK")
        print("=" * 30)
        
        # Look for sensors with recent updates
        recent_sensors = []
        current_time = datetime.now()
        
        for sensor in blupow_sensors:
            if sensor['state'] not in ['unavailable', 'unknown']:
                last_updated = sensor.get('last_updated', '')
                if last_updated:
                    try:
                        # Parse ISO timestamp
                        update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        time_diff = (current_time - update_time.replace(tzinfo=None)).total_seconds()
                        
                        if time_diff < 300:  # Updated within 5 minutes
                            recent_sensors.append((sensor['entity_id'], sensor['state'], time_diff))
                    except:
                        pass
        
        if recent_sensors:
            print(f"Found {len(recent_sensors)} sensors with recent updates:")
            for entity_id, state, seconds_ago in recent_sensors[:10]:
                print(f"   {entity_id}: {state} ({int(seconds_ago)}s ago)")
        else:
            print("⚠️  No sensors with recent updates found")
        
        # Check device info
        print("\n🔧 DEVICE INFORMATION")
        print("=" * 25)
        
        device_sensors = [s for s in blupow_sensors if 'model' in s['entity_id'] or 'device_id' in s['entity_id']]
        for sensor in device_sensors:
            print(f"   {sensor['entity_id']}: {sensor['state']}")
        
        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT")
        print("=" * 25)
        
        total_sensors = len(blupow_sensors)
        working_ratio = len(working_sensors) / total_sensors if total_sensors > 0 else 0
        
        if working_ratio > 0.8:
            print("✅ EXCELLENT: Most sensors are working")
        elif working_ratio > 0.5:
            print("⚠️  GOOD: Many sensors working, some issues")
        elif working_ratio > 0.2:
            print("❌ POOR: Few sensors working")
        else:
            print("💀 CRITICAL: Most sensors not working")
        
        print(f"Working: {len(working_sensors)}/{total_sensors} ({working_ratio:.1%})")
        
        if len(fake_data_sensors) > 0:
            print("⚠️  WARNING: Suspected fake data detected")
        
        if len(recent_sensors) > 0:
            print("✅ GOOD: Real-time data updates detected")
        else:
            print("❌ ISSUE: No recent data updates")
            
    except Exception as e:
        print(f"❌ Error testing sensors: {e}")

if __name__ == "__main__":
    test_ha_sensors() 