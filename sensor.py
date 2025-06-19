"""Sensor platform for the BluPow integration."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BluPowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DEVICE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="model_number",
        name="Model Number",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        icon="mdi:battery",
        device_class="voltage",
        unit_of_measurement="V",
    ),
    SensorEntityDescription(
        key="solar_voltage",
        name="Solar Voltage",
        icon="mdi:solar-power",
        device_class="voltage",
        unit_of_measurement="V",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BluPow sensor entities."""
    try:
        coordinator: BluPowDataUpdateCoordinator = entry.runtime_data
        _LOGGER.info("Setting up BluPow sensors with coordinator: %s", coordinator)
        
        # Create sensors with comprehensive error handling
        entities = []
        for description in DEVICE_SENSORS:
            try:
                sensor = BluPowSensor(coordinator, description)
                entities.append(sensor)
                _LOGGER.debug("Created sensor: %s", description.key)
            except Exception as err:
                _LOGGER.error("Failed to create sensor %s: %s", description.key, err)
                continue
        
        if entities:
            async_add_entities(entities)
            _LOGGER.info("Successfully added %d BluPow sensors", len(entities))
        else:
            _LOGGER.error("No BluPow sensors were created successfully")
            
    except Exception as err:
        _LOGGER.error("Failed to set up BluPow sensors: %s", err)
        raise


class BluPowSensor(CoordinatorEntity[BluPowDataUpdateCoordinator], SensorEntity):
    """A sensor entity for a BluPow device that uses the coordinator."""

    def __init__(
        self,
        coordinator: BluPowDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor with comprehensive error handling."""
        try:
            super().__init__(coordinator)
            self.entity_description = description
            
            # Safe unique ID generation
            if coordinator and coordinator.ble_device:
                self._attr_unique_id = f"{coordinator.ble_device.address}_{description.key}"
                _LOGGER.debug("Generated unique ID: %s", self._attr_unique_id)
            else:
                _LOGGER.error("Coordinator or BLE device not available for sensor %s", description.key)
                raise ValueError("Coordinator or BLE device not available")
            
            # Safe device info initialization
            self._attr_device_info = self._create_device_info(coordinator)
            
            _LOGGER.info("Successfully initialized BluPow sensor: %s", description.key)
            
        except Exception as err:
            _LOGGER.error("Failed to initialize BluPow sensor %s: %s", description.key, err)
            raise

    def _create_device_info(self, coordinator: BluPowDataUpdateCoordinator) -> DeviceInfo:
        """Create device info with comprehensive error handling."""
        try:
            if not coordinator or not coordinator.ble_device:
                _LOGGER.warning("Creating device info with minimal data")
                return DeviceInfo(
                    connections={},
                    name="BluPow Device",
                    manufacturer="BluPow",
                    model="Unknown",
                )
            
            device_name = coordinator.ble_device.name or "BluPow Device"
            device_address = coordinator.ble_device.address or "unknown"
            
            _LOGGER.debug("Creating device info for %s (%s)", device_name, device_address)
            
            return DeviceInfo(
                connections={("bluetooth", device_address)},
                name=device_name,
                manufacturer="BluPow",
                model=device_name,
            )
            
        except Exception as err:
            _LOGGER.error("Failed to create device info: %s", err)
            return DeviceInfo(
                connections={},
                name="BluPow Device",
                manufacturer="BluPow",
                model="Unknown",
            )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor with comprehensive error handling."""
        try:
            # Check if coordinator exists
            if not self.coordinator:
                _LOGGER.warning("No coordinator available for sensor %s", self.entity_description.key)
                return None
            
            # Check if coordinator data exists
            if not hasattr(self.coordinator, 'data') or self.coordinator.data is None:
                _LOGGER.debug("No coordinator data available for sensor %s", self.entity_description.key)
                return None
            
            # Safe data access
            value = self.coordinator.data.get(self.entity_description.key)
            _LOGGER.debug("Sensor %s value: %s (type: %s)", 
                         self.entity_description.key, value, type(value))
            
            return value
            
        except Exception as err:
            _LOGGER.error("Error getting native value for sensor %s: %s", 
                         self.entity_description.key, err)
            return None

    @property
    def available(self) -> bool:
        """Return if the entity is available with error handling."""
        try:
            if not self.coordinator:
                _LOGGER.debug("No coordinator available for availability check")
                return False
            
            available = self.coordinator.last_update_success
            _LOGGER.debug("Sensor %s availability: %s", self.entity_description.key, available)
            return available
            
        except Exception as err:
            _LOGGER.error("Error checking availability for sensor %s: %s", 
                         self.entity_description.key, err)
            return False

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass with logging."""
        try:
            await super().async_added_to_hass()
            _LOGGER.info("BluPow sensor %s added to Home Assistant", self.entity_description.key)
        except Exception as err:
            _LOGGER.error("Error adding BluPow sensor %s to hass: %s", 
                         self.entity_description.key, err)

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal with logging."""
        try:
            await super().async_will_remove_from_hass()
            _LOGGER.info("BluPow sensor %s removed from Home Assistant", self.entity_description.key)
        except Exception as err:
            _LOGGER.error("Error removing BluPow sensor %s from hass: %s", 
                         self.entity_description.key, err)

