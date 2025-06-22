#!/usr/bin/env python3
"""
Test inverter-specific commands for RIV1230RCH-SPS
"""
import asyncio
import sys
import struct
from pathlib import Path

# Add the custom_components directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "blupow"))

from blupow_client import BluPowClient

async def test_inverter_commands(mac_address):
    """Test different register ranges for inverter devices"""
    print(f"🔧 Testing inverter commands for: {mac_address}")
    
    # Inverter-specific register ranges (different from controllers)
    inverter_commands = [
        # Different register ranges for inverters
        (bytes([0xFF, 0x03, 0x00, 0x00, 0x00, 0x0C, 0x44, 0x08]), "Registers 0x0000-0x000B (12 regs)"),
        (bytes([0xFF, 0x03, 0x00, 0x0C, 0x00, 0x0C, 0x44, 0x09]), "Registers 0x000C-0x0017 (12 regs)"),
        (bytes([0xFF, 0x03, 0x00, 0x18, 0x00, 0x0C, 0x44, 0x0C]), "Registers 0x0018-0x0023 (12 regs)"),
        (bytes([0xFF, 0x03, 0x00, 0x24, 0x00, 0x0C, 0x44, 0x0E]), "Registers 0x0024-0x002F (12 regs)"),
        
        # Try standard ranges with different device IDs
        (bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x0C, 0x44, 0x38]), "Device ID 0x01, regs 0x0000-0x000B"),
        (bytes([0x20, 0x03, 0x00, 0x00, 0x00, 0x0C, 0x44, 0x6C]), "Device ID 0x20, regs 0x0000-0x000B"),
        (bytes([0x32, 0x03, 0x00, 0x00, 0x00, 0x0C, 0x44, 0x4F]), "Device ID 0x32, regs 0x0000-0x000B"),
        
        # Shorter reads
        (bytes([0xFF, 0x03, 0x00, 0x00, 0x00, 0x06, 0x44, 0x1B]), "First 6 registers"),
        (bytes([0xFF, 0x03, 0x00, 0x00, 0x00, 0x04, 0x44, 0x1C]), "First 4 registers"),
        (bytes([0xFF, 0x03, 0x00, 0x00, 0x00, 0x02, 0x44, 0x1F]), "First 2 registers"),
        
        # Basic device info queries
        (bytes([0xFF, 0x03, 0x00, 0x64, 0x00, 0x04, 0x44, 0x15]), "Device info registers"),
        (bytes([0xFF, 0x03, 0x00, 0x6A, 0x00, 0x02, 0x44, 0x11]), "Model/version registers"),
    ]
    
    client = BluPowClient(mac_address)
    
    try:
        print("1. Connecting to device...")
        connected = await client.connect()
        
        if not connected:
            print("❌ Failed to connect to device")
            return None
            
        print("✅ Device connected successfully")
        
        for cmd, description in inverter_commands:
            print(f"\n2. Testing: {description}")
            print(f"   Command: {cmd.hex()}")
            
            try:
                response = await client._send_command(cmd)
                
                if response and len(response) > 5:
                    print(f"   ✅ Valid response: {len(response)} bytes")
                    print(f"   📊 Data: {response.hex()}")
                    
                    # Try to extract meaningful data
                    if len(response) >= 7 and response[1] == 0x03:  # Valid read response
                        try:
                            # Parse raw values
                            data_start = 3  # Skip device_id, function_code, byte_count
                            data_bytes = response[data_start:-2]  # Remove CRC
                            
                            values = []
                            for i in range(0, len(data_bytes), 2):
                                if i + 1 < len(data_bytes):
                                    val = struct.unpack('>H', data_bytes[i:i+2])[0]
                                    values.append(val)
                            
                            print(f"   📋 Parsed {len(values)} values: {values}")
                            
                            # Look for reasonable values
                            reasonable_values = []
                            for val in values:
                                if 0 <= val <= 5000:  # Reasonable range
                                    reasonable_values.append(val)
                                    
                            if reasonable_values:
                                print(f"   🎯 Reasonable values found: {reasonable_values}")
                                return cmd, description, response
                                
                        except Exception as e:
                            print(f"   ⚠️ Parse error: {e}")
                            
                elif response:
                    print(f"   ❌ Error response: {response.hex()}")
                    if len(response) >= 3 and response[1] == 0x83:
                        error_code = response[2]
                        errors = {
                            0x01: "Illegal Function",
                            0x02: "Illegal Data Address", 
                            0x03: "Illegal Data Value",
                            0x04: "Server Device Failure"
                        }
                        print(f"   📋 Modbus error: {errors.get(error_code, f'Unknown ({error_code})')}")
                else:
                    print(f"   ❌ No response")
                    
            except Exception as e:
                print(f"   ❌ Command failed: {e}")
                
            await asyncio.sleep(0.5)  # Wait between commands
            
        print("\n❌ No valid data response found")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        await client.disconnect()
        
    return None

async def main():
    """Test the problematic inverter device"""
    inverter_device = "D8:B6:73:BF:4F:75"  # BTRIC134000035
    
    print("🔧 Inverter Device Command Testing")
    print("=" * 50)
    print(f"Testing device: {inverter_device} (BTRIC134000035)")
    print("Device type: RIV1230RCH-SPS Inverter")
    
    result = await test_inverter_commands(inverter_device)
    
    if result:
        cmd, desc, response = result
        print(f"\n🎯 SUCCESS! Working command found:")
        print(f"Description: {desc}")
        print(f"Command: {cmd.hex()}")
        print(f"Response: {response.hex()}")
        
        print(f"\n🔧 TO FIX THE INTEGRATION:")
        print(f"Update blupow_client.py read_device_info() method:")
        print(f"Replace the command for this device with: {cmd}")
        
    else:
        print(f"\n❌ No working command found")
        print("This inverter may need a different communication approach")

if __name__ == "__main__":
    asyncio.run(main()) 