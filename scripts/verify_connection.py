#!/usr/bin/env python3
"""
BluPow Connection Verification Script

This script performs a definitive test to confirm that the BluPow
integration can connect to the Renogy inverter and read all sensor data.

Usage:
    python3 scripts/verify_connection.py [options]

Options:
    --json              Output results in JSON format (for AI/automation)
    --quiet             Suppress progress messages, only show results
    --device ADDRESS    Use specific device MAC address (default: D8:B6:73:BF:4F:75)
    --timeout SECONDS   Connection timeout in seconds (default: 20)
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

from blupow_client import BluPowClient

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Default to WARNING to keep output clean
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_DEVICE_ADDRESS = "D8:B6:73:BF:4F:75"

class VerificationResult:
    """Structured result for verification test"""
    def __init__(self):
        self.success = False
        self.connected = False
        self.data_received = False
        self.sensor_count = 0
        self.timestamp = datetime.now().isoformat()
        self.device_address = ""
        self.error_message = ""
        self.data = {}
        
    def to_dict(self):
        return {
            'success': self.success,
            'connected': self.connected,
            'data_received': self.data_received,
            'sensor_count': self.sensor_count,
            'timestamp': self.timestamp,
            'device_address': self.device_address,
            'error_message': self.error_message,
            'data': self.data
        }

async def run_verification(device_address: str, quiet: bool = False, timeout: int = 20) -> VerificationResult:
    """Connects to the inverter, reads data, and returns structured results."""
    result = VerificationResult()
    result.device_address = device_address
    
    if not quiet:
        print("🚀 Starting BluPow Connection Verification")
        print("=" * 50)
        print(f"Target Device: Renogy RIV1230RCH-SPS Inverter")
        print(f"MAC Address:   {device_address}")
        print(f"Timestamp:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
    
    client = BluPowClient(device_address)
    
    try:
        if not quiet:
            print("🔄 Attempting to connect to the inverter...")
        
        if not await client.connect():
            result.error_message = "Failed to connect to the inverter"
            if not quiet:
                print("❌ ERROR: Failed to connect to the inverter.")
                print("Please check the following:")
                print("  1. The inverter is powered on.")
                print("  2. Your Home Assistant machine's Bluetooth is enabled and in range.")
                print("  3. No other devices (like your phone) are connected to the inverter.")
            return result

        result.connected = True
        if not quiet:
            print("✅ Connection successful!")
        
        if not quiet:
            print("\n🔄 Reading all sensor data from the inverter...")
        
        data = await client.read_device_info()
        
        if not data:
            result.error_message = "Connected but failed to read data"
            if not quiet:
                print("❌ ERROR: Connected to the inverter, but failed to read data.")
                print("This can sometimes be a temporary issue. Please try running the script again.")
            return result
            
        result.data_received = True
        result.data = data
        result.sensor_count = len(data)
        result.success = True
        
        if not quiet:
            print("✅ Successfully received data from the inverter!")
            print(f"📊 Retrieved {len(data)} data points")

            print("\n📊 INVERTER DATA SUMMARY:")
            print("-" * 30)
            
            # Display key data points
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
            print("\n🎉 VERIFICATION COMPLETE! 🎉")
            print("Your BluPow integration is ready to be added to Home Assistant.")
            print("You can now proceed with the integration setup.")
        
        return result

    except Exception as e:
        result.error_message = str(e)
        if not quiet:
            print(f"\n❌ An unexpected error occurred: {e}")
        logger.exception("Verification script failed:")
        return result
    finally:
        if client.is_connected:
            await client.disconnect()
            if not quiet:
                print("\n🔌 Disconnected from inverter.")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BluPow Connection Verification Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/verify_connection.py                    # Interactive mode
    python3 scripts/verify_connection.py --json --quiet     # JSON output for AI
    python3 scripts/verify_connection.py --device AA:BB:CC:DD:EE:FF --timeout 30
        """
    )
    
    parser.add_argument('--json', action='store_true',
                        help='Output results in JSON format (for AI/automation)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress messages, only show results')
    parser.add_argument('--device', default=DEFAULT_DEVICE_ADDRESS,
                        help=f'Device MAC address (default: {DEFAULT_DEVICE_ADDRESS})')
    parser.add_argument('--timeout', type=int, default=20,
                        help='Connection timeout in seconds (default: 20)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    return parser.parse_args()

async def main():
    """Main entry point with CLI argument support"""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    result = await run_verification(
        device_address=args.device,
        quiet=args.quiet,
        timeout=args.timeout
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif args.quiet and not result.success:
        print(f"FAILED: {result.error_message}")
    
    return 0 if result.success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 