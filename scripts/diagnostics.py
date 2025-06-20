#!/usr/bin/env python3
"""
BluPow Unified Diagnostic Tool

This script provides a comprehensive suite of diagnostic and utility functions
for the BluPow Home Assistant integration. It combines the functionality of
previous, scattered test scripts into a single, user-friendly tool.

Usage:
    python3 scripts/diagnostics.py [options]

Interactive Mode (default):
    python3 scripts/diagnostics.py

CLI Mode (for AI/automation):
    python3 scripts/diagnostics.py --test connection
    python3 scripts/diagnostics.py --test sensors --json
    python3 scripts/diagnostics.py --test scan --quiet
    python3 scripts/diagnostics.py --test structure

Options:
    --test TYPE         Run specific test (connection, sensors, scan, structure)
    --json              Output results in JSON format
    --quiet             Suppress progress messages
    --device ADDRESS    Use specific device MAC address
    --help              Show this help message
"""

import asyncio
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from blupow_client import BluPowClient
    from const import DEVICE_SENSORS
except ImportError as e:
    print(f"❌ Failed to import BluPow modules: {e}")
    print("Please ensure you are running this script from the project's root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEVICE_ADDRESS = "D8:B6:73:BF:4F:75"

class DiagnosticResult:
    """Structured result for diagnostic tests"""
    def __init__(self, test_type: str):
        self.test_type = test_type
        self.success = False
        self.timestamp = datetime.now().isoformat()
        self.data = {}
        self.errors = []
        self.warnings = []
        
    def to_dict(self):
        return {
            'test_type': self.test_type,
            'success': self.success,
            'timestamp': self.timestamp,
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings
        }

class UnifiedDiagnostics:
    """A single class for all diagnostic functions."""

    def __init__(self, address: str):
        self.address = address
        self.client = BluPowClient(self.address)

    async def run_connection_test(self, quiet: bool = False) -> DiagnosticResult:
        """Connects to the inverter, reads data, and returns structured results."""
        result = DiagnosticResult("connection")
        
        if not quiet:
            print("\n--- [1] Running Live Connection Test ---")
        
        try:
            if not quiet:
                print(f"🔄 Attempting to connect to {self.address}...")
            
            if not await self.client.connect():
                result.errors.append("Failed to connect to the inverter")
                if not quiet:
                    print("❌ ERROR: Failed to connect to the inverter.")
                    print("Please consult docs/troubleshooting/TROUBLESHOOTING.md")
                return result

            result.data['connected'] = True
            if not quiet:
                print("✅ Connection successful!")

            if not quiet:
                print("\n🔄 Reading all sensor data from the inverter...")
            
            data = await self.client.read_device_info()
            
            if not data:
                result.errors.append("Connected but failed to read data")
                if not quiet:
                    print("❌ ERROR: Connected, but failed to read data.")
                return result
                
            result.data['sensor_data'] = data
            result.data['sensor_count'] = len(data)
            result.success = True
            
            if not quiet:
                print("✅ Data received! Verifying...")
                self._print_data_summary(data)

        except Exception as e:
            result.errors.append(str(e))
            if not quiet:
                logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            if self.client.is_connected:
                await self.client.disconnect()
                if not quiet:
                    print("\n🔌 Disconnected from inverter.")
        
        return result

    def run_sensor_validation(self, quiet: bool = False) -> DiagnosticResult:
        """Validates that all defined sensors have a corresponding key in the parsers."""
        result = DiagnosticResult("sensors")
        
        if not quiet:
            print("\n--- [2] Running Sensor Definition Validation ---")
        
        try:
            # This is a conceptual test. We check which keys our parsers can produce.
            parser_methods = [
                self.client.parse_inverter_stats,
                self.client.parse_device_id,
                self.client.parse_inverter_model,
                self.client.parse_charging_info,
                self.client.parse_load_info
            ]

            # Simulate empty payloads to see what keys are generated
            produced_keys = set()
            for parser in parser_methods:
                # The exact payload doesn't matter, only the keys produced.
                # We create a dummy payload that is long enough to prevent index errors.
                dummy_payload = b'\x00' * 30 
                data = parser(dummy_payload)
                produced_keys.update(data.keys())

            defined_sensor_keys = {desc.key for desc in DEVICE_SENSORS}
            
            mapped_sensors = defined_sensor_keys.intersection(produced_keys)
            unmapped_sensors = defined_sensor_keys.difference(produced_keys)
            extra_keys = produced_keys.difference(defined_sensor_keys)

            result.data['total_sensors'] = len(defined_sensor_keys)
            result.data['mapped_sensors'] = len(mapped_sensors)
            result.data['unmapped_sensors'] = list(unmapped_sensors)
            result.data['extra_keys'] = list(extra_keys)
            
            if not quiet:
                print(f"Total Sensors Defined in const.py: {len(defined_sensor_keys)}")
                print(f"Sensors Mapped to a Parser: {len(mapped_sensors)}")
            
            if unmapped_sensors:
                result.warnings.extend(unmapped_sensors)
                if not quiet:
                    print("\n⚠️ Unmapped Sensors (defined in const.py but no parser provides the key):")
                    for key in sorted(unmapped_sensors):
                        print(f"  - {key}")
            
            if extra_keys:
                result.warnings.extend(extra_keys)
                if not quiet:
                    print("\n⚠️ Extra Keys (produced by a parser but not defined as a sensor):")
                    for key in sorted(extra_keys):
                        print(f"  - {key}")

            if not unmapped_sensors and not extra_keys:
                result.success = True
                if not quiet:
                    print("\n✅ Success! All defined sensors have a corresponding parser key.")
            else:
                result.success = False
                
        except Exception as e:
            result.errors.append(str(e))
            if not quiet:
                logger.error(f"Sensor validation failed: {e}", exc_info=True)
        
        return result
        
    async def run_ble_scan(self, quiet: bool = False) -> DiagnosticResult:
        """Performs a BLE scan to find the device and check its signal strength."""
        result = DiagnosticResult("scan")
        
        if not quiet:
            print("\n--- [3] Running BLE Device Scan ---")
        
        try:
            from bleak import BleakScanner
        except ImportError:
            result.errors.append("Bleak not installed. Cannot perform scan.")
            if not quiet:
                print("❌ Bleak not installed. Cannot perform scan.")
            return result

        try:
            if not quiet:
                print(f"📡 Scanning for BLE devices for 10 seconds...")
            
            devices = await BleakScanner.discover(timeout=10.0)
            
            target_found = False
            for device in devices:
                if device.address.upper() == self.address.upper():
                    target_found = True
                    result.data['device_found'] = True
                    result.data['device_name'] = device.name
                    result.data['device_address'] = device.address
                    result.data['rssi'] = device.rssi
                    result.success = True
                    
                    if not quiet:
                        print(f"\n✅ Target Device Found!")
                        print(f"  Name:    {device.name}")
                        print(f"  Address: {device.address}")
                        print(f"  RSSI:    {device.rssi} dBm (signal strength)")
                    break
            
            if not target_found:
                result.data['device_found'] = False
                result.errors.append(f"Target device {self.address} not found")
                if not quiet:
                    print(f"\n❌ Target device {self.address} not found.")
                    print("   Check if it is powered on and within range.")
                    
        except Exception as e:
            result.errors.append(str(e))
            if not quiet:
                logger.error(f"BLE scan failed: {e}", exc_info=True)
        
        return result

    def run_project_structure_check(self, quiet: bool = False) -> DiagnosticResult:
        """Checks for the presence of key files and directories."""
        result = DiagnosticResult("structure")
        
        if not quiet:
            print("\n--- [4] Running Project Structure Check ---")
        
        paths_to_check = {
            "Core": ["blupow_client.py", "coordinator.py", "sensor.py", "const.py", "manifest.json"],
            "Docs": ["docs/PROJECT_HISTORY.md", "docs/guides/VERIFICATION_GUIDE.md"],
            "Scripts": ["scripts/diagnostics.py", "scripts/verify_connection.py"]
        }
        
        try:
            all_found = True
            missing_files = []
            
            for category, paths in paths_to_check.items():
                if not quiet:
                    print(f"\nChecking {category}...")
                
                for path_str in paths:
                    path = Path(path_str)
                    if path.exists():
                        if not quiet:
                            print(f"  ✅ Found: {path_str}")
                    else:
                        if not quiet:
                            print(f"  ❌ Missing: {path_str}")
                        missing_files.append(path_str)
                        all_found = False
            
            result.data['missing_files'] = missing_files
            result.success = all_found
            
            if all_found:
                if not quiet:
                    print("\n✅ Project structure appears to be correct.")
            else:
                result.errors.extend(missing_files)
                if not quiet:
                    print("\n⚠️ Some project files are missing. This may indicate an incomplete checkout.")
                    
        except Exception as e:
            result.errors.append(str(e))
            if not quiet:
                logger.error(f"Structure check failed: {e}", exc_info=True)
        
        return result

    def _print_data_summary(self, data: dict):
        """Prints a formatted summary of the inverter data."""
        print("\n📊 INVERTER DATA SUMMARY:")
        print("-" * 30)
        
        key_data = {
            'Model': data.get('model', 'N/A'),
            'Device ID': data.get('device_id', 'N/A'),
            'Input Voltage': f"{data.get('input_voltage', 'N/A')}V",
            'Output Voltage': f"{data.get('output_voltage', 'N/A')}V",
            'Input Frequency': f"{data.get('input_frequency', 'N/A')}Hz",
            'Output Frequency': f"{data.get('output_frequency', 'N/A')}Hz",
            'Battery Voltage': f"{data.get('battery_voltage', 'N/A')}V",
            'Battery SOC': f"{data.get('battery_percentage', 'N/A')}%",
            'Load Power': f"{data.get('load_active_power', 'N/A')}W",
            'Temperature': f"{data.get('temperature', 'N/A')}°C",
            'Solar Voltage': f"{data.get('solar_voltage', 'N/A')}V",
            'Solar Current': f"{data.get('solar_current', 'N/A')}A"
        }
        
        for key, value in key_data.items():
            print(f"{key+':':<18} {value}")
        
        print("-" * 30)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BluPow Unified Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/diagnostics.py                          # Interactive menu
    python3 scripts/diagnostics.py --test connection        # Run connection test
    python3 scripts/diagnostics.py --test sensors --json    # JSON sensor validation
    python3 scripts/diagnostics.py --test scan --quiet      # Quiet BLE scan
        """
    )
    
    parser.add_argument('--test', choices=['connection', 'sensors', 'scan', 'structure'],
                        help='Run specific test type')
    parser.add_argument('--json', action='store_true',
                        help='Output results in JSON format')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress messages')
    parser.add_argument('--device', default=DEVICE_ADDRESS,
                        help=f'Device MAC address (default: {DEVICE_ADDRESS})')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    return parser.parse_args()

async def run_interactive_menu(diagnostics: UnifiedDiagnostics):
    """Run the interactive menu for human users"""
    while True:
        print("\nBluPow - Unified Diagnostic Tool")
        print("=" * 35)
        print("1. Live Connection Test")
        print("2. Sensor Definition Validation")
        print("3. BLE Device Scan")
        print("4. Project Structure Check")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            await diagnostics.run_connection_test()
        elif choice == '2':
            diagnostics.run_sensor_validation()
        elif choice == '3':
            await diagnostics.run_ble_scan()
        elif choice == '4':
            diagnostics.run_project_structure_check()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

async def main():
    """Main entry point with CLI and interactive support"""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    diagnostics = UnifiedDiagnostics(args.device)
    
    # CLI mode - run specific test
    if args.test:
        if args.test == 'connection':
            result = await diagnostics.run_connection_test(quiet=args.quiet)
        elif args.test == 'sensors':
            result = diagnostics.run_sensor_validation(quiet=args.quiet)
        elif args.test == 'scan':
            result = await diagnostics.run_ble_scan(quiet=args.quiet)
        elif args.test == 'structure':
            result = diagnostics.run_project_structure_check(quiet=args.quiet)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        elif args.quiet and not result.success:
            print(f"FAILED: {', '.join(result.errors)}")
        
        return 0 if result.success else 1
    
    # Interactive mode
    else:
        await run_interactive_menu(diagnostics)
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nDiagnostic tool cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 