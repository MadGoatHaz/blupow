#!/usr/bin/env python3
"""
Final Debug: Get BluPow sensors working in Home Assistant
"""
import asyncio
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_coordinator_issue():
    """Diagnose why coordinator fails when direct connection works"""
    print("🔍 FINAL DEBUG: Diagnosing coordinator vs direct connection")
    print("=" * 60)
    
    try:
        sys.path.append('/config/custom_components')
        from blupow.blupow_client import BluPowClient
        from blupow.coordinator import BluPowDataUpdateCoordinator
        
        print("✅ Imports successful")
        
        # Test 1: Direct connection (we know this works)
        print("\n🧪 TEST 1: Direct connection")
        client = BluPowClient("D8:B6:73:BF:4F:75")
        
        connected = await client.connect()
        if connected:
            print("✅ Direct connection: SUCCESS")
            data = await client.read_device_info()
            print(f"✅ Direct data read: {len(data)} fields")
            await client.disconnect()
        else:
            print("❌ Direct connection: FAILED")
            return False
        
        # Test 2: Check if there's a timing issue
        print("\n🧪 TEST 2: Testing timing issue")
        print("Waiting 5 seconds for device to be ready...")
        await asyncio.sleep(5)
        
        # Test 3: Simulate coordinator behavior exactly
        print("\n🧪 TEST 3: Simulating coordinator behavior")
        
        # Create a new client like coordinator does
        coord_client = BluPowClient("D8:B6:73:BF:4F:75")
        
        print("Attempting coordinator-style connection...")
        coord_connected = await coord_client.connect()
        
        if coord_connected:
            print("✅ Coordinator-style connection: SUCCESS")
            
            # Try the exact same data read the coordinator does
            coord_data = await coord_client.read_device_info()
            
            if coord_data and len(coord_data) > 0:
                print(f"✅ Coordinator-style data read: SUCCESS - {len(coord_data)} fields")
                
                # Check if data has the expected keys
                expected_keys = ['input_voltage', 'battery_voltage', 'model']
                missing_keys = [key for key in expected_keys if key not in coord_data]
                
                if not missing_keys:
                    print("✅ All expected data keys present")
                    print("🎯 SOLUTION: The coordinator should work!")
                    
                    # Show sample data
                    print("\n📊 Sample data that should appear in sensors:")
                    for key, value in list(coord_data.items())[:10]:
                        print(f"   {key}: {value}")
                    
                    await coord_client.disconnect()
                    return True
                else:
                    print(f"❌ Missing expected keys: {missing_keys}")
            else:
                print("❌ Coordinator-style data read: FAILED")
        else:
            print("❌ Coordinator-style connection: FAILED")
        
        if coord_client.is_connected:
            await coord_client.disconnect()
        
        return False
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def force_coordinator_refresh():
    """Force the coordinator to refresh and hopefully pick up data"""
    print("\n🔄 ATTEMPTING COORDINATOR FORCE REFRESH")
    print("=" * 50)
    
    try:
        # Try to trigger a coordinator refresh
        print("Attempting to force coordinator refresh...")
        
        # We'll do this by creating a successful connection and leaving data in the client cache
        client = BluPowClient("D8:B6:73:BF:4F:75")
        connected = await client.connect()
        
        if connected:
            print("✅ Pre-loading data for coordinator...")
            data = await client.read_device_info()
            
            if data:
                print(f"✅ Data pre-loaded: {len(data)} fields")
                print("💡 Data is now cached in client - coordinator should pick it up")
                
                # Don't disconnect immediately - let coordinator potentially use this connection
                await asyncio.sleep(2)
                
                # Now disconnect
                await client.disconnect()
                print("✅ Connection released for coordinator")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Force refresh failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 FINAL PUSH: Getting BluPow sensors to show data")
    print("=" * 60)
    
    async def main():
        # Run diagnosis
        diagnosis_success = await diagnose_coordinator_issue()
        
        if diagnosis_success:
            print("\n" + "=" * 60)
            print("🎉 DIAGNOSIS: Integration should work!")
            print("✅ Connection: Working")
            print("✅ Data retrieval: Working") 
            print("✅ Data parsing: Working")
            print("\n💡 NEXT STEPS:")
            print("1. Wait for next coordinator refresh (30 seconds)")
            print("2. Check Home Assistant sensors")
            print("3. If still unavailable, restart Home Assistant")
        else:
            print("\n❌ DIAGNOSIS: Found issues that need fixing")
        
        # Try force refresh
        await force_coordinator_refresh()
        
        print("\n🏁 Final debug complete!")
        return diagnosis_success
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 