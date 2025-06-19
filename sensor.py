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
    async_add_entities(
        BluPowSensor(coordinator, description) for description in DEVICE_SENSORS
    )


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
        
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.ble_device.address}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            connections={("bluetooth", coordinator.ble_device.address)},
            name=coordinator.ble_device.name,
            manufacturer="Renogy",
            model=self.coordinator.data.get("model_number"),
        )

    @property
    def native_value(self) -> str | float | None:
        """Return the state of the sensor from the coordinator."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self.entity_description.key)
            if value is None:
                return None
            # For numeric sensors, ensure we return a number
            if self.entity_description.key in ["battery_voltage", "solar_voltage"]:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            return value
        return None

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None

