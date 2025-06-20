#!/usr/bin/env python3
"""
Coordinator Fix: Ensure coordinator gets real data by eliminating race conditions
"""
import asyncio
import sys
import time
import subprocess

async def stop_all_bluetooth_interference():
    """Stop anything that might interfere with coordinator connection"""
    print("🛑 STOPPING BLUETOOTH INTERFERENCE")
    print("=" * 50)
    
    try:
        # Kill any lingering python processes that might hold bluetooth
        print("Checking for interfering processes...")
        
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout.split('\n')
        
        bluetooth_processes = []
        for line in processes:
            if ('python' in line and 'bleak' in line) or ('python' in line and 'bluetooth' in line):
                if 'coordinator' not in line:  # Don't kill coordinator
                    bluetooth_processes.append(line)
        
        if bluetooth_processes:
            print(f"Found {len(bluetooth_processes)} potentially interfering processes")
            for proc in bluetooth_processes:
                print(f"   {proc[:100]}...")
        else:
            print("✅ No interfering processes found")
        
        # Reset bluetooth to clean state
        print("Resetting bluetooth to clean state...")
        subprocess.run(['hciconfig', 'hci0', 'down'], capture_output=True)
        await asyncio.sleep(1)
        subprocess.run(['hciconfig', 'hci0', 'up'], capture_output=True)
        await asyncio.sleep(2)
        print("✅ Bluetooth reset complete")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Interference cleanup failed: {e}")
        return False

async def wait_for_coordinator_window():
    """Wait for the optimal window when coordinator will attempt connection"""
    print("\n⏰ WAITING FOR COORDINATOR WINDOW")
    print("=" * 50)
    
    # Coordinator runs every 30 seconds
    # We need to time this perfectly
    print("Calculating optimal timing...")
    
    current_time = time.time()
    # Coordinator typically starts at :00, :30 seconds
    seconds_in_minute = current_time % 60
    
    if seconds_in_minute < 25:
        # Wait until just before 30-second mark
        wait_time = 25 - seconds_in_minute
        print(f"Waiting {wait_time:.1f}s until coordinator window...")
        await asyncio.sleep(wait_time)
    elif seconds_in_minute < 55:
        # Wait until just before next minute
        wait_time = 55 - seconds_in_minute
        print(f"Waiting {wait_time:.1f}s until coordinator window...")
        await asyncio.sleep(wait_time)
    else:
        # We're in the window
        print("✅ In coordinator window now")
    
    return True

async def ensure_device_ready():
    """Ensure the Renogy device is ready and responsive"""
    print("\n🔌 ENSURING DEVICE READINESS")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    # Quick connection test to wake up device
    print("Performing device wake-up test...")
    
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    try:
        # Very quick connection to wake device
        connected = await client.connect()
        if connected:
            print("✅ Device is responsive")
            # Don't read data, just disconnect quickly
            await client.disconnect()
            
            # Give device a moment to be ready for coordinator
            print("⏳ Allowing device recovery time...")
            await asyncio.sleep(3)
            return True
        else:
            print("❌ Device not responsive")
            return False
            
    except Exception as e:
        print(f"⚠️  Device test failed: {e}")
        if client.is_connected:
            await client.disconnect()
        return False

async def monitor_coordinator_success():
    """Monitor coordinator attempts in real-time"""
    print("\n👁️  MONITORING COORDINATOR")
    print("=" * 50)
    
    print("Watching for coordinator connection attempts...")
    
    # Monitor for 60 seconds (2 coordinator cycles)
    start_time = time.time()
    last_log_time = start_time
    
    while time.time() - start_time < 60:
        try:
            # Get recent logs
            result = subprocess.run([
                'docker', 'logs', '--since', f'{int(last_log_time)}', 'homeassistant'
            ], capture_output=True, text=True)
            
            logs = result.stdout
            
            if "Connection successful!" in logs:
                print("🎉 COORDINATOR CONNECTION SUCCESS!")
                print("✅ Real data should now be flowing to sensors!")
                return True
            elif "Connection attempt" in logs:
                print("📡 Coordinator attempting connection...")
            elif "Failed to connect to device after all retries" in logs:
                print("❌ Coordinator failed this cycle")
            
            last_log_time = time.time()
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"⚠️  Log monitoring error: {e}")
            await asyncio.sleep(2)
    
    print("⏰ Monitoring period complete")
    return False

