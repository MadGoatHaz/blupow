#!/usr/bin/env python3
"""
Smart BluPow Device Discovery & Configuration Assistant

This intelligent scanner will:
- Automatically detect Renogy devices by name patterns and service UUIDs
- Test connectivity to discovered devices
- Provide actionable configuration recommendations
- Generate Home Assistant configuration snippets
"""

import asyncio
import logging
import sys
from typing import Dict, List, Optional, Tuple
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# Renogy device identification patterns
RENOGY_PATTERNS = {
    'inverter': ['BTRIC', 'RIV'],
    'charge_controller': ['BT-TH-', 'ROVER', 'WANDERER', 'ADVENTURER'],
    'battery': ['RBT', 'BATTERY'],
    'dc_charger': ['RBC', 'DCC']
}

# Known Renogy service UUIDs (from cyrils/renogy-bt documentation)
RENOGY_SERVICE_UUIDS = [
    "0000ffd0-0000-1000-8000-00805f9b34fb",  # Primary service
    "0000fff0-0000-1000-8000-00805f9b34fb",  # Alternative service
]

RENOGY_CHARACTERISTIC_UUIDS = [
    "0000ffd1-0000-1000-8000-00805f9b34fb",  # Write characteristic
    "0000fff1-0000-1000-8000-00805f9b34fb",  # Notification characteristic
]

