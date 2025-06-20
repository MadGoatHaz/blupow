#!/usr/bin/env python3
"""
Ultimate Test: Compare standalone vs Home Assistant Bluetooth behavior
"""
import asyncio
import sys
import os

# Test 1: Standalone environment (should work)
async def test_standalone():
    print("🧪 TEST 1: STANDALONE ENVIRONMENT")
    print("=" * 40)
    
    # Import bleak directly
    try:
        from bleak import BleakClient
        print("✅ Direct bleak import successful")
        
        # Test direct bleak connection
        print("Testing direct BleakClient connection...")
        
        async with BleakClient("D8:B6:73:BF:4F:75", timeout=20.0) as client:
            if client.is_connected:
                print("✅ Direct BleakClient: SUCCESS")
                
                # Try to discover services
                services = await client.get_services()
                print(f"✅ Services discovered: {len(services)}")
                
                # Look for our service
                target_service = None
                for service in services:
                    if "fff0" in str(service.uuid).lower():
                        target_service = service
                        break
                
                if target_service:
                    print(f"✅ Target service found: {target_service.uuid}")
                    return True
                else:
                    print("❌ Target service not found")
                    return False
            else:
                print("❌ Direct BleakClient: FAILED")
                return False
                
    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 2: Home Assistant environment (currently failing)
async def test_home_assistant_env():
    print("\n🧪 TEST 2: HOME ASSISTANT ENVIRONMENT")
    print("=" * 40)
    
    try:
        # Import Home Assistant's bluetooth manager
        from homeassistant.components import bluetooth
        from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
        print("✅ Home Assistant bluetooth imports successful")
        
        # Try to get bluetooth manager
        # This might be the issue - HA might be managing bluetooth differently
        print("Checking Home Assistant bluetooth state...")
        
        # Test our client in HA environment
        sys.path.append('/config/custom_components')
        from blupow.blupow_client import BluPowClient
        
        client = BluPowClient("D8:B6:73:BF:4F:75")
        
        print("Testing BluPowClient in HA environment...")
        connected = await client.connect()
        
        if connected:
            print("✅ BluPowClient in HA env: SUCCESS")
            
            data = await client.read_device_info()
            if data:
                print(f"✅ Data retrieval: {len(data)} fields")
                await client.disconnect()
                return True
            else:
                print("❌ Data retrieval failed")
        else:
            print("❌ BluPowClient in HA env: FAILED")
        
        if client.is_connected:
            await client.disconnect()
            
        return False
        
    except Exception as e:
        print(f"❌ Home Assistant env test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 3: Check for process/permission differences
async def test_environment_differences():
    print("\n🧪 TEST 3: ENVIRONMENT ANALYSIS")
    print("=" * 40)
    
    try:
        # Check user/permissions
        import pwd
        import grp
        
        user = pwd.getpwuid(os.getuid()).pw_name
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        
        print(f"Current user: {user}")
        print(f"Groups: {', '.join(groups)}")
        
        # Check if we're in a container
        if os.path.exists('/.dockerenv'):
            print("✅ Running in Docker container")
        else:
            print("❌ Not in Docker container")
        
        # Check bluetooth device access
        import subprocess
        try:
            result = subprocess.run(['ls', '-la', '/dev/'], capture_output=True, text=True)
            bluetooth_devices = [line for line in result.stdout.split('\n') if 'bluetooth' in line.lower() or 'hci' in line.lower()]
            
            if bluetooth_devices:
                print("✅ Bluetooth devices found:")
                for device in bluetooth_devices:
                    print(f"   {device}")
            else:
                print("❌ No bluetooth devices found in /dev/")
                
        except Exception as e:
            print(f"⚠️  Could not check /dev/: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment analysis failed: {e}")
        return False

async def main():
    print("🎯 ULTIMATE BLUETOOTH DIAGNOSIS")
    print("=" * 60)
    
    # Run all tests
    standalone_ok = await test_standalone()
    ha_env_ok = await test_home_assistant_env()
    env_analysis_ok = await test_environment_differences()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    print(f"Standalone environment: {'✅ WORKS' if standalone_ok else '❌ FAILS'}")
    print(f"Home Assistant environment: {'✅ WORKS' if ha_env_ok else '❌ FAILS'}")
    print(f"Environment analysis: {'✅ COMPLETE' if env_analysis_ok else '❌ FAILED'}")
    
    if standalone_ok and not ha_env_ok:
        print("\n🔍 DIAGNOSIS: Home Assistant environment issue")
        print("💡 Possible causes:")
        print("   - Home Assistant bluetooth manager interference")
        print("   - Different asyncio event loop")
        print("   - Container networking/permissions")
        print("   - Bluetooth adapter access restrictions")
        
        print("\n🛠️  RECOMMENDED SOLUTIONS:")
        print("   1. Check Home Assistant bluetooth integration conflicts")
        print("   2. Try disabling other bluetooth integrations temporarily")
        print("   3. Restart Home Assistant container with --privileged")
        print("   4. Check if device is being scanned by HA bluetooth discovery")
        
    elif ha_env_ok:
        print("\n🎉 SUCCESS: Both environments work!")
        print("📊 The coordinator should work - check sensors again!")
        
    else:
        print("\n❌ CRITICAL: Both environments failing")
        print("💡 Hardware or driver issue")
    
    return standalone_ok or ha_env_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 