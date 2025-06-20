#!/usr/bin/env python3
"""
BluPow Comprehensive Device Discovery & Hardware Testing System

This intelligent system will:
- Scan for all Bluetooth devices with detailed analysis
- Identify Renogy devices using Cyril's renogy-bt patterns
- Test connectivity with different Bluetooth proxies
- Provide hardware recommendations and MAC address selection
- Generate Home Assistant configuration suggestions
- Support multiple Renogy device types (controllers, batteries, inverters)

Based on cyrils/renogy-bt patterns and protocols
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    from bleak.exc import BleakError
except ImportError:
    print("Error: bleak library not found. Please install it with:")
    print("  pip install bleak")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Renogy Device Patterns (from cyrils/renogy-bt)
RENOGY_DEVICE_PATTERNS = {
    'charge_controller': {
        'patterns': ['BT-TH-', 'ROVER', 'WANDERER', 'ADVENTURER', 'RNG-CTRL'],
        'description': 'Solar Charge Controller',
        'typical_models': ['RNG-CTRL-RVR40', 'RNG-CTRL-WND10', 'ROVER-20A', 'ROVER-40A']
    },
    'inverter': {
        'patterns': ['BTRIC', 'RIV'],
        'description': 'Power Inverter',
        'typical_models': ['RIV1230RCH-SPS', 'RIV4835CSH1S']
    },
    'battery': {
        'patterns': ['RBT', 'BATTERY'],
        'description': 'Smart Battery',
        'typical_models': ['RBT100LFP12S-G', 'RBT100LFP12-BT', 'RBT200LFP12-BT']
    },
    'dc_charger': {
        'patterns': ['RBC', 'DCC'],
        'description': 'DC-DC Charger',
        'typical_models': ['RBC50D1S-G1', 'DCC30S', 'DCC50S']
    }
}

# Known Renogy Bluetooth UUIDs (from cyrils/renogy-bt)
RENOGY_SERVICE_UUIDS = [
    "0000ffd0-0000-1000-8000-00805f9b34fb",  # Primary service
    "0000fff0-0000-1000-8000-00805f9b34fb",  # Alternative service
]

RENOGY_CHARACTERISTIC_UUIDS = [
    "0000ffd1-0000-1000-8000-00805f9b34fb",  # Write characteristic (TX)
    "0000fff1-0000-1000-8000-00805f9b34fb",  # Notification characteristic (RX)
]

RENOGY_MANUFACTURER_ID = 0x7DE0  # Renogy manufacturer ID

# ESPHome Bluetooth Proxy patterns
PROXY_PATTERNS = ['esphome', 'bluetooth-proxy', 'esp32-proxy', 'proxy']

@dataclass
class DeviceInfo:
    """Comprehensive device information"""
    address: str
    name: str
    device_type: Optional[str]
    rssi: int
    is_renogy: bool
    is_proxy: bool
    connectable: bool
    connection_time: Optional[float]
    services: List[str]
    characteristics: List[str]
    renogy_services: List[str]
    manufacturer_data: Dict[int, bytes]
    service_data: Dict[str, bytes]
    error: Optional[str]
    recommendation_score: int
    compatibility_notes: List[str]

@dataclass
class ProxyInfo:
    """Bluetooth proxy information"""
    name: str
    ip_address: str
    description: str
    status: str
    signal_improvement: Optional[str]

@dataclass
class TestResults:
    """Comprehensive test results"""
    timestamp: datetime
    scan_duration: float
    total_devices: int
    renogy_devices: int
    proxy_devices: int
    connectable_devices: int
    recommended_devices: List[DeviceInfo]
    environment_analysis: Dict[str, Any]
    recommendations: List[str]

class BluPowDeviceDiscoverySystem:
    """Comprehensive device discovery and testing system"""
    
    def __init__(self):
        self.discovered_devices: Dict[str, DeviceInfo] = {}
        self.proxy_devices: Dict[str, DeviceInfo] = {}
        self.test_results: Optional[TestResults] = None
        
        # Known ESPHome Bluetooth Proxies (from user's setup)
        self.known_proxies = [
            ProxyInfo("esp32-bluetooth-proxy-2105e4", "192.168.51.151", 
                     "Primary proxy - tested +10 dB improvement", "active", "+10 dB"),
            ProxyInfo("proxy-2", "192.168.51.207", 
                     "Secondary proxy - available for testing", "available", None),
            ProxyInfo("proxy-3", "192.168.51.109", 
                     "Tertiary proxy - available for testing", "available", None),
        ]
        
    async def comprehensive_scan(self, duration: float = 20.0, total_timeout: float = 60.0) -> Dict[str, DeviceInfo]:
        """Perform comprehensive device discovery with retries until a Renogy device is found."""
        _LOGGER.info("🚀 Starting BluPow Comprehensive Device Discovery System")
        _LOGGER.info("="*80)
        _LOGGER.info(f"⏱️  Scanning for Renogy devices for up to {total_timeout} seconds...")
        
        start_time = time.time()
        
        while time.time() - start_time < total_timeout:
            try:
                # Discover devices with advertisement data
                discovered = await BleakScanner.discover(timeout=duration, return_adv=True)
                
                scan_time = time.time() - start_time
                _LOGGER.info(f"📡 Discovered {len(discovered)} devices in this scan cycle ({scan_time:.1f}s elapsed)")
                
                # Analyze each device
                renogy_found = False
                for device, adv_data in discovered.values():
                    device_info = self._analyze_device(device, adv_data)
                    self.discovered_devices[device.address] = device_info
                    
                    if device_info.is_renogy:
                        renogy_found = True
                    
                    if device_info.is_proxy:
                        self.proxy_devices[device.address] = device_info
                
                if renogy_found:
                    _LOGGER.info("✅ Found at least one Renogy device. Proceeding with analysis.")
                    return self.discovered_devices
                        
            except Exception as e:
                _LOGGER.error(f"❌ Discovery cycle failed: {e}")

            _LOGGER.info("... No Renogy devices found yet, rescanning ...")
            await asyncio.sleep(5) # Wait 5 seconds before next scan

        _LOGGER.warning("⚠️  Timed out searching for Renogy devices.")
        return self.discovered_devices
    
    def _analyze_device(self, device: BLEDevice, adv_data: AdvertisementData) -> DeviceInfo:
        """Analyze individual device for Renogy compatibility"""
        name = device.name or "Unknown"
        address = device.address
        rssi = adv_data.rssi if hasattr(adv_data, 'rssi') else -999
        
        # Check if device is Renogy
        is_renogy, device_type = self._identify_renogy_device(device, adv_data)
        
        # Check if device is proxy
        is_proxy = self._is_bluetooth_proxy(device)
        
        # Get advertisement data
        manufacturer_data = getattr(adv_data, 'manufacturer_data', {})
        service_data = getattr(adv_data, 'service_data', {})
        service_uuids = getattr(adv_data, 'service_uuids', [])
        
        # Calculate recommendation score
        recommendation_score = self._calculate_recommendation_score(
            device, adv_data, is_renogy, device_type, rssi
        )
        
        # Generate compatibility notes
        compatibility_notes = self._generate_compatibility_notes(
            device, adv_data, is_renogy, device_type
        )
        
        return DeviceInfo(
            address=address,
            name=name,
            device_type=device_type,
            rssi=rssi,
            is_renogy=is_renogy,
            is_proxy=is_proxy,
            connectable=False,  # Will be tested later
            connection_time=None,
            services=[],
            characteristics=[],
            renogy_services=[],
            manufacturer_data=manufacturer_data,
            service_data=service_data,
            error=None,
            recommendation_score=recommendation_score,
            compatibility_notes=compatibility_notes
        )
    
    def _identify_renogy_device(self, device: BLEDevice, adv_data: AdvertisementData) -> Tuple[bool, Optional[str]]:
        """Identify if device is Renogy and determine type"""
        if not device.name:
            return False, None
            
        name = device.name.upper()
        
        # Check manufacturer data
        manufacturer_data = getattr(adv_data, 'manufacturer_data', {})
        if RENOGY_MANUFACTURER_ID in manufacturer_data:
            _LOGGER.debug(f"Found Renogy manufacturer ID in {device.name}")
            return True, self._classify_by_name(name)
        
        # Check service UUIDs
        service_uuids = getattr(adv_data, 'service_uuids', [])
        for uuid in service_uuids:
            if uuid.lower() in [s.lower() for s in RENOGY_SERVICE_UUIDS]:
                _LOGGER.debug(f"Found Renogy service UUID in {device.name}")
                return True, self._classify_by_name(name)
        
        # Check name patterns
        for device_type, config in RENOGY_DEVICE_PATTERNS.items():
            for pattern in config['patterns']:
                if pattern in name:
                    _LOGGER.debug(f"Found Renogy name pattern '{pattern}' in {device.name}")
                    return True, device_type
        
        return False, None
    
    def _classify_by_name(self, name: str) -> Optional[str]:
        """Classify device type by name patterns"""
        name = name.upper()
        
        for device_type, config in RENOGY_DEVICE_PATTERNS.items():
            for pattern in config['patterns']:
                if pattern in name:
                    return device_type
        
        return 'unknown_renogy'
    
    def _is_bluetooth_proxy(self, device: BLEDevice) -> bool:
        """Check if device is a Bluetooth proxy"""
        if not device.name:
            return False
            
        name = device.name.lower()
        return any(pattern in name for pattern in PROXY_PATTERNS)
    
    def _calculate_recommendation_score(self, device: BLEDevice, adv_data: AdvertisementData, 
                                      is_renogy: bool, device_type: Optional[str], rssi: int) -> int:
        """Calculate recommendation score for device"""
        score = 0
        
        if is_renogy:
            score += 50
            
        if device_type == 'charge_controller':
            score += 20  # Preferred for energy dashboard
        elif device_type in ['battery', 'inverter']:
            score += 15
        elif device_type == 'dc_charger':
            score += 10
            
        # Signal strength scoring
        if rssi > -60:
            score += 20  # Excellent
        elif rssi > -75:
            score += 15  # Good
        elif rssi > -85:
            score += 10  # Fair
        else:
            score += 5   # Poor
            
        # Bonus for known service UUIDs
        service_uuids = getattr(adv_data, 'service_uuids', [])
        for uuid in service_uuids:
            if uuid.lower() in [s.lower() for s in RENOGY_SERVICE_UUIDS]:
                score += 10
                
        # Bonus for manufacturer data
        manufacturer_data = getattr(adv_data, 'manufacturer_data', {})
        if RENOGY_MANUFACTURER_ID in manufacturer_data:
            score += 15
            
        return score
    
    def _generate_compatibility_notes(self, device: BLEDevice, adv_data: AdvertisementData,
                                    is_renogy: bool, device_type: Optional[str]) -> List[str]:
        """Generate compatibility and recommendation notes"""
        notes = []
        
        if is_renogy:
            notes.append("✅ Confirmed Renogy device")
            
            if device_type:
                device_config = RENOGY_DEVICE_PATTERNS.get(device_type, {})
                description = device_config.get('description', 'Unknown Type')
                notes.append(f"📱 Device Type: {description}")
                
                typical_models = device_config.get('typical_models', [])
                if typical_models:
                    notes.append(f"🏷️  Typical Models: {', '.join(typical_models[:3])}")
        
        # Check service UUIDs
        service_uuids = getattr(adv_data, 'service_uuids', [])
        renogy_services = [uuid for uuid in service_uuids 
                          if uuid.lower() in [s.lower() for s in RENOGY_SERVICE_UUIDS]]
        if renogy_services:
            notes.append(f"🔧 Renogy Services Found: {len(renogy_services)}")
        
        # Signal quality assessment
        rssi = getattr(adv_data, 'rssi', -999)
        if rssi > -60:
            notes.append("📶 Signal: Excellent")
        elif rssi > -75:
            notes.append("📶 Signal: Good")
        elif rssi > -85:
            notes.append("📶 Signal: Fair - consider proxy")
        else:
            notes.append("📶 Signal: Poor - proxy recommended")
            
        return notes
    
    async def test_connectivity(self) -> Dict[str, DeviceInfo]:
        """Test connectivity to discovered Renogy devices"""
        _LOGGER.info("🔌 Testing connectivity to Renogy devices...")
        
        renogy_devices = {addr: info for addr, info in self.discovered_devices.items() 
                         if info.is_renogy}
        
        if not renogy_devices:
            _LOGGER.warning("⚠️  No Renogy devices found to test")
            return {}
        
        for address, device_info in renogy_devices.items():
            _LOGGER.info(f"   🧪 Testing {device_info.name} ({address})...")
            
            try:
                start_time = time.time()
                
                # BleakClient can take an address string or a BLEDevice object.
                # Using address string directly is simpler here.
                async with BleakClient(address, timeout=10.0) as client:
                    if client.is_connected:
                        connection_time = time.time() - start_time
                        device_info.connectable = True
                        device_info.connection_time = connection_time
                        
                        # Get services and characteristics
                        services = await client.get_services()
                        device_info.services = [str(service.uuid) for service in services]
                        
                        # Find Renogy-specific services
                        renogy_services = []
                        characteristics = []
                        
                        for service in services:
                            service_uuid = str(service.uuid).lower()
                            if service_uuid in [s.lower() for s in RENOGY_SERVICE_UUIDS]:
                                renogy_services.append(service_uuid)
                            
                            for char in service.characteristics:
                                char_uuid = str(char.uuid).lower()
                                characteristics.append(char_uuid)
                                
                        device_info.renogy_services = renogy_services
                        device_info.characteristics = characteristics
                        
                        if renogy_services:
                            _LOGGER.info(f"   ✅ {device_info.name}: Connected with Renogy services!")
                            device_info.recommendation_score += 25
                        else:
                            _LOGGER.info(f"   ⚠️  {device_info.name}: Connected but no Renogy services")
                            
                    else:
                        _LOGGER.warning(f"   ❌ {device_info.name}: Connection failed")
                        
            except Exception as e:
                _LOGGER.error(f"   ❌ {device_info.name}: Error - {str(e)}")
                device_info.error = str(e)
                
        return renogy_devices
    
    def analyze_bluetooth_environment(self) -> Dict[str, Any]:
        """Analyze Bluetooth environment and interference"""
        _LOGGER.info("🌐 Analyzing Bluetooth environment...")
        
        # Count devices by type
        device_types = {}
        signal_strengths = []
        
        for device_info in self.discovered_devices.values():
            # Classify device type
            if device_info.is_renogy:
                device_type = f"Renogy {device_info.device_type or 'Device'}"
            elif device_info.is_proxy:
                device_type = "Bluetooth Proxy"
            elif 'phone' in device_info.name.lower() or 'iphone' in device_info.name.lower():
                device_type = "Mobile Phone"
            elif any(x in device_info.name.lower() for x in ['watch', 'band', 'fit']):
                device_type = "Wearable"
            elif any(x in device_info.name.lower() for x in ['tv', 'speaker', 'audio']):
                device_type = "Audio/Video"
            elif 'esp32' in device_info.name.lower():
                device_type = "ESP32 Device"
            else:
                device_type = "Other"
                
            device_types[device_type] = device_types.get(device_type, 0) + 1
            signal_strengths.append(device_info.rssi)
        
        # Calculate environment metrics
        avg_signal = sum(signal_strengths) / len(signal_strengths) if signal_strengths else -999
        strong_signals = len([rssi for rssi in signal_strengths if rssi > -60])
        weak_signals = len([rssi for rssi in signal_strengths if rssi < -80])
        
        analysis = {
            'total_devices': len(self.discovered_devices),
            'device_types': device_types,
            'average_signal_strength': avg_signal,
            'strong_signals': strong_signals,
            'weak_signals': weak_signals,
            'interference_risk': 'High' if len(self.discovered_devices) > 20 else 'Low',
            'known_proxies': len(self.known_proxies),
            'detected_proxies': len(self.proxy_devices)
        }
        
        return analysis
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Find best Renogy devices
        renogy_devices = [info for info in self.discovered_devices.values() if info.is_renogy]
        
        if not renogy_devices:
            recommendations.extend([
                "❌ No Renogy devices detected!",
                "💡 Troubleshooting Steps:",
                "   • Ensure Renogy device is powered on and operational",
                "   • Check if device has Bluetooth activation (button/menu)",
                "   • Move closer to device (within 10 meters)",
                "   • Verify device model supports Bluetooth (BT-1/BT-2 module)",
                "   • Try running scan during device activity (charging/load)"
            ])
            return recommendations
        
        # Sort by recommendation score
        renogy_devices.sort(key=lambda x: x.recommendation_score, reverse=True)
        best_devices = renogy_devices[:3]  # Top 3 recommendations
        
        recommendations.append("🎯 DEVICE RECOMMENDATIONS (Ranked by Compatibility):")
        recommendations.append("")
        
        for i, device in enumerate(best_devices, 1):
            status = "✅ READY" if device.connectable else "⚠️  NEEDS TESTING"
            device_description = 'Unknown'
            if device.device_type:
                device_description = RENOGY_DEVICE_PATTERNS.get(device.device_type, {}).get('description', 'Unknown')
            
            recommendations.extend([
                f"#{i} {device.name} ({device.address})",
                f"   📱 Type: {device_description}",
                f"   📶 Signal: {device.rssi} dBm",
                f"   🏆 Score: {device.recommendation_score}/100",
                f"   🔌 Status: {status}",
                ""
            ])
            
            if device.compatibility_notes:
                recommendations.append("   📋 Notes:")
                for note in device.compatibility_notes:
                    recommendations.append(f"      • {note}")
                recommendations.append("")
        
        # Proxy recommendations
        if self.proxy_devices:
            recommendations.extend([
                "🌐 BLUETOOTH PROXY ANALYSIS:",
                f"   Detected Proxies: {len(self.proxy_devices)}",
                f"   Known Proxies: {len(self.known_proxies)}",
                ""
            ])
            
            for proxy in self.known_proxies:
                recommendations.append(f"   📡 {proxy.name} ({proxy.ip_address})")
                recommendations.append(f"      {proxy.description}")
                if proxy.signal_improvement:
                    recommendations.append(f"      Signal boost: {proxy.signal_improvement}")
                recommendations.append("")
        
        # Home Assistant configuration
        connectable_devices = [d for d in renogy_devices if d.connectable]
        if connectable_devices:
            best_device = connectable_devices[0]
            recommendations.extend([
                "🏠 HOME ASSISTANT CONFIGURATION:",
                f"   Recommended Device: {best_device.name}",
                f"   MAC Address: {best_device.address}",
                "",
                "   Setup Steps:",
                "   1. Go to Settings → Devices & Services",
                "   2. Click '+ ADD INTEGRATION'",
                "   3. Search for 'BluPow'",
                f"   4. Enter MAC address: {best_device.address}",
                ""
            ])
        
        return recommendations
    
    async def run_comprehensive_test(self) -> TestResults:
        """Run complete comprehensive test suite"""
        _LOGGER.info("🚀 Starting BluPow Comprehensive Device Discovery & Testing")
        _LOGGER.info("="*80)
        
        start_time = time.time()
        
        # Phase 1: Discovery
        await self.comprehensive_scan(duration=20.0)
        
        # Phase 2: Connectivity Testing
        await self.test_connectivity()
        
        # Phase 3: Environment Analysis
        environment_analysis = self.analyze_bluetooth_environment()
        
        # Phase 4: Generate Recommendations
        recommendations = self.generate_recommendations()
        
        # Compile results
        total_time = time.time() - start_time
        renogy_count = len([d for d in self.discovered_devices.values() if d.is_renogy])
        connectable_count = len([d for d in self.discovered_devices.values() if d.connectable])
        
        # Get top recommended devices
        renogy_devices = [info for info in self.discovered_devices.values() if info.is_renogy]
        renogy_devices.sort(key=lambda x: x.recommendation_score, reverse=True)
        recommended_devices = renogy_devices[:5]  # Top 5
        
        self.test_results = TestResults(
            timestamp=datetime.now(),
            scan_duration=total_time,
            total_devices=len(self.discovered_devices),
            renogy_devices=renogy_count,
            proxy_devices=len(self.proxy_devices),
            connectable_devices=connectable_count,
            recommended_devices=recommended_devices,
            environment_analysis=environment_analysis,
            recommendations=recommendations
        )
        
        return self.test_results
    
    def display_results(self):
        """Display comprehensive test results"""
        if not self.test_results:
            _LOGGER.error("No test results available. Run comprehensive test first.")
            return
        
        results = self.test_results
        
        print("\n" + "="*80)
        print("📊 BLUPOW COMPREHENSIVE TEST RESULTS")
        print("="*80)
        print(f"⏱️  Test Duration: {results.scan_duration:.1f} seconds")
        print(f"🗓️  Timestamp: {results.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        print("📈 DISCOVERY SUMMARY:")
        print(f"   Total Devices Found: {results.total_devices}")
        print(f"   Renogy Devices: {results.renogy_devices}")
        print(f"   Bluetooth Proxies: {results.proxy_devices}")
        print(f"   Connectable Devices: {results.connectable_devices}")
        print("")
        
        print("🌐 ENVIRONMENT ANALYSIS:")
        env = results.environment_analysis
        print(f"   Interference Risk: {env['interference_risk']}")
        print(f"   Average Signal: {env['average_signal_strength']:.1f} dBm")
        print(f"   Strong Signals (>-60dBm): {env['strong_signals']}")
        print(f"   Weak Signals (<-80dBm): {env['weak_signals']}")
        print("")
        
        print("📱 DEVICE BREAKDOWN:")
        for device_type, count in env['device_types'].items():
            print(f"   {device_type}: {count}")
        print("")
        
        print("\n".join(results.recommendations))
        
        # Save detailed results
        self.save_results()
    
    def save_results(self, filename: str = "blupow_discovery_results.json"):
        """Save detailed results to file"""
        if not self.test_results:
            return
        
        # Convert to serializable format
        results_dict = asdict(self.test_results)
        
        # Convert datetime to string
        results_dict['timestamp'] = self.test_results.timestamp.isoformat()
        
        # Add detailed device information
        results_dict['detailed_devices'] = {}
        for address, device_info in self.discovered_devices.items():
            results_dict['detailed_devices'][address] = asdict(device_info)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results_dict, f, indent=2, default=str)
            _LOGGER.info(f"📄 Detailed results saved to {filename}")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to save results: {e}")

async def main():
    """Main function to run comprehensive discovery system"""
    discovery_system = BluPowDeviceDiscoverySystem()
    
    try:
        # Run comprehensive test
        results = await discovery_system.run_comprehensive_test()
        
        # Display results
        discovery_system.display_results()
        
        print("\n" + "="*80)
        print("🎉 BluPow Device Discovery Complete!")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        _LOGGER.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 