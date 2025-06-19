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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BluPow sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: BluPowDataUpdateCoordinator = data["coordinator"]

    sensors_to_add = [
        BluPowSensor(coordinator, entry, description) for description in DEVICE_SENSORS
    ]
    async_add_entities(sensors_to_add)


class BluPowSensor(CoordinatorEntity[BluPowDataUpdateCoordinator], SensorEntity):
    """A sensor entity for a BluPow device that uses the coordinator."""

    def __init__(
        self,
        coordinator: BluPowDataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_ADDRESS])},
            name=entry.title,
            manufacturer="Renogy (via BluPow)",
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor from the coordinator."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success and self.coordinator.client.is_connected

