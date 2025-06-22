#!/usr/bin/env python3
"""
Troubleshoot device connection issues for BluPow devices
"""
import asyncio
import sys
import struct
from pathlib import Path

# Add the custom_components directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "blupow"))

from blupow_client import BluPowClient

async def test_different_commands(mac_address):
    """Test different Renogy commands to find what works for this device"""
    print(f"🔧 Testing different commands for device: {mac_address}")
    
    # Different possible commands for Renogy devices
    commands_to_test = [
        # Standard controller command
        (bytes([0xFF, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD1, 0xF1]), "Standard controller (34 registers)"),
        
        # Shorter read
        (bytes([0xFF, 0x03, 0x01, 0x00, 0x00, 0x10, 0xD0, 0x3E]), "Shorter read (16 registers)"),
        
        # Different device IDs - some devices use different IDs
        (bytes([0x01, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD5, 0xE1]), "Device ID 0x01"),
        (bytes([0x11, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD0, 0x21]), "Device ID 0x11 (17)"),
        (bytes([0x20, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD6, 0x4C]), "Device ID 0x20 (32)"),
        (bytes([0x30, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD7, 0x6C]), "Device ID 0x30 (48)"),
        
        # Different register ranges
        (bytes([0xFF, 0x03, 0x00, 0x0A, 0x00, 0x0D, 0xA5, 0xCD]), "Registers 0x000A-0x0016"),
        (bytes([0xFF, 0x03, 0x01, 0x07, 0x00, 0x08, 0x35, 0xF0]), "Registers 0x0107-0x010E"),
    ]
    
    client = BluPowClient(mac_address)
    
    try:
        print("1. Connecting to device...")
        connected = await client.connect()
        
        if not connected:
            print("❌ Failed to connect to device")
            return
            
        print("✅ Device connected successfully")
        
        for cmd, description in commands_to_test:
            print(f"\n2. Testing: {description}")
            print(f"   Command: {cmd.hex()}")
            
            try:
                response = await client._send_command(cmd)
                
                if response:
                    print(f"   ✅ Response received: {len(response)} bytes")
                    print(f"   📊 Data: {response.hex()}")
                    
                    # Try to parse if it looks like valid data
                    if len(response) >= 7:
                        try:
                            parsed = client._parse_renogy_response(response)
                            if parsed and len(parsed) > 5:
                                print(f"   🎯 Successfully parsed {len(parsed)} fields!")
                                print("   📋 Sample data:")
                                for key, value in list(parsed.items())[:5]:
                                    print(f"      {key}: {value}")
                                return cmd, description, parsed
                        except Exception as e:
                            print(f"   ⚠️ Parse failed: {e}")
                else:
                    print(f"   ❌ No response")
                    
            except Exception as e:
                print(f"   ❌ Command failed: {e}")
                
            await asyncio.sleep(1)  # Wait between commands
            
        print("\n❌ No working command found")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        await client.disconnect()
        
    return None

async def test_device_discovery(mac_address):
    """Test basic device discovery and services"""
    print(f"\n🔍 Testing device discovery for: {mac_address}")
    
    try:
        from bleak import BleakClient, BleakScanner
        
        print("1. Scanning for device...")
        devices = await BleakScanner.discover(timeout=10.0)
        
        target_device = None
        for device in devices:
            if device.address.upper() == mac_address.upper():
                target_device = device
                break
                
        if not target_device:
            print(f"❌ Device {mac_address} not found in scan")
            return False
            
        print(f"✅ Device found: {target_device.name or 'Unknown'}")
        
        print("2. Connecting and checking services...")
        async with BleakClient(mac_address) as client:
            if not client.is_connected:
                print("❌ Failed to connect")
                return False
                
            print("✅ Connected, checking services...")
            
            services = await client.get_services()
            for service in services:
                print(f"   Service: {service.uuid}")
                for char in service.characteristics:
                    print(f"     Characteristic: {char.uuid} - {char.properties}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return False

async def main():
    """Main troubleshooting function"""
    problem_device = "D8:B6:73:BF:4F:75"
    working_device = "C4:D3:6A:66:7E:D4"
    
    print("🔧 BluPow Device Connection Troubleshoot")
    print("=" * 50)
    
    print(f"Problem device: {problem_device}")
    print(f"Working device: {working_device}")
    
    # Test the working device first to confirm our approach
    print("\n" + "=" * 50)
    print("🧪 Testing WORKING device first...")
    working_result = await test_different_commands(working_device)
    
    if working_result:
        cmd, desc, data = working_result
        print(f"\n✅ Working device uses: {desc}")
        print(f"   Command: {cmd.hex()}")
    else:
        print("\n⚠️ Even the working device failed - check Bluetooth")
        
    # Now test the problem device
    print("\n" + "=" * 50)
    print("🔧 Testing PROBLEM device...")
    
    # First do basic discovery
    discovery_ok = await test_device_discovery(problem_device)
    
    if discovery_ok:
        # Try different commands
        problem_result = await test_different_commands(problem_device)
        
        if problem_result:
            cmd, desc, data = problem_result
            print(f"\n🎯 SOLUTION FOUND!")
            print(f"Problem device needs: {desc}")
            print(f"Command: {cmd.hex()}")
            
            # Suggest the fix
            print(f"\n🔧 TO FIX:")
            print(f"Update the command in blupow_client.py read_device_info() method:")
            print(f"Replace: bytes([0xFF, 0x03, 0x01, 0x00, 0x00, 0x22, 0xD1, 0xF1])")
            print(f"With: {cmd}")
            
        else:
            print(f"\n❌ No working command found for problem device")
            print("This device may need a different protocol or be in a different mode")

if __name__ == "__main__":
    asyncio.run(main()) 