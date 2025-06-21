#!/usr/bin/env python3
"""
BluPow Bluetooth Diagnostics Tool

This script helps diagnose Bluetooth connectivity issues with the BluPow integration.
Run this script to check your system's Bluetooth configuration and discover devices.
"""

import asyncio
import logging
import sys
import platform
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

try:
    from bleak import BleakClient, BleakScanner
    from bleak.exc import BleakDeviceNotFoundError, BleakError
    from bleak.backends.device import BLEDevice
except ImportError:
    print("Error: bleak library not found. Please install it with:")
    print("  sudo apt install python3-bleak")
    print("  or")
    print("  pip install bleak")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Constants (copied from const.py to make this standalone)
RENOGY_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
RENOGY_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
MODEL_NUMBER_CHAR_UUID = "00002A24-0000-1000-8000-00805F9B34FB"

class EnvironmentInfo:
    """Detect and store information about the current environment"""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_version = sys.version_info
        self.is_docker = self._detect_docker()
        self.is_hassio = self._detect_hassio()
        self.ble_backend = self._detect_ble_backend()
        
    def _detect_docker(self) -> bool:
        """Detect if running in Docker container"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read() or 'containerd' in f.read()
        except (FileNotFoundError, PermissionError):
            import os
            return any(var in os.environ for var in ['DOCKER_CONTAINER', 'HOSTNAME']) and \
                   os.path.exists('/.dockerenv')
    
    def _detect_hassio(self) -> bool:
        """Detect if running in Home Assistant OS/Supervised"""
        import os
        return os.path.exists('/usr/share/hassio') or \
               os.path.exists('/etc/hassio.json') or \
               'HASSIO' in os.environ
    
    def _detect_ble_backend(self) -> str:
        """Detect which BLE backend is being used"""
        if self.platform == "Linux":
            return "BlueZ"
        elif self.platform == "Windows":
            return "WinRT"
        elif self.platform == "Darwin":
            return "CoreBluetooth"
        else:
            return "Unknown"
    
    def __str__(self) -> str:
        return (f"Platform: {self.platform}, Python: {self.python_version[:2]}, "
                f"Docker: {self.is_docker}, HassIO: {self.is_hassio}, "
                f"BLE: {self.ble_backend}")

async def scan_devices(timeout: float = 10.0) -> List[Tuple[str, str]]:
    """Scan for BluPow devices with enhanced diagnostics."""
    try:
        _LOGGER.info("Scanning for BluPow devices (timeout: %.1fs)...", timeout)
        
        # Enhanced scanning with diagnostics
        devices = await BleakScanner.discover(timeout=timeout)
        found_devices = []
        
        if not devices:
            _LOGGER.warning("No Bluetooth devices found during scan")
            print("No Bluetooth devices found during scan")
            return []
        
        _LOGGER.info("Found %d Bluetooth devices during scan", len(devices))
        print(f"Found {len(devices)} Bluetooth devices during scan")
        
        for device in devices:
            name = device.name or "Unknown"
            address = device.address
            rssi = getattr(device, 'rssi', 'Unknown')
            
            _LOGGER.debug("Discovered device: %s (%s) RSSI: %s", name, address, rssi)
            
            # Look for potential BluPow devices
            if any(keyword in name.lower() for keyword in ['bt-th', 'blupow', 'renogy', 'solar', 'esp32']):
                _LOGGER.info("Potential BluPow device found: %s (%s) RSSI: %s", name, address, rssi)
                found_devices.append((address, name))
            
        return found_devices
        
    except Exception as err:
        _LOGGER.error("Device scanning failed: %s", err)
        print(f"Device scanning failed: {err}")
        return []

async def diagnose_bluetooth() -> Dict[str, Any]:
    """Comprehensive Bluetooth diagnostics for troubleshooting."""
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "scan_results": {},
        "platform_info": {},
        "recommendations": []
    }
    
    try:
        _LOGGER.info("Running BluPow Bluetooth diagnostics...")
        
        # Platform detection
        env = EnvironmentInfo()
        diagnostics["environment"] = str(env)
        diagnostics["platform_info"] = {
            "platform": env.platform,
            "python_version": str(env.python_version),
            "is_docker": env.is_docker,
            "is_hassio": env.is_hassio,
            "ble_backend": env.ble_backend
        }
        
        # Test basic scanning
        try:
            _LOGGER.info("Testing Bluetooth device discovery...")
            scan_start = datetime.now()
            devices = await BleakScanner.discover(timeout=5.0)
            scan_duration = (datetime.now() - scan_start).total_seconds()
            
            diagnostics["scan_results"] = {
                "success": True,
                "device_count": len(devices),
                "scan_duration_seconds": scan_duration,
                "devices": []
            }
            
            for device in devices:
                device_info = {
                    "name": device.name or "Unknown",
                    "address": device.address,
                    "rssi": getattr(device, 'rssi', None)
                }
                diagnostics["scan_results"]["devices"].append(device_info)
                
            _LOGGER.info("Bluetooth scan successful: %d devices found in %.1fs", len(devices), scan_duration)
            
        except Exception as scan_err:
            _LOGGER.error("Bluetooth scan failed: %s", scan_err)
            diagnostics["scan_results"] = {
                "success": False,
                "error": str(scan_err),
                "device_count": 0
            }
            diagnostics["recommendations"].append("Bluetooth scanning failed - check adapter and permissions")
        
        # Generate recommendations based on findings
        if diagnostics["scan_results"].get("device_count", 0) == 0:
            diagnostics["recommendations"].extend([
                "No Bluetooth devices detected - check if Bluetooth is enabled",
                "Verify Home Assistant has Bluetooth permissions",
                "Try restarting the Bluetooth service"
            ])
        
        if env.is_docker:
            diagnostics["recommendations"].append("Docker environment detected - ensure container has Bluetooth access")
            
        if env.is_hassio:
            diagnostics["recommendations"].append("Home Assistant OS detected - Bluetooth should work automatically")
            
        return diagnostics
        
    except Exception as err:
        _LOGGER.error("Bluetooth diagnostics failed: %s", err)
        diagnostics["error"] = str(err)
        diagnostics["recommendations"].append("Diagnostics failed - serious Bluetooth system issue")
        return diagnostics

async def test_device_connection(address: str) -> bool:
    """Test connecting to a specific device."""
    try:
        print(f"Testing connection to device {address}...")
        
        # Try to find the device
        devices = await BleakScanner.discover(timeout=5.0)
        target_device = None
        for device in devices:
            if device.address.upper() == address.upper():
                target_device = device
                break
        
        if not target_device:
            print(f"Device {address} not found in scan")
            return False
        
        print(f"Device found: {target_device.name} ({target_device.address})")
        
        # Try to connect
        try:
            async with BleakClient(target_device, timeout=10.0) as client:
                print(f"✓ Successfully connected to {address}")
                
                # Get services
                try:
                    services = client.services
                    service_list = list(services) if services else []
                    print(f"Found {len(service_list)} services")
                    for service in service_list:
                        print(f"  Service: {service.uuid}")
                        for char in service.characteristics:
                            print(f"    Characteristic: {char.uuid} (properties: {char.properties})")
                except Exception as e:
                    print(f"Could not read services: {e}")
                
                return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            if "No backend with an available connection slot" in str(e):
                print("This is the same error Home Assistant is experiencing!")
                print("Possible causes:")
                print("  1. Bluetooth adapter is busy")
                print("  2. Another application is connected to the device")
                print("  3. System Bluetooth permissions issue")
                print("  4. Bluetooth stack needs restart")
            return False
            
    except Exception as e:
        print(f"Error testing connection: {e}")
        return False

async def main():
    """Run comprehensive BluPow diagnostics."""
    print("=" * 60)
    print("BluPow Bluetooth Diagnostics Tool")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Run comprehensive diagnostics
        print("Running Bluetooth system diagnostics...")
        diagnostics = await diagnose_bluetooth()
        
        print("\n--- Platform Information ---")
        platform_info = diagnostics.get("platform_info", {})
        for key, value in platform_info.items():
            print(f"{key}: {value}")
        
        print("\n--- Bluetooth Scan Results ---")
        scan_results = diagnostics.get("scan_results", {})
        if scan_results.get("success", False):
            print(f"✓ Bluetooth scan successful")
            print(f"  - Found {scan_results.get('device_count', 0)} devices")
            print(f"  - Scan duration: {scan_results.get('scan_duration_seconds', 0):.1f} seconds")
            
            devices = scan_results.get("devices", [])
            if devices:
                print("\n--- Discovered Devices ---")
                for i, device in enumerate(devices, 1):
                    name = device.get('name', 'Unknown')
                    address = device.get('address', 'Unknown')
                    rssi = device.get('rssi', 'Unknown')
                    print(f"{i:2d}. {name} ({address}) RSSI: {rssi}")
            else:
                print("  - No devices found")
        else:
            print("✗ Bluetooth scan failed")
            print(f"  Error: {scan_results.get('error', 'Unknown error')}")
        
        print("\n--- Device Discovery ---")
        print("Searching for potential BluPow devices...")
        devices = await scan_devices(timeout=10.0)
        
        if devices:
            print(f"✓ Found {len(devices)} potential BluPow device(s):")
            for i, (address, name) in enumerate(devices, 1):
                print(f"{i}. {name} ({address})")
        else:
            print("✗ No potential BluPow devices found")
        
        # Test connection to the problematic device from logs
        target_address = "C4:D3:6A:66:7E:D4"
        print(f"\n--- Testing Connection to {target_address} ---")
        await test_device_connection(target_address)
        
        print("\n--- Recommendations ---")
        recommendations = diagnostics.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("✓ No specific issues detected")
        
        print("\n--- Troubleshooting Steps ---")
        print("If you're having connection issues:")
        print("1. Ensure your solar charger is powered on and nearby (< 10 meters)")
        print("2. Check if the device is advertising/discoverable")
        print("3. Verify no other applications are connected to the device")
        print("4. Try power cycling the solar charger")
        print("5. Restart Home Assistant's Bluetooth integration")
        print("6. Check Home Assistant logs for specific error messages")
        
        print("\n--- System Commands to Try ---")
        print("If connection slot errors persist:")
        print("1. sudo systemctl restart bluetooth")
        print("2. sudo hciconfig hci0 reset")
        print("3. Restart Home Assistant")
        print("4. Check for other Bluetooth applications: lsof | grep bluetooth")
        
    except Exception as e:
        print(f"✗ Diagnostics failed: {e}")
        print("\nThis indicates a serious Bluetooth system issue.")
        print("Please check:")
        print("1. Bluetooth adapter is properly installed and working")
        print("2. Required Python packages are installed (bleak)")
        print("3. Home Assistant has proper system permissions")
        
    print(f"\nDiagnostics completed at: {datetime.now().isoformat()}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
    except Exception as e:
        print(f"Failed to run diagnostics: {e}")
        sys.exit(1) 