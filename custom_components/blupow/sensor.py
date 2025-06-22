"""Support for BluPow sensors through MQTT."""
from __future__ import annotations

import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfFrequency,
    CONF_ADDRESS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Correct sensor definitions that match the JSON payload from the gateway
# Format: { "JSON Key": (Name, Device Class, State Class, Unit, Icon), ... }
SENSOR_DEFS = {
    "AC Input Voltage": ("AC Input Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:flash"),
    "AC Input Current": ("AC Input Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-ac"),
    "AC Input Frequency": ("AC Input Frequency", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    "AC Output Voltage": ("AC Output Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:power-plug"),
    "AC Output Current": ("AC Output Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:power-plug"),
    "AC Output Frequency": ("AC Output Frequency", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, UnitOfFrequency.HERTZ, "mdi:sine-wave"),
    "Load Power": ("Load Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:power-plug"),
    "Load Apparent Power": ("Load Apparent Power", SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT, "VA", "mdi:power-plug"),
    "Load Percentage": ("Load Percentage", SensorDeviceClass.POWER_FACTOR, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:gauge"),
    "Battery Voltage": ("Battery Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:battery"),
    "Battery Current": ("Battery Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:current-dc"),
    "Battery State of Charge": ("Battery SOC", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:battery-high"),
    "Inverter Temperature": ("Inverter Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    "Solar Input Voltage": ("Solar Input Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, UnitOfElectricPotential.VOLT, "mdi:solar-power"),
    "Solar Input Current": ("Solar Input Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, UnitOfElectricCurrent.AMPERE, "mdi:solar-power"),
    "Solar Input Power": ("Solar Input Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:solar-power"),
    "Charging Power": ("Charging Power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT, "mdi:battery-charging"),
    "Charging Status": ("Charging Status", None, None, None, "mdi:battery-charging"),
    "Model": ("Model", None, None, None, "mdi:information-outline"),
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback):
    """Set up the BluPow sensors from a config entry."""
    
    address = entry.data[CONF_ADDRESS]
    mac_slug = address.replace(":", "").lower()
    
    # Generic device info. The 'Model' sensor will fill in the model details later.
    device_info = {
        "identifiers": {(DOMAIN, mac_slug)},
        "name": f"Inverter {mac_slug[-4:].upper()}",
        "manufacturer": "Renogy",
        "model": "Inverter",
        "via_device": (DOMAIN, "blupow_mqtt_gateway"),
    }

    # Create all defined sensors for this device.
    sensors = [
        BluPowMqttSensor(
            hass=hass,
            device_info=device_info,
            mac_slug=mac_slug,
            sensor_key=key,
            name=name,
            device_class=dev_class,
            state_class=state_class,
            unit=unit,
            icon=icon,
        )
        for key, (name, dev_class, state_class, unit, icon) in SENSOR_DEFS.items()
    ]
    
    async_add_entities(sensors)


class BluPowMqttSensor(SensorEntity):
    """Representation of a sensor that reads data from an MQTT topic."""

    def __init__(self, hass, device_info, mac_slug, sensor_key, name, device_class, state_class, unit, icon):
        self.hass = hass
        self.mac_slug = mac_slug
        self.sensor_key = sensor_key

        self._attr_name = name
        self._attr_unique_id = f"{mac_slug}_{sensor_key.lower().replace(' ', '_')}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info
        self._attr_available = False # Start as unavailable
        
        self.state_topic = f"blupow/{self.mac_slug}/state"
        self.availability_topic = f"blupow/{self.mac_slug}/status"

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events."""
        await super().async_added_to_hass()

        @callback
        def state_message_received(msg: mqtt.ReceiveMessage):
            try:
                payload = json.loads(msg.payload)
                if self.sensor_key in payload:
                    self._attr_native_value = payload[self.sensor_key]
                    self._attr_available = True
                    self.async_write_ha_state()
            except (json.JSONDecodeError, KeyError):
                _LOGGER.debug(f"Could not parse state for {self.unique_id}")

        @callback
        def availability_message_received(msg: mqtt.ReceiveMessage):
            self._attr_available = msg.payload.decode('utf-8') == "online"
            self.async_write_ha_state()

        await mqtt.async_subscribe(self.hass, self.state_topic, state_message_received, qos=0)
        await mqtt.async_subscribe(self.hass, self.availability_topic, availability_message_received, qos=0)

