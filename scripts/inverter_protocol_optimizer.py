#!/usr/bin/env python3
"""
🔧 INVERTER PROTOCOL OPTIMIZER
Get the BTRIC134000035 inverter data working properly

Based on device scan results, the inverter has:
- Service: 0000ffd0-0000-1000-8000-00805f9b34fb
- TX: 0000ffd1-0000-1000-8000-00805f9b34fb (write)
- RX: 0000ffd2-0000-1000-8000-00805f9b34fb (notify)

This script will test different register addresses and protocols.
"""

import asyncio
import struct
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bleak import BleakClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InverterProtocolOptimizer:
    """Optimize protocol for BTRIC134000035 inverter"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client = None
        
        # BLE characteristics from device scan
        self.service_uuid = "0000ffd0-0000-1000-8000-00805f9b34fb"
        self.tx_char = "0000ffd1-0000-1000-8000-00805f9b34fb"
        self.rx_char = "0000ffd2-0000-1000-8000-00805f9b34fb"
        
        # Response handling
        self.response_data = bytearray()
        self.response_received = False
        
        # Protocol variants to test
        self.register_variants = [
            # Standard Renogy registers
            {'register': 256, 'words': 34, 'description': 'Standard BT-TH registers'},
            {'register': 5000, 'words': 20, 'description': 'Inverter status registers'},
            {'register': 5017, 'words': 8, 'description': 'Inverter power registers'},
            {'register': 5030, 'words': 10, 'description': 'Inverter battery registers'},
            
            # Try different starting points
            {'register': 1, 'words': 10, 'description': 'Low register test'},
            {'register': 100, 'words': 15, 'description': 'Mid register test'},
            {'register': 500, 'words': 12, 'description': 'High register test'},
            
            # Try single registers
            {'register': 256, 'words': 1, 'description': 'Single register 256'},
            {'register': 5000, 'words': 1, 'description': 'Single register 5000'},
        ]

    async def notification_handler(self, sender, data: bytearray):
        """Handle notifications from device"""
        self.response_data.extend(data)
        self.response_received = True
        logger.debug(f"Received {len(data)} bytes: {data.hex()}")

    def calculate_crc(self, data: bytes) -> int:
        """Calculate CRC16 for Modbus"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def create_read_command(self, register: int, words: int, device_id: int = 255) -> bytes:
        """Create Modbus read command"""
        # Modbus function code 0x03 (Read Holding Registers)
        command = struct.pack('>BBHHi', device_id, 0x03, register, words, 0)
        command = command[:-4]  # Remove the extra padding
        
        # Calculate and append CRC
        crc = self.calculate_crc(command)
        command += struct.pack('<H', crc)  # Little-endian CRC
        
        return command

    async def test_register_variant(self, variant: dict) -> bool:
        """Test a specific register variant"""
        register = variant['register']
        words = variant['words']
        description = variant['description']
        
        logger.info(f"🧪 Testing: {description} (reg:{register}, words:{words})")
        
        try:
            # Clear previous response
            self.response_data.clear()
            self.response_received = False
            
            # Create command
            command = self.create_read_command(register, words)
            logger.debug(f"Command: {command.hex()}")
            
            # Send command
            await self.client.write_gatt_char(self.tx_char, command)
            
            # Wait for response
            timeout_start = asyncio.get_event_loop().time()
            while not self.response_received and (asyncio.get_event_loop().time() - timeout_start) < 3.0:
                await asyncio.sleep(0.1)
            
            if self.response_received and len(self.response_data) > 0:
                logger.info(f"✅ Response received: {len(self.response_data)} bytes")
                logger.info(f"   Data: {self.response_data.hex()}")
                
                # Try to parse as meaningful data
                if self.analyze_response(self.response_data, variant):
                    return True
                    
            else:
                logger.debug(f"❌ No response for {description}")
                
        except Exception as e:
            logger.debug(f"❌ Error testing {description}: {e}")
            
        return False

    def analyze_response(self, data: bytes, variant: dict) -> bool:
        """Analyze response data for meaningful values"""
        if len(data) < 5:
            return False
            
        try:
            # Check if it looks like Modbus response
            if data[0] == 255 and data[1] == 0x03:  # Device ID and function code
                payload_length = data[2]
                if len(data) >= payload_length + 5:  # +3 for header, +2 for CRC
                    payload = data[3:3+payload_length]
                    
                    logger.info(f"📊 Modbus response detected:")
                    logger.info(f"   Device ID: {data[0]}")
                    logger.info(f"   Function: {data[1]}")
                    logger.info(f"   Length: {payload_length}")
                    logger.info(f"   Payload: {payload.hex()}")
                    
                    # Try to extract meaningful values
                    values = self.extract_values(payload)
                    if values:
                        logger.info(f"🎉 Extracted values: {values}")
                        return True
                        
        except Exception as e:
            logger.debug(f"Error analyzing response: {e}")
            
        return False

    def extract_values(self, payload: bytes) -> dict:
        """Extract meaningful values from payload"""
        values = {}
        
        try:
            # Try interpreting as 16-bit big-endian values
            if len(payload) >= 2:
                for i in range(0, len(payload)-1, 2):
                    if i + 1 < len(payload):
                        value = struct.unpack('>H', payload[i:i+2])[0]
                        # Look for reasonable values
                        if 0 < value < 65000:  # Skip obviously invalid values
                            values[f'register_{i//2}'] = value
                            
                            # Guess what common values might be
                            if 100 <= value <= 150:  # Possible voltage (12V system = 120-140)
                                values[f'possible_voltage_{i//2}'] = value / 10.0
                            elif 0 < value <= 100:  # Possible percentage
                                values[f'possible_percentage_{i//2}'] = value
                                
        except Exception as e:
            logger.debug(f"Error extracting values: {e}")
            
        return values

    async def optimize_protocol(self) -> dict:
        """Run full protocol optimization"""
        logger.info(f"🚀 Starting protocol optimization for {self.mac_address}")
        
        results = {
            'device_mac': self.mac_address,
            'connection_successful': False,
            'working_variants': [],
            'best_variant': None,
            'extracted_data': {}
        }
        
        try:
            # Connect to device
            self.client = BleakClient(self.mac_address)
            await self.client.connect()
            
            if not self.client.is_connected:
                logger.error("Failed to connect")
                return results
                
            results['connection_successful'] = True
            logger.info("✅ Connected to inverter")
            
            # Start notifications
            await self.client.start_notify(self.rx_char, self.notification_handler)
            logger.info("✅ Notifications started")
            
            # Test each register variant
            for variant in self.register_variants:
                if await self.test_register_variant(variant):
                    results['working_variants'].append(variant)
                    
                    if not results['best_variant']:
                        results['best_variant'] = variant
                        
                await asyncio.sleep(1)  # Delay between tests
            
            # Disconnect
            await self.client.disconnect()
            logger.info("🔌 Disconnected")
            
            # Summary
            if results['working_variants']:
                logger.info(f"🎉 Found {len(results['working_variants'])} working variants!")
                logger.info(f"Best variant: {results['best_variant']['description']}")
            else:
                logger.warning("❌ No working variants found")
                
        except Exception as e:
            logger.error(f"Protocol optimization error: {e}")
            
        return results

async def main():
    """Run inverter protocol optimization"""
    mac = "D8:B6:73:BF:4F:75"  # BTRIC134000035
    
    optimizer = InverterProtocolOptimizer(mac)
    results = await optimizer.optimize_protocol()
    
    print("\n" + "="*60)
    print("🔧 INVERTER PROTOCOL OPTIMIZATION RESULTS")
    print("="*60)
    
    if results['connection_successful']:
        print("✅ Connection: SUCCESS")
        
        if results['working_variants']:
            print(f"✅ Working protocols: {len(results['working_variants'])}")
            print(f"🎯 Best protocol: {results['best_variant']['description']}")
            print(f"   Register: {results['best_variant']['register']}")
            print(f"   Words: {results['best_variant']['words']}")
        else:
            print("❌ No working protocols found")
            print("💡 Device may need different protocol or activation")
    else:
        print("❌ Connection: FAILED")
    
    # Save results
    import json
    with open("inverter_protocol_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: inverter_protocol_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 