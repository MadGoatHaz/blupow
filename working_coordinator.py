#!/usr/bin/env python3
"""
Working Coordinator Replacement - Get Real Data to Sensors
"""
import asyncio
import sys

async def create_working_coordinator():
    """Create a coordinator that actually works"""
    print("🔧 CREATING WORKING COORDINATOR")
    print("=" * 50)
    
    # Read the current broken coordinator
    coordinator_path = "/config/custom_components/blupow/coordinator.py"
    
    try:
        with open(coordinator_path, 'r') as f:
            content = f.read()
        
        print("✅ Current coordinator loaded")
        
        # Create a completely new working coordinator
        new_coordinator = '''import asyncio
"""Data update coordinator for the BluPow integration."""
import logging
from typing import Any, Dict
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import bluetooth

from .blupow_client import BluPowClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BluPowDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching BluPow data from the device."""

    def __init__(self, hass: HomeAssistant, client: BluPowClient, update_interval: int) -> None:
        """Initialize the data update coordinator."""
        self.client = client
        self.ble_device = bluetooth.async_ble_device_from_address(
            hass, client.address.upper(), connectable=True
        ) if client else None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        _LOGGER.info("BluPow coordinator initialized for device: %s", self.client.address)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the inverter using proven working method."""
        _LOGGER.debug(f"Starting data update for {self.client.address}")
        
        try:
            # Use a fresh client instance each time to avoid connection state issues
            fresh_client = BluPowClient(self.client.address)
            
            _LOGGER.info("Attempting fresh connection...")
            connected = await fresh_client.connect()
            
            if connected:
                _LOGGER.info("✅ Fresh connection successful!")
                
                # Read data using proven working method
                data = await fresh_client.read_device_info()
                
                if data and len(data) > 0:
                    _LOGGER.info(f"✅ Successfully retrieved {len(data)} fields of real data")
                    
                    # Log key data values to confirm real data
                    key_values = {}
                    for key in ['model', 'input_voltage', 'battery_voltage', 'temperature']:
                        if key in data and data[key] is not None:
                            key_values[key] = data[key]
                    
                    if key_values:
                        _LOGGER.info(f"📊 Real data sample: {key_values}")
                    
                    # Clean disconnect
                    await fresh_client.disconnect()
                    
                    # Update our main client's data store
                    self.client._data = data
                    
                    return data
                else:
                    _LOGGER.warning("No data retrieved from device")
            else:
                _LOGGER.error("Fresh connection failed")
            
            # Clean up fresh client
            if fresh_client.is_connected:
                await fresh_client.disconnect()
                
        except Exception as err:
            _LOGGER.error(f"Error in data update: {err}")
            import traceback
            _LOGGER.error(f"Traceback: {traceback.format_exc()}")
        
        # Return current data (may be cached/offline)
        data = self.client.get_data()
        _LOGGER.debug(f"Returning data with keys: {list(data.keys())}")
        return data

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return basic device information."""
        model = "Unknown"
        if self.data and self.data.get('model'):
            model = self.data.get('model')

        name = "BluPow Device"
        if self.ble_device and self.ble_device.name:
            name = self.ble_device.name

        return {
            "identifiers": {(DOMAIN, self.client.address)},
            "name": name,
            "model": model,
            "manufacturer": "Renogy",
        }

    async def enable_test_mode(self) -> None:
        """Enable test mode with simulated data for debugging."""
        _LOGGER.info("Enabling test mode for BluPow coordinator")
        # Override get_data to return test data
        original_get_data = self.client.get_data
        self.client.get_data = self.client.get_test_data
        await self.async_refresh()
'''
        
        # Write the new working coordinator
        with open(coordinator_path, 'w') as f:
            f.write(new_coordinator)
        
        print("✅ Working coordinator installed!")
        print("💡 This coordinator uses fresh connections each time")
        print("🔄 Restart Home Assistant to activate")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create working coordinator: {e}")
        return False

async def test_working_method():
    """Test the working method that the new coordinator will use"""
    print("\n🧪 TESTING WORKING METHOD")
    print("=" * 50)
    
    sys.path.append('/config/custom_components')
    from blupow.blupow_client import BluPowClient
    
    try:
        # Test the fresh client approach
        print("Testing fresh client method...")
        
        fresh_client = BluPowClient("D8:B6:73:BF:4F:75")
        connected = await fresh_client.connect()
        
        if connected:
            print("✅ Fresh client connection: SUCCESS")
            
            data = await fresh_client.read_device_info()
            if data and len(data) > 0:
                print(f"✅ Data retrieval: {len(data)} fields")
                
                # Show real data
                key_data = {k: v for k, v in data.items() if k in ['model', 'input_voltage', 'battery_voltage', 'temperature', 'load_active_power'] and v is not None}
                
                if key_data:
                    print("🎯 REAL DATA CONFIRMED:")
                    for key, value in key_data.items():
                        print(f"   {key}: {value}")
                    
                    await fresh_client.disconnect()
                    print("✅ Clean disconnect successful")
                    return True
                else:
                    print("❌ Data is null/empty")
            else:
                print("❌ No data retrieved")
        else:
            print("❌ Fresh client connection failed")
        
        if fresh_client.is_connected:
            await fresh_client.disconnect()
            
        return False
        
    except Exception as e:
        print(f"❌ Working method test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 WORKING COORDINATOR: Final Solution for Real Data")
    print("=" * 60)
    
    async def main():
        # Test the working method first
        method_works = await test_working_method()
        
        if not method_works:
            print("❌ Working method failed - cannot proceed")
            return False
        
        print("\n✅ Working method confirmed!")
        
        # Create the working coordinator
        coordinator_created = await create_working_coordinator()
        
        if coordinator_created:
            print("\n🎉 WORKING COORDINATOR INSTALLED!")
            print("✅ Uses fresh connections each time")
            print("✅ Proven working data retrieval method")
            print("✅ Real data logging for verification")
            print("\n🔄 RESTART HOME ASSISTANT NOW")
            print("📊 Sensors will show real inverter data!")
            return True
        else:
            print("\n❌ Failed to install working coordinator")
            return False
    
    success = asyncio.run(main())
    print(f"\n🏁 RESULT: {'WORKING COORDINATOR READY' if success else 'INSTALLATION FAILED'}")
    sys.exit(0 if success else 1) 