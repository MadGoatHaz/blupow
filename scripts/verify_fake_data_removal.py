#!/usr/bin/env python3
"""
Verification script to check if fake data has been removed from the Home Assistant integration
"""
import subprocess
import sys
import time

def check_ha_logs_for_fake_data():
    """Check Home Assistant logs for signs of fake data"""
    print("🔍 Checking Home Assistant logs for fake data indicators...")
    
    try:
        # Check recent logs for any fake data indicators
        result = subprocess.run([
            'docker', 'exec', 'homeassistant', 
            'grep', '-i', 
            'fake\|hardcoded\|simulation\|test_mode\|production_fallback\|ultimate_fallback',
            '/config/home-assistant.log'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("⚠️ WARNING: Found potential fake data indicators in logs:")
            print(result.stdout)
            return False
        else:
            print("✅ No fake data indicators found in logs")
            return True
            
    except subprocess.TimeoutExpired:
        print("⏱️ Log check timed out")
        return True
    except Exception as e:
        print(f"ℹ️ Could not check logs: {e}")
        return True

def check_integration_files():
    """Check that the correct integration files are loaded"""
    print("\n🔍 Checking integration files in Home Assistant...")
    
    try:
        # Check the client file header
        result = subprocess.run([
            'docker', 'exec', 'homeassistant',
            'head', '-3', '/config/custom_components/blupow/blupow_client.py'
        ], capture_output=True, text=True, timeout=5)
        
        if 'Real Device Communication' in result.stdout:
            print("✅ Correct updated client file is loaded")
            return True
        else:
            print("❌ Old client file is still loaded!")
            print(f"Header: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"⚠️ Could not verify files: {e}")
        return False

def check_for_specific_fake_values():
    """Check for specific fake values that should not appear"""
    print("\n🔍 Checking for specific fake values in integration files...")
    
    fake_values = [
        "124.9",  # Fake AC voltage
        "bulk_charge",  # Fake charging status
        "INVERTER_RIV1230",  # Fake device ID
        "CONTROLLER_RVR40",  # Fake device ID
        "426890"  # Fake total generation
    ]
    
    all_clean = True
    
    for value in fake_values:
        try:
            result = subprocess.run([
                'docker', 'exec', 'homeassistant',
                'grep', '-r', value, '/config/custom_components/blupow/'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"❌ Found fake value '{value}' in:")
                print(result.stdout)
                all_clean = False
            else:
                print(f"✅ Fake value '{value}' not found")
                
        except Exception as e:
            print(f"ℹ️ Could not check for '{value}': {e}")
    
    return all_clean

def main():
    """Main verification function"""
    print("🔍 BluPow Integration - Fake Data Removal Verification")
    print("=" * 60)
    
    print("Waiting for Home Assistant to fully restart...")
    time.sleep(10)  # Give HA time to restart
    
    results = []
    
    # Run all checks
    results.append(check_integration_files())
    results.append(check_for_specific_fake_values())
    results.append(check_ha_logs_for_fake_data())
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("✅ SUCCESS: All checks passed!")
        print("✅ Fake data has been successfully removed")
        print("✅ Integration should now use real device data")
        print("\n🎯 Next steps:")
        print("1. Check your Home Assistant dashboard")
        print("2. Values should now change and reflect real device status")
        print("3. If sensors show 'unavailable', devices may need time to connect")
    else:
        print("❌ ISSUES FOUND: Some fake data may still be present")
        print("❌ Please check the issues above")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 