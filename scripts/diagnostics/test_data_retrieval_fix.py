#!/usr/bin/env python3
"""
Test script to identify and fix the data retrieval issue in BluPow client
"""
import asyncio
import logging
import sys
import time
from pathlib import Path
import os
from bleak import BleakScanner, BleakClient

# Add the project root to the path to allow importing blupow_client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from custom_components.blupow.blupow_client import BluPowClient, RenogySmartBattery

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# --- Configuration ---
# Use an environment variable for the target device, or a placeholder
TARGET_DEVICE_ADDRESS = os.environ.get("BLUPOW_TEST_MAC")

async def test_device_data_retrieval(mac_address: str):
    """
    Connects to a specific device and attempts to retrieve its data.
    """
    _LOGGER.info(f"Attempting to connect to {mac_address}...")
    
    try:
        async with BleakClient(mac_address) as client:
            if not client.is_connected:
                _LOGGER.error(f"Failed to connect to {mac_address}")
                return

            _LOGGER.info(f"Connected to {mac_address}. Initializing BluPowClient...")
            
            # We don't know the device type, so we can't fully initialize
            # the client here. This script's purpose is to test the underlying
            # connection and get_data method. For this test, we might
            # need a more generic "get_data" or assume a type.
            
            # Let's assume it's a battery for this test, as it's a common device.
            device = RenogySmartBattery(mac_address) 
            blupow_client = BluPowClient(device)

            _LOGGER.info("Fetching data...")
            data = await blupow_client.get_data()

            if data:
                _LOGGER.info(f"✅ SUCCESS! Received data from {mac_address}:")
                for key, value in data.items():
                    print(f"  - {key}: {value}")
            else:
                _LOGGER.warning(f"⚠️  Connected to {mac_address}, but received no data.")

    except Exception as e:
        _LOGGER.exception(f"❌ An error occurred while testing {mac_address}: {e}")

async def main():
    """
    Main function to run the data retrieval test.
    """
    target_mac = os.environ.get("BLUPOW_TEST_MAC")

    if not target_mac:
        _LOGGER.error("Please set the BLUPOW_TEST_MAC environment variable.")
        print("Example: export BLUPOW_TEST_MAC='AA:BB:CC:DD:EE:FF'")
        return

    print(f"--- Running Data Retrieval Test for {target_mac} ---")
    await test_device_data_retrieval(target_mac)
    print("--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main()) 