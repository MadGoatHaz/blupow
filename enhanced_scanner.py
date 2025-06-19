#!/usr/bin/env python3
"""
Enhanced Renogy Device Scanner
Based on cyrils/renogy-bt protocol - Enhanced device discovery with ESPHome support
"""

import asyncio
import logging
from typing import List, Tuple, Dict, Any
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRenogyScanner:
    """Enhanced scanner for Renogy devices with comprehensive discovery"""
    
    def __init__(self):
        self.renogy_patterns = [
            'bt-th',       # BT-TH-XXXXXXXX (common Renogy pattern)
            'btric',       # BTRIC134000035 (Renogy inverter) 
            'renogy',      # Direct Renogy naming
            'rover',       # Rover series
            'wanderer',    # Wanderer series
            'rng-ctrl',    # Direct controller naming
        ]
        
        self.esphome_patterns = [
            'esphome',
            'bluetooth-proxy',
            'esp32-proxy',
            'ble-proxy'
        ]
        
        # Renogy UUIDs from cyrils/renogy-bt
        self.renogy_service_uuid = "0000ffd0-0000-1000-8000-00805f9b34fb"
        self.renogy_manufacturer_id = 0x7DE0
    
    async def comprehensive_scan(self, timeout: float = 15.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Comprehensive scan for all devices with detailed categorization
        """
        logger.info("🔍 Starting comprehensive Bluetooth device discovery...")
        logger.info(f"⏱️ Scan timeout: {timeout} seconds")
        
        results = {
            'renogy_devices': [],
            'esphome_proxies': [],
            'other_devices': [],
            'scan_summary': {}
        }
        
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            logger.info(f"📡 Scan completed: {len(devices)} devices discovered")
            
            for device in devices:
                device_info = self._analyze_device(device)
                
                if device_info['is_renogy']:
                    results['renogy_devices'].append(device_info)
                    logger.info(f"🎯 RENOGY DEVICE: {device_info['name']} ({device_info['address']}) RSSI: {device_info['rssi']}")
                    
                    # Special attention to our target device
                    if device_info['address'].upper() == 'C4:D3:6A:66:7E:D4':
                        logger.info("🚨 *** TARGET DEVICE FOUND: C4:D3:6A:66:7E:D4 ***")
                        
                elif device_info['is_esphome']:
                    results['esphome_proxies'].append(device_info)
                    logger.info(f"🌐 ESPHome Proxy: {device_info['name']} ({device_info['address']}) RSSI: {device_info['rssi']}")
                    
                else:
                    results['other_devices'].append(device_info)
                    logger.debug(f"📱 Other device: {device_info['name']} ({device_info['address']})")
            
            # Generate summary
            results['scan_summary'] = {
                'total_devices': len(devices),
                'renogy_devices': len(results['renogy_devices']),
                'esphome_proxies': len(results['esphome_proxies']),
                'other_devices': len(results['other_devices']),
                'target_device_found': any(d['address'].upper() == 'C4:D3:6A:66:7E:D4' for d in results['renogy_devices'])
            }
            
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}")
            
        return results
    
    def _analyze_device(self, device: BLEDevice) -> Dict[str, Any]:
        """Analyze device to categorize and extract information"""
        name = device.name or "Unknown"
        address = device.address
        rssi = getattr(device, 'rssi', -999)
        
        # Get metadata
        metadata = getattr(device, 'metadata', {})
        manufacturer_data = metadata.get('manufacturer_data', {})
        service_uuids = metadata.get('uuids', [])
        
        device_info = {
            'name': name,
            'address': address,
            'rssi': rssi,
            'metadata': metadata,
            'manufacturer_data': manufacturer_data,
            'service_uuids': service_uuids,
            'is_renogy': False,
            'is_esphome': False,
            'confidence_score': 0
        }
        
        # Check if it's a Renogy device
        device_info['is_renogy'] = self._is_renogy_device(device_info)
        
        # Check if it's an ESPHome proxy
        device_info['is_esphome'] = self._is_esphome_proxy(device_info)
        
        return device_info
    
    def _is_renogy_device(self, device_info: Dict[str, Any]) -> bool:
        """Determine if device is a Renogy device"""
        name = device_info['name'].lower()
        confidence = 0
        
        # Check name patterns
        for pattern in self.renogy_patterns:
            if pattern in name:
                confidence += 30
                logger.debug(f"Name pattern match '{pattern}': +30 confidence")
        
        # Check manufacturer data
        if self.renogy_manufacturer_id in device_info['manufacturer_data']:
            confidence += 50
            logger.debug(f"Renogy manufacturer ID found: +50 confidence")
        
        # Check service UUIDs
        for uuid in device_info['service_uuids']:
            if uuid.lower() == self.renogy_service_uuid.lower():
                confidence += 40
                logger.debug(f"Renogy service UUID found: +40 confidence")
        
        # Special case for our known devices
        if device_info['address'].upper() in ['C4:D3:6A:66:7E:D4', 'D8:B6:73:BF:4F:75']:
            confidence += 60
            logger.debug(f"Known device address: +60 confidence")
        
        device_info['confidence_score'] = confidence
        return confidence >= 30  # Threshold for Renogy device
    
    def _is_esphome_proxy(self, device_info: Dict[str, Any]) -> bool:
        """Determine if device is an ESPHome Bluetooth proxy"""
        name = device_info['name'].lower()
        
        for pattern in self.esphome_patterns:
            if pattern in name:
                return True
        
        return False
    
    def print_detailed_report(self, results: Dict[str, List[Dict[str, Any]]]):
        """Print a detailed scan report"""
        print("\n" + "="*80)
        print("🔍 ENHANCED RENOGY DEVICE DISCOVERY REPORT")
        print("="*80)
        
        summary = results['scan_summary']
        print(f"\n📊 SCAN SUMMARY:")
        print(f"   Total devices discovered: {summary['total_devices']}")
        print(f"   Renogy devices found: {summary['renogy_devices']}")
        print(f"   ESPHome proxies found: {summary['esphome_proxies']}")
        print(f"   Other devices: {summary['other_devices']}")
        print(f"   Target device (C4:D3:6A:66:7E:D4) found: {'✅ YES' if summary['target_device_found'] else '❌ NO'}")
        
        if results['renogy_devices']:
            print(f"\n🎯 RENOGY DEVICES ({len(results['renogy_devices'])}):")
            for i, device in enumerate(results['renogy_devices'], 1):
                print(f"   {i}. {device['name']} ({device['address']})")
                print(f"      RSSI: {device['rssi']} dBm")
                print(f"      Confidence: {device['confidence_score']}%")
                if device['address'].upper() == 'C4:D3:6A:66:7E:D4':
                    print("      🚨 *** THIS IS OUR TARGET CHARGE CONTROLLER! ***")
                elif device['address'].upper() == 'D8:B6:73:BF:4F:75':
                    print("      ⚡ *** THIS IS OUR WORKING INVERTER/CHARGER! ***")
                print()
        
        if results['esphome_proxies']:
            print(f"🌐 ESPHome BLUETOOTH PROXIES ({len(results['esphome_proxies'])}):")
            for i, device in enumerate(results['esphome_proxies'], 1):
                print(f"   {i}. {device['name']} ({device['address']}) RSSI: {device['rssi']} dBm")
                print("      💡 Can extend Bluetooth range for Home Assistant")
        
        print(f"\n🔧 NEXT STEPS:")
        if summary['target_device_found']:
            print("   ✅ Target Renogy device is discoverable!")
            print("   🚀 Ready to configure BluPow integration in Home Assistant")
            print("   📊 Device can be added to Energy Dashboard")
        else:
            print("   ⚠️  Target device C4:D3:6A:66:7E:D4 not found")
            print("   🔋 Check if charge controller is powered on")
            print("   📍 Ensure device is within 10 meters")
            print("   🔄 Try power cycling the charge controller")
        
        if results['esphome_proxies']:
            print(f"   🌐 {len(results['esphome_proxies'])} ESPHome proxies available for range extension")
        
        print("\n" + "="*80)

async def main():
    """Main scanning function"""
    scanner = EnhancedRenogyScanner()
    
    print("🔍 Enhanced Renogy Device Scanner")
    print("📡 Based on cyrils/renogy-bt protocol")
    print("🌐 Includes ESPHome Bluetooth Proxy detection")
    print("\nScanning...")
    
    # Perform comprehensive scan
    results = await scanner.comprehensive_scan(timeout=15.0)
    
    # Print detailed report
    scanner.print_detailed_report(results)
    
    # Check if we found our target device
    target_found = any(
        device['address'].upper() == 'C4:D3:6A:66:7E:D4' 
        for device in results['renogy_devices']
    )
    
    if target_found:
        print("\n🎉 SUCCESS: Target Renogy device is ready for Home Assistant integration!")
        return True
    else:
        print("\n⚠️  Target device not found. Check troubleshooting steps above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Scan interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        exit(1) 