from .base import BaseDevice
from renogy_bt import RenogyInverter

class RenogyInverterDevice(BaseDevice):
    def __init__(self, mac):
        self.mac = mac
        self.device = RenogyInverter(mac, name="Renogy Inverter")
        self.device_id = None

    async def connect(self, client):
        await self.device.connect(client=client)

    async def disconnect(self):
        await self.device.disconnect()

    async def get_data(self):
        """Get data from the Renogy Inverter."""
        raw_data = await self.device.get_inverter_info()
        
        # Apply scaling factors
        scaled_data = {
            "battery_voltage": raw_data.get("battery_voltage", 0) / 10.0,
            "battery_power": raw_data.get("battery_power", 0), # Already in Watts
            "battery_current": raw_data.get("battery_current", 0) / 10.0,
            "battery_soc": raw_data.get("battery_soc", 0),
            "inverter_output_voltage": raw_data.get("inverter_output_voltage", 0) / 10.0,
            "inverter_output_current": raw_data.get("inverter_output_current", 0) / 10.0,
            "inverter_output_power": raw_data.get("inverter_output_power", 0), # Already in Watts
            "inverter_temperature": raw_data.get("inverter_temperature", 0),
        }
        return scaled_data 