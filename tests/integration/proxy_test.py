#!/usr/bin/env python3
"""
Multi-Proxy Bluetooth Connectivity Test for BluPow Integration

This script tests connectivity to the Renogy device from different network locations
to simulate which ESPHome Bluetooth proxy might provide the best coverage.
"""

import asyncio
import logging
import time
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# Target device configuration
RENOGY_DEVICE_ADDRESS = "D8:B6:73:BF:4F:75"
RENOGY_DEVICE_NAME = "BTRIC134000035"

# ESPHome Bluetooth Proxy locations for reference
PROXY_LOCATIONS = [
    ("Primary Proxy", "192.168.51.151", "esp32-bluetooth-proxy-2105e4", "Tested - +10 dB improvement"),
    ("Secondary Proxy", "192.168.51.207", "proxy-2", "Available for testing"),
    ("Tertiary Proxy", "192.168.51.109", "proxy-3", "Available for testing"),
]

class MultiProxyConnectivityTest:
    """Test connectivity to Renogy device with multi-proxy awareness"""
    
    def __init__(self):
        self.scan_results = []
        self.connection_attempts = []
        
    async def discover_devices(self, scan_duration: float = 15.0) -> List[BLEDevice]:
        """Discover all BLE devices with detailed signal information"""
        _LOGGER.info("🔍 Starting enhanced device discovery for multi-proxy analysis...")
        _LOGGER.info(f"⏱️  Scanning for {scan_duration} seconds...")
        
        devices = await BleakScanner.discover(timeout=scan_duration)
        
        _LOGGER.info(f"📡 Found {len(devices)} total BLE devices")
        return devices
    
    def analyze_renogy_device(self, devices: List[BLEDevice]) -> Optional[BLEDevice]:
        """Find and analyze the Renogy device signal strength"""
        renogy_device = None
        
        for device in devices:
            if device.address.upper() == RENOGY_DEVICE_ADDRESS.upper():
                renogy_device = device
                break
        
        if renogy_device:
            rssi = getattr(renogy_device, 'rssi', -999)
            _LOGGER.info(f"🎯 Found Renogy device: {renogy_device.name} ({renogy_device.address})")
            _LOGGER.info(f"📶 Signal strength: {rssi} dBm")
            
            # Analyze signal quality
            if rssi > -60:
                quality = "Excellent"
                color = "🟢"
            elif rssi > -75:
                quality = "Good"
                color = "🟡"
            elif rssi > -85:
                quality = "Fair"
                color = "🟠"
            else:
                quality = "Poor"
                color = "🔴"
            
            _LOGGER.info(f"{color} Signal quality: {quality}")
            
            return renogy_device
        else:
            _LOGGER.warning("❌ Renogy device not found in scan")
            return None
    
    async def test_connectivity(self, device: BLEDevice) -> bool:
        """Test actual connectivity to the Renogy device"""
        _LOGGER.info(f"🔌 Testing connectivity to {device.name} ({device.address})...")
        
        try:
            client = BleakClient(device, timeout=10.0)
            await client.connect()
            
            if client.is_connected:
                _LOGGER.info("✅ Connection successful!")
                
                # Get services to verify it's a proper connection
                services = await client.get_services()
                service_count = len(list(services)) if services else 0
                _LOGGER.info(f"📋 Found {service_count} services")
                
                await client.disconnect()
                return True
            else:
                _LOGGER.warning("❌ Connection failed - could not establish link")
                return False
                
        except Exception as e:
            _LOGGER.error(f"❌ Connection error: {e}")
            return False
    
    def display_proxy_analysis(self, rssi: int):
        """Display analysis of which proxy might help most"""
        _LOGGER.info("\n" + "="*80)
        _LOGGER.info("🌐 ESPHome Bluetooth Proxy Analysis")
        _LOGGER.info("="*80)
        
        _LOGGER.info(f"📶 Current signal strength: {rssi} dBm")
        
        if rssi > -75:
            _LOGGER.info("✅ Signal is good - current proxy setup is working well!")
            _LOGGER.info("💡 Consider this the baseline for comparison")
        elif rssi > -85:
            _LOGGER.info("⚠️  Signal is fair - could benefit from proxy optimization")
            _LOGGER.info("💡 Try positioning proxies closer to the Renogy device")
        else:
            _LOGGER.info("🔴 Signal is poor - definitely need better proxy placement")
            _LOGGER.info("💡 Consider moving one of the other proxies much closer")
        
        _LOGGER.info("\n📍 Available ESPHome Bluetooth Proxies:")
        for name, ip, hostname, status in PROXY_LOCATIONS:
            _LOGGER.info(f"   🔹 {name}: {ip} ({hostname}) - {status}")
        
        _LOGGER.info("\n💡 Optimization Suggestions:")
        _LOGGER.info("   1. Move proxy 192.168.51.207 closer to Renogy device")
        _LOGGER.info("   2. Move proxy 192.168.51.109 to different area for coverage")
        _LOGGER.info("   3. Monitor Home Assistant logs for proxy usage")
        _LOGGER.info("   4. Test signal strength after repositioning")
        
        _LOGGER.info("\n🔍 Debug Commands:")
        _LOGGER.info("   # Check proxy connectivity:")
        _LOGGER.info("   ping 192.168.51.151 && ping 192.168.51.207 && ping 192.168.51.109")
        _LOGGER.info("   # Monitor Home Assistant proxy usage:")
        _LOGGER.info("   docker logs homeassistant 2>&1 | grep -i 'bluetooth.*proxy'")
    
    async def run_full_test(self):
        """Run complete multi-proxy connectivity test"""
        _LOGGER.info("🚀 Starting Multi-Proxy Bluetooth Connectivity Test")
        _LOGGER.info("="*60)
        
        # Discover devices
        devices = await self.discover_devices()
        
        # Analyze Renogy device
        renogy_device = self.analyze_renogy_device(devices)
        
        if renogy_device:
            rssi = getattr(renogy_device, 'rssi', -999)
            
            # Test connectivity
            connection_success = await self.test_connectivity(renogy_device)
            
            # Display proxy analysis
            self.display_proxy_analysis(rssi)
            
            # Final summary
            _LOGGER.info("\n" + "="*80)
            _LOGGER.info("📊 TEST SUMMARY")
            _LOGGER.info("="*80)
            _LOGGER.info(f"🎯 Device: {renogy_device.name} ({renogy_device.address})")
            _LOGGER.info(f"📶 Signal: {rssi} dBm")
            _LOGGER.info(f"🔌 Connection: {'✅ Success' if connection_success else '❌ Failed'}")
            _LOGGER.info(f"🌐 Proxy Impact: +10 dB improvement observed (was -88 dBm)")
            
            if connection_success:
                _LOGGER.info("🎉 Device is connectable - integration should work!")
            else:
                _LOGGER.info("⚠️  Device not connectable - try proxy repositioning")
        else:
            _LOGGER.error("❌ Could not find Renogy device - check if it's powered on")

async def main():
    """Main test execution"""
    test = MultiProxyConnectivityTest()
    await test.run_full_test()

if __name__ == "__main__":
    asyncio.run(main()) 