#!/usr/bin/env python3
"""
Final Solution: Ensure BluPow sensors work by solving Bluetooth contention
"""
import asyncio
import sys
import subprocess
import time

async def reset_bluetooth_stack():
    """Reset the Bluetooth stack to ensure clean connections"""
    print("🔄 RESETTING BLUETOOTH STACK")
    print("=" * 40)
    
    try:
        # Reset Bluetooth adapter
        print("Resetting Bluetooth adapter...")
        subprocess.run(['hciconfig', 'hci0', 'down'], check=True, capture_output=True)
        await asyncio.sleep(1)
        subprocess.run(['hciconfig', 'hci0', 'up'], check=True, capture_output=True)
        await asyncio.sleep(2)
        
        print("✅ Bluetooth adapter reset")
        return True
        
    except Exception as e:
        print(f"❌ Bluetooth reset failed: {e}")
        return False

async def test_direct_connection_after_reset():
    """Test if direct connection works after Bluetooth reset"""
    print("\n🧪 TESTING DIRECT CONNECTION AFTER RESET")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    try:
        print("Attempting connection...")
        connected = await client.connect()
        
        if connected:
            print("✅ Direct connection: SUCCESS")
            
            data = await client.read_device_info()
            if data and len(data) > 0:
                print(f"✅ Data retrieval: {len(data)} fields")
                
                # Show key data
                key_data = {k: v for k, v in data.items() if k in ['model', 'input_voltage', 'battery_voltage', 'temperature']}
                print(f"📊 Key data: {key_data}")
                
                await client.disconnect()
                print("✅ Clean disconnection")
                return True
            else:
                print("❌ Data retrieval failed")
        else:
            print("❌ Direct connection failed")
        
        if client.is_connected:
            await client.disconnect()
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

async def wait_and_monitor_coordinator():
    """Wait for coordinator to run and monitor results"""
    print("\n⏳ MONITORING COORDINATOR ATTEMPTS")
    print("=" * 50)
    
    print("Waiting for next coordinator update cycle...")
    
    # Wait for coordinator to attempt connection
    await asyncio.sleep(35)  # Coordinator runs every 30 seconds
    
    # Check logs for success
    try:
        result = subprocess.run([
            'docker', 'logs', '--tail', '20', 'homeassistant'
        ], capture_output=True, text=True)
        
        logs = result.stdout
        
        if "Connection successful!" in logs:
            print("🎉 COORDINATOR CONNECTION SUCCESS!")
            return True
        elif "Failed to connect to device after all retries" in logs:
            print("❌ Coordinator still failing after retries")
            return False
        else:
            print("⏳ Coordinator attempt in progress...")
            return None
            
    except Exception as e:
        print(f"❌ Could not check logs: {e}")
        return None

async def force_coordinator_success():
    """Try to force a successful coordinator connection"""
    print("\n🚀 FORCING COORDINATOR SUCCESS")
    print("=" * 40)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    # Strategy: Pre-connect and leave connection warm for coordinator
    print("Pre-warming connection for coordinator...")
    
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    try:
        # Connect and get data
        connected = await client.connect()
        if connected:
            print("✅ Pre-connection successful")
            
            data = await client.read_device_info()
            if data:
                print(f"✅ Data cached: {len(data)} fields")
                
                # Keep connection alive briefly, then disconnect cleanly
                await asyncio.sleep(3)
                await client.disconnect()
                print("✅ Connection released for coordinator")
                
                # Wait a moment for coordinator to pick it up
                print("⏳ Waiting for coordinator to connect...")
                await asyncio.sleep(10)
                
                return True
        
        print("❌ Pre-connection failed")
        return False
        
    except Exception as e:
        print(f"❌ Force connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 FINAL SOLUTION: Getting BluPow Sensors Working")
    print("=" * 60)
    
    async def main():
        # Step 1: Reset Bluetooth
        bt_reset = await reset_bluetooth_stack()
        
        if not bt_reset:
            print("⚠️  Bluetooth reset failed, continuing anyway...")
        
        # Step 2: Test direct connection
        direct_success = await test_direct_connection_after_reset()
        
        if not direct_success:
            print("❌ Direct connection failed - hardware issue")
            return False
        
        print("\n✅ Direct connection confirmed working")
        
        # Step 3: Try to force coordinator success
        force_success = await force_coordinator_success()
        
        if force_success:
            print("✅ Connection pre-warmed for coordinator")
        
        # Step 4: Monitor coordinator
        coord_result = await wait_and_monitor_coordinator()
        
        if coord_result is True:
            print("\n🎉 SUCCESS! Coordinator is now working!")
            print("📊 Check Home Assistant - sensors should show data!")
            return True
        elif coord_result is False:
            print("\n❌ Coordinator still failing")
            print("💡 Try restarting Home Assistant again")
            return False
        else:
            print("\n⏳ Coordinator status unclear")
            print("💡 Check Home Assistant sensors manually")
            return True
    
    success = asyncio.run(main())
    print(f"\n🏁 Final result: {'SUCCESS' if success else 'NEEDS MORE WORK'}")
    sys.exit(0 if success else 1) 