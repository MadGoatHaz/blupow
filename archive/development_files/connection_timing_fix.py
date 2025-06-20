#!/usr/bin/env python3
"""
Connection Timing Fix for BluPow Integration
"""
import asyncio
import sys
import time

async def test_connection_timing():
    """Test if there's a timing issue with consecutive connections"""
    print("🕐 TESTING CONNECTION TIMING THEORY")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    # Test multiple consecutive connections with different delays
    delays = [0, 1, 3, 5, 10]
    
    for delay in delays:
        print(f"\n🧪 Testing with {delay}s delay between connections")
        
        # First connection
        client1 = BluPowClient("D8:B6:73:BF:4F:75")
        connected1 = await client1.connect()
        
        if connected1:
            print(f"✅ Connection 1: SUCCESS")
            await client1.disconnect()
            print(f"🔌 Disconnected, waiting {delay}s...")
            await asyncio.sleep(delay)
            
            # Second connection (simulating coordinator)
            client2 = BluPowClient("D8:B6:73:BF:4F:75")
            connected2 = await client2.connect()
            
            if connected2:
                print(f"✅ Connection 2: SUCCESS (delay={delay}s)")
                await client2.disconnect()
                return delay  # Found working delay
            else:
                print(f"❌ Connection 2: FAILED (delay={delay}s)")
        else:
            print(f"❌ Connection 1: FAILED")
    
    return None

async def implement_retry_fix():
    """Implement a connection retry mechanism"""
    print("\n🔧 IMPLEMENTING CONNECTION RETRY FIX")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    print("Testing connection with retry logic...")
    
    client = BluPowClient("D8:B6:73:BF:4F:75")
    
    # Try connection with retries and delays
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        print(f"🔗 Connection attempt {attempt + 1}/{max_retries}")
        
        try:
            connected = await client.connect()
            
            if connected:
                print("✅ CONNECTION SUCCESS with retry logic!")
                
                # Test data retrieval
                data = await client.read_device_info()
                if data:
                    print(f"✅ Data retrieval: {len(data)} fields")
                    print("🎯 This proves the retry mechanism works!")
                    
                    await client.disconnect()
                    return True
                else:
                    print("❌ Data retrieval failed")
            else:
                print(f"❌ Connection attempt {attempt + 1} failed")
                
        except Exception as e:
            print(f"❌ Connection attempt {attempt + 1} error: {e}")
        
        if attempt < max_retries - 1:
            delay = base_delay * (attempt + 1)
            print(f"⏳ Waiting {delay}s before retry...")
            await asyncio.sleep(delay)
    
    print("❌ All retry attempts failed")
    return False

async def patch_coordinator_with_retry():
    """Create a patched version of the coordinator with retry logic"""
    print("\n🩹 PATCHING COORDINATOR WITH RETRY LOGIC")
    print("=" * 50)
    
    # Read the current coordinator file
    coordinator_path = "/config/custom_components/blupow/coordinator.py"
    
    try:
        with open(coordinator_path, 'r') as f:
            content = f.read()
        
        # Check if retry logic is already present
        if "max_retries" in content:
            print("✅ Retry logic already present in coordinator")
            return True
        
        # Add retry logic to the connect call
        old_connect_code = """                connected = await self.client.connect()
                if not connected:
                    _LOGGER.error("Failed to connect to device")
                    return self.client.get_data()"""
        
        new_connect_code = """                # Try connection with retry logic for reliability
                max_retries = 3
                base_delay = 2
                connected = False
                
                for attempt in range(max_retries):
                    _LOGGER.info(f"Connection attempt {attempt + 1}/{max_retries}")
                    try:
                        connected = await self.client.connect()
                        if connected:
                            _LOGGER.info("Connection successful!")
                            break
                        else:
                            _LOGGER.warning(f"Connection attempt {attempt + 1} failed")
                    except Exception as e:
                        _LOGGER.warning(f"Connection attempt {attempt + 1} error: {e}")
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (attempt + 1)
                        _LOGGER.info(f"Waiting {delay}s before retry...")
                        await asyncio.sleep(delay)
                
                if not connected:
                    _LOGGER.error("Failed to connect to device after all retries")
                    return self.client.get_data()"""
        
        if old_connect_code in content:
            # Apply the patch
            new_content = content.replace(old_connect_code, new_connect_code)
            
            # Write the patched version
            with open(coordinator_path, 'w') as f:
                f.write(new_content)
            
            print("✅ Coordinator patched with retry logic!")
            print("💡 Restart Home Assistant to apply the fix")
            return True
        else:
            print("❌ Could not find connection code to patch")
            return False
            
    except Exception as e:
        print(f"❌ Failed to patch coordinator: {e}")
        return False

if __name__ == "__main__":
    print("🎯 FINAL CONNECTION TIMING FIX")
    print("=" * 50)
    
    async def main():
        # Test timing theory
        optimal_delay = await test_connection_timing()
        
        if optimal_delay is not None:
            print(f"\n✅ Found optimal delay: {optimal_delay}s")
        else:
            print("\n⚠️  No optimal delay found, will use retry logic")
        
        # Test retry mechanism
        retry_success = await implement_retry_fix()
        
        if retry_success:
            print("\n✅ Retry mechanism works!")
            
            # Patch the coordinator
            patch_success = await patch_coordinator_with_retry()
            
            if patch_success:
                print("\n🎉 SOLUTION IMPLEMENTED!")
                print("✅ Coordinator patched with retry logic")
                print("💡 Restart Home Assistant to activate the fix")
                print("📊 Sensors should show data after restart!")
                return True
        
        print("\n❌ Could not implement fix")
        return False
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 