"""Sensor platform for the BluPow integration."""
import logging

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
    coordinator: BluPowDataUpdateCoordinator = entry.runtime_data
    
    # Create sensors with minimal initialization
    entities = []
    for description in DEVICE_SENSORS:
        entities.append(BluPowSensor(coordinator, description))
    
    async_add_entities(entities)


class BluPowSensor(CoordinatorEntity[BluPowDataUpdateCoordinator], SensorEntity):
    """A sensor entity for a BluPow device that uses the coordinator."""

    def __init__(
        self,
        coordinator: BluPowDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.ble_device.address}_{description.key}"
        
        # Minimal device info - no model number dependency
        self._attr_device_info = DeviceInfo(
            connections={("bluetooth", coordinator.ble_device.address)},
            name=coordinator.ble_device.name or "BluPow Device",
            manufacturer="BluPow",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Safe access to coordinator data
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success