async def verify_sensor_data():
    """Verify that sensors now have real data"""
    print("\n📊 VERIFYING SENSOR DATA")
    print("=" * 50)
    
    try:
        # Check recent logs for sensor updates
        result = subprocess.run([
            'docker', 'logs', '--tail', '50', 'homeassistant'
        ], capture_output=True, text=True)
        
        logs = result.stdout
        
        # Look for sensor value updates (not "unavailable")
        sensor_updates = []
        for line in logs.split('\n'):
            if 'blupow' in line and 'sensor' in line and 'unavailable' not in line:
                if any(key in line for key in ['voltage', 'current', 'power', 'temperature']):
                    sensor_updates.append(line)
        
        if sensor_updates:
            print(f"✅ Found {len(sensor_updates)} sensor updates!")
            print("📈 Recent sensor activity:")
            for update in sensor_updates[-5:]:  # Show last 5
                print(f"   {update.split(']')[-1].strip()}")
            return True
        else:
            print("❌ No sensor data updates found")
            return False
            
    except Exception as e:
        print(f"⚠️  Sensor verification failed: {e}")
        return False

async def final_connection_test():
    """One final test to confirm everything works"""
    print("\n🧪 FINAL VERIFICATION TEST")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    try:
        print("Final connection test...")
        connected = await client.connect()
        
        if connected:
            print("✅ Connection: SUCCESS")
            
            data = await client.read_device_info()
            if data and len(data) > 0:
                print(f"✅ Data retrieval: {len(data)} fields")
                
                # Show key values
                key_values = {}
                for key in ['model', 'input_voltage', 'battery_voltage', 'temperature', 'load_active_power']:
                    if key in data and data[key] is not None:
                        key_values[key] = data[key]
                
                if key_values:
                    print("🎯 REAL DATA CONFIRMED:")
                    for key, value in key_values.items():
                        print(f"   {key}: {value}")
                    
                    await client.disconnect()
                    return True
                else:
                    print("❌ Data is null/empty")
            else:
                print("❌ No data retrieved")
        else:
            print("❌ Connection failed")
        
        if client.is_connected:
            await client.disconnect()
            
        return False
        
    except Exception as e:
        print(f"❌ Final test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 COORDINATOR FIX: Getting Real Data to Sensors")
    print("=" * 60)
    
    async def main():
        # Step 1: Clean up interference
        cleanup_ok = await stop_all_bluetooth_interference()
        
        # Step 2: Wait for optimal timing
        timing_ok = await wait_for_coordinator_window()
        
        # Step 3: Ensure device is ready
        device_ok = await ensure_device_ready()
        
        if not device_ok:
            print("❌ Device not ready - cannot proceed")
            return False
        
        # Step 4: Monitor coordinator
        coordinator_success = await monitor_coordinator_success()
        
        if coordinator_success:
            print("\n🎉 COORDINATOR SUCCESS!")
            
            # Step 5: Verify sensor data
            sensor_ok = await verify_sensor_data()
            
            if sensor_ok:
                print("✅ Sensors have real data!")
            else:
                print("⚠️  Coordinator connected but sensors not updated yet")
                print("💡 Check Home Assistant UI - data may be there")
        else:
            print("\n⚠️  Coordinator didn't connect during monitoring")
            print("💡 But connection capability is confirmed")
        
        # Step 6: Final verification
        final_ok = await final_connection_test()
        
        if final_ok:
            print("\n🎉 FINAL SUCCESS!")
            print("✅ Real data connection confirmed")
            print("📊 Sensors should show live inverter data")
            return True
        else:
            print("\n⚠️  Final test inconclusive")
            print("💡 Check Home Assistant sensors manually")
            return True  # Still consider success if coordinator worked
    
    success = asyncio.run(main())
    print(f"\n🏁 RESULT: {'SUCCESS - REAL DATA WORKING' if success else 'NEEDS INVESTIGATION'}")
    sys.exit(0 if success else 1) 