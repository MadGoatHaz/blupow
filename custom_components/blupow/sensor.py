"""Sensor platform for the BluPow integration."""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import get_device_sensors, DOMAIN, DEVICE_TYPES
from .coordinator import BluPowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BluPow sensor entities from a config entry."""
    coordinator: BluPowDataUpdateCoordinator = entry.runtime_data
    
    # Get appropriate sensors for this device
    sensors = get_device_sensors(coordinator.mac_address)
    
    # Create sensor entities
    entities = [
        BluPowSensor(coordinator, description)
        for description in sensors
    ]
    
    async_add_entities(entities)
    
    device_type = DEVICE_TYPES.get(coordinator.mac_address, "unknown")
    _LOGGER.info(f"✅ Added {len(entities)} BluPow {device_type} sensors for {coordinator.mac_address}")


class BluPowSensor(CoordinatorEntity[BluPowDataUpdateCoordinator], SensorEntity):
    """A sensor entity for a BluPow device."""

    def __init__(
        self,
        coordinator: BluPowDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        
        # Get device type for entity naming
        device_type = DEVICE_TYPES.get(coordinator.mac_address, "unknown")
        
        # Create clean MAC ID (remove colons and convert to lowercase)
        clean_mac = coordinator.mac_address.replace(':', '').lower()
        
        # Create unique_id: {clean_mac}_{sensor_key}
        self._attr_unique_id = f"{clean_mac}_{description.key}"
        
        # Create entity_id: sensor.blupow_{device_type}_{sensor_key}
        self._attr_entity_id = f"sensor.blupow_{device_type}_{description.key}"
        
        # Set device info
        self._attr_device_info = coordinator.device_info
        
        _LOGGER.debug(f"Created sensor: {self._attr_entity_id} (unique_id: {self._attr_unique_id})")

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        # Get raw value from coordinator data
        raw_value = self.coordinator.data.get(self.entity_description.key)
        
        # Handle None values
        if raw_value is None:
            return None
        
        # Handle string values that represent null/empty states
        if isinstance(raw_value, str):
            if raw_value.lower() in ['none', 'null', 'unknown', 'unavailable', '', 'n/a']:
                return None
            
            # Try to convert numeric strings to numbers for numeric sensors
            if self._is_numeric_sensor():
                try:
                    return float(raw_value)
                except (ValueError, TypeError):
                    return raw_value
        
        # For numeric values, perform basic validation
        if isinstance(raw_value, (int, float)):
            if self._is_percentage_sensor() and not (0 <= raw_value <= 100):
                return None
            if self._is_voltage_sensor() and (raw_value < 0 or raw_value > 1000):
                return None
            if self._is_current_sensor() and (raw_value < -1000 or raw_value > 1000):
                return None
        
        return raw_value

    def _is_numeric_sensor(self) -> bool:
        """Check if this sensor should have numeric values."""
        return (
            hasattr(self.entity_description, 'device_class') and 
            self.entity_description.device_class in ['voltage', 'current', 'power', 'temperature', 'frequency', 'battery', 'energy']
        ) or (
            hasattr(self.entity_description, 'native_unit_of_measurement') and
            self.entity_description.native_unit_of_measurement in ['V', 'A', 'W', '°C', '°F', 'Hz', '%', 'VA', 'Ah', 'Wh']
        )

    def _is_percentage_sensor(self) -> bool:
        """Check if this sensor represents a percentage."""
        return (
            self.entity_description.key.endswith('_percentage') or 
            self.entity_description.key.endswith('_soc') or
            self.entity_description.key == 'load_percentage'
        )

    def _is_voltage_sensor(self) -> bool:
        """Check if this sensor represents voltage."""
        return 'voltage' in self.entity_description.key

    def _is_current_sensor(self) -> bool:
        """Check if this sensor represents current."""
        return 'current' in self.entity_description.key

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        # Simple availability logic:
        # Available if we have data and the coordinator's last update was successful
        return (
            self.coordinator.data is not None and 
            self.coordinator.last_update_success
        )

    @property
    def extra_state_attributes(self) -> Optional[dict]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return None
            
        attributes = {}
        
        # Add connection status
        connection_status = self.coordinator.data.get('connection_status')
        if connection_status:
            attributes['connection_status'] = connection_status
            
        # Add last update time
        last_update = self.coordinator.data.get('last_update')
        if last_update:
            attributes['last_update'] = last_update
            
        # Add device type
        device_type = self.coordinator.data.get('device_type')
        if device_type:
            attributes['device_type'] = device_type
            
        return attributes if attributes else None

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        _LOGGER.info(f"✅ BluPow sensor added: {self.entity_id}")

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        await super().async_will_remove_from_hass()
        _LOGGER.info(f"🗑️ BluPow sensor removed: {self.entity_id}")

