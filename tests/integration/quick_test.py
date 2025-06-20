#!/usr/bin/env python3
"""
Quick BluPow Connection Test
Simple diagnostic for immediate troubleshooting
"""

import asyncio
import logging
from bleak import BleakScanner, BleakClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_MAC = "D8:B6:73:BF:4F:75"
TARGET_NAME = "BTRIC134000035"

async def quick_scan():
    """Quick scan to find the device"""
    logger.info(f"🔍 Scanning for {TARGET_NAME}...")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    target_device = None
    for device in devices:
        if device.address.upper() == TARGET_MAC.upper():
            target_device = device
            logger.info(f"✅ Found {device.name or 'Unknown'} at {device.address}")
            logger.info(f"📶 Signal strength: {getattr(device, 'rssi', 'Unknown')} dBm")
            break
    
    if not target_device:
        logger.error(f"❌ Device {TARGET_NAME} not found")
        logger.info("💡 Try moving closer to the device or check if it's powered on")
        return None
    
    return target_device

async def quick_connect():
    """Quick connection test"""
    logger.info(f"🔗 Attempting connection to {TARGET_MAC}...")
    
    try:
        async with BleakClient(TARGET_MAC, timeout=15.0) as client:
            if client.is_connected:
                logger.info("🎉 Connection successful!")
                
                # Try to get basic info
                try:
                    services = await client.get_services()
                    service_count = len(services.services) if hasattr(services, 'services') else len(list(services))
                    logger.info(f"📋 Found {service_count} services")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Connected but couldn't read services: {e}")
                    return True
            else:
                logger.error("❌ Connection failed - client not connected")
                return False
                
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        
        # Provide specific guidance based on error
        error_str = str(e).lower()
        if "fail_establish" in error_str:
            logger.info("💡 Device may be busy, in sleep mode, or connected elsewhere")
            logger.info("💡 Try: Power cycle device, wait a few minutes, try again")
        elif "timeout" in error_str:
            logger.info("💡 Connection timeout - device may be too far or interference")
            logger.info("💡 Try: Move closer, check for WiFi interference")
        elif "not found" in error_str:
            logger.info("💡 Device disappeared during connection")
            logger.info("💡 Try: Ensure device stays powered and advertising")
        
        return False

async def main():
    """Main test routine"""
    logger.info("🚀 BluPow Quick Connection Test")
    logger.info("=" * 50)
    
    # Step 1: Scan for device
    device = await quick_scan()
    if not device:
        return
    
    logger.info("")
    
    # Step 2: Test connection
    success = await quick_connect()
    
    logger.info("")
    logger.info("=" * 50)
    
    if success:
        logger.info("✅ SUCCESS: Device is connectable!")
        logger.info("💡 If Home Assistant still shows connection issues:")
        logger.info("   - Restart Home Assistant")
        logger.info("   - Reload Bluetooth integration")
        logger.info("   - Check for competing connections")
    else:
        logger.info("❌ FAILED: Connection issues detected")
        logger.info("💡 Next steps:")
        logger.info("   1. Check if device is connected to another system")
        logger.info("   2. Power cycle the Renogy device")
        logger.info("   3. Move Home Assistant server closer")
        logger.info("   4. Check ESPHome proxy logs")
        logger.info("   5. Run full diagnostics: python3 connection_test.py")

if __name__ == "__main__":
    asyncio.run(main()) 