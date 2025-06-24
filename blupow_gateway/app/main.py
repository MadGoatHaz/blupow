import asyncio
import logging

from app.device_manager import DeviceManager
from app.mqtt_handler import MqttHandler

# --- Constants ---
GATEWAY_VERSION = "1.0.0"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


async def main(device_manager: DeviceManager, mqtt_handler: MqttHandler):
    """Main application entry point."""
    _LOGGER.info(f"Starting BluPow Gateway v{GATEWAY_VERSION}")
    
    # Load devices from config
    device_manager.load_devices_from_config()

    # Connect to MQTT and start the client loop
    try:
        mqtt_handler.connect()
    except Exception:
        # If MQTT connection fails, we can't do anything.
        # Error is already logged by MqttHandler.
        return

    # Start polling for all configured devices
    for device in device_manager.devices.values():
        # Discovery will be published by the MqttHandler's on_connect callback
        await device_manager.start_polling_device(device)

    _LOGGER.info("Gateway is online and waiting for commands.")


async def shutdown(device_manager: DeviceManager, mqtt_handler: MqttHandler):
    """Gracefully stop all services."""
    _LOGGER.info("Shutting down gateway...")
    
    # The order is important: shut down devices first, then MQTT.
    await device_manager.shutdown()
    mqtt_handler.disconnect()
    
    _LOGGER.info("Gateway shutdown complete.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    device_manager = None
    mqtt_handler = None
    
    try:
        device_manager = DeviceManager(loop)
        mqtt_handler = MqttHandler(loop, device_manager)
        
        loop.run_until_complete(main(device_manager, mqtt_handler))
        loop.run_forever()  # Keep the event loop running until stop() is called

    except KeyboardInterrupt:
        _LOGGER.info("Shutdown requested by user.")
    except Exception:
        _LOGGER.exception("An unexpected error occurred in the main execution loop.")
    finally:
        _LOGGER.info("Starting final shutdown sequence.")
        if loop.is_running() and device_manager and mqtt_handler:
            loop.run_until_complete(shutdown(device_manager, mqtt_handler))
        
        # Close the loop
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        
        # Gather all tasks to let them finish cancelling
        async def gather_tasks():
            await asyncio.gather(*tasks, return_exceptions=True)

        # Run the task gathering until it's complete
        loop.run_until_complete(gather_tasks())
        loop.close()
        _LOGGER.info("Event loop closed.") 