class SmartRenogyScanner:
    """Intelligent Renogy device scanner and configuration assistant."""
    
    def __init__(self):
        self.discovered_devices: List[Tuple[BLEDevice, AdvertisementData]] = []
        self.renogy_devices: Dict[str, Dict] = {}
        
    async def scan_for_devices(self, duration: int = 15) -> List[Tuple[BLEDevice, AdvertisementData]]:
        """Scan for all BLE devices."""
        _LOGGER.info("🔍 Starting intelligent device discovery...")
        _LOGGER.info(f"⏱️  Scanning for {duration} seconds...")
        
        devices = await BleakScanner.discover(timeout=duration, return_adv=True)
        self.discovered_devices = list(devices.values())
        
        _LOGGER.info(f"📡 Found {len(self.discovered_devices)} total BLE devices")
        return self.discovered_devices
    
    def identify_renogy_devices(self) -> Dict[str, Dict]:
        """Identify potential Renogy devices by name patterns."""
        _LOGGER.info("🎯 Analyzing devices for Renogy compatibility...")
        
        for device, adv_data in self.discovered_devices:
            device_name = device.name or "Unknown"
            device_type = self._classify_device(device_name)
            
            if device_type:
                self.renogy_devices[device.address] = {
                    'device': device,
                    'adv_data': adv_data,
                    'name': device_name,
                    'type': device_type,
                    'rssi': adv_data.rssi,
                    'connectable': False,
                    'services': [],
                    'characteristics': []
                }
                
        if self.renogy_devices:
            _LOGGER.info(f"🎉 Found {len(self.renogy_devices)} potential Renogy device(s)!")
            for addr, info in self.renogy_devices.items():
                _LOGGER.info(f"   📱 {info['name']} ({addr}) - Type: {info['type']}")
        else:
            _LOGGER.warning("⚠️  No Renogy devices detected by name pattern")
            
        return self.renogy_devices
    
    def _classify_device(self, name: str) -> Optional[str]:
        """Classify device type based on name patterns."""
        name_upper = name.upper()
        
        for device_type, patterns in RENOGY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_upper:
                    return device_type
        return None
    
    async def test_connectivity(self) -> Dict[str, Dict]:
        """Test connectivity to identified Renogy devices."""
        if not self.renogy_devices:
            _LOGGER.warning("⚠️  No Renogy devices to test")
            return {}
            
        _LOGGER.info("🔌 Testing connectivity to Renogy devices...")
        
        for addr, info in self.renogy_devices.items():
            _LOGGER.info(f"   🧪 Testing {info['name']} ({addr})...")
            
            try:
                async with BleakClient(info['device']) as client:
                    if client.is_connected:
                        info['connectable'] = True
                        
                        # Get services and characteristics
                        services = client.services
                        info['services'] = [str(service.uuid) for service in services]
                        
                        # Check for Renogy-specific services
                        renogy_services = [uuid for uuid in info['services'] 
                                         if uuid.lower() in [s.lower() for s in RENOGY_SERVICE_UUIDS]]
                        
                        if renogy_services:
                            info['renogy_services'] = renogy_services
                            _LOGGER.info(f"   ✅ {info['name']}: Connected successfully with Renogy services!")
                        else:
                            _LOGGER.info(f"   ⚠️  {info['name']}: Connected but no Renogy services detected")
                            
                    else:
                        _LOGGER.warning(f"   ❌ {info['name']}: Connection failed")
                        
            except Exception as e:
                _LOGGER.warning(f"   ❌ {info['name']}: Connection error - {str(e)}")
                info['error'] = str(e)
                
        return self.renogy_devices
    
    def generate_recommendations(self) -> None:
        """Generate actionable recommendations based on scan results."""
        _LOGGER.info("\n" + "="*80)
        _LOGGER.info("🎯 SMART CONFIGURATION RECOMMENDATIONS")
        _LOGGER.info("="*80)
        
        if not self.renogy_devices:
            _LOGGER.error("❌ No Renogy devices found!")
            _LOGGER.info("\n💡 TROUBLESHOOTING SUGGESTIONS:")
            _LOGGER.info("   1. Ensure your Renogy device is powered on")
            _LOGGER.info("   2. Check if device has a Bluetooth activation button")
            _LOGGER.info("   3. Move closer to the device (within 10 meters)")
            _LOGGER.info("   4. Verify device model supports Bluetooth (BT-1/BT-2 module)")
            return
            
        connectable_devices = {addr: info for addr, info in self.renogy_devices.items() 
                             if info['connectable']}
        
        if connectable_devices:
            _LOGGER.info("✅ READY FOR HOME ASSISTANT CONFIGURATION:")
            _LOGGER.info("")
            
            for addr, info in connectable_devices.items():
                _LOGGER.info(f"📱 Device: {info['name']}")
                _LOGGER.info(f"   📍 MAC Address: {addr}")
                _LOGGER.info(f"   🔧 Device Type: {info['type']}")
                _LOGGER.info(f"   📶 Signal Strength: {info['rssi']} dBm")
                
                if info.get('renogy_services'):
                    _LOGGER.info(f"   ✅ Renogy Services: Found")
                    _LOGGER.info(f"\n   🏠 HOME ASSISTANT CONFIGURATION:")
                    _LOGGER.info(f"      1. Go to Settings → Devices & Services")
                    _LOGGER.info(f"      2. Click '+ ADD INTEGRATION'")
                    _LOGGER.info(f"      3. Search for 'BluPow'")
                    _LOGGER.info(f"      4. Enter MAC address: {addr}")
                else:
                    _LOGGER.info(f"   ⚠️  No Renogy services detected - may need protocol investigation")
                    
                _LOGGER.info("")
                
        else:
            _LOGGER.warning("⚠️  Renogy devices found but none are connectable")
            _LOGGER.info("\n💡 TROUBLESHOOTING SUGGESTIONS:")
            for addr, info in self.renogy_devices.items():
                _LOGGER.info(f"   📱 {info['name']} ({addr}):")
                if 'error' in info:
                    _LOGGER.info(f"      ❌ Error: {info['error']}")
                _LOGGER.info(f"      💡 Try power cycling the device")
                _LOGGER.info(f"      💡 Ensure device is not paired with another system")
                
        # Show all devices for reference
        _LOGGER.info("\n📋 ALL DISCOVERED DEVICES:")
        for device, adv_data in self.discovered_devices:
            name = device.name or "Unknown"
            rssi = adv_data.rssi
            status = "🎯 Renogy" if device.address in self.renogy_devices else "📱 Other"
            _LOGGER.info(f"   {status} - {name} ({device.address}) - {rssi} dBm")

async def main():
    """Main scanning and analysis routine."""
    scanner = SmartRenogyScanner()
    
    try:
        # Step 1: Scan for all devices
        await scanner.scan_for_devices(duration=15)
        
        # Step 2: Identify Renogy devices
        scanner.identify_renogy_devices()
        
        # Step 3: Test connectivity
        await scanner.test_connectivity()
        
        # Step 4: Generate recommendations
        scanner.generate_recommendations()
        
    except KeyboardInterrupt:
        _LOGGER.info("\n⏹️  Scan interrupted by user")
    except Exception as e:
        _LOGGER.error(f"❌ Scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 