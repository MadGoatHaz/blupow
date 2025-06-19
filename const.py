"""Constants for the BluPow: Temperature/Humidity Bluetooth integration."""
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)

DOMAIN: Final = "blupow"

# Characteristic UUIDs - Updated for actual device characteristics
MODEL_NUMBER_CHAR_UUID: Final = "00002a24-0000-1000-8000-00805f9b34fb"
MANUFACTURER_CHAR_UUID: Final = "00002a29-0000-1000-8000-00805f9b34fb"

# Device-specific UUIDs discovered from tuner168.com BT-TH device
DEVICE_SERVICE_UUID: Final = "0000ffd0-0000-1000-8000-00805f9b34fb"
DEVICE_READ_WRITE_CHAR: Final = "0000ffd1-0000-1000-8000-00805f9b34fb"
DEVICE_NOTIFY_CHAR: Final = "0000ffd2-0000-1000-8000-00805f9b34fb"
DEVICE_WRITE_CHAR: Final = "0000ffd3-0000-1000-8000-00805f9b34fb"
DEVICE_READ_CHAR: Final = "0000ffd4-0000-1000-8000-00805f9b34fb"
DEVICE_SPECIAL_CHAR: Final = "0000ffd5-0000-1000-8000-00805f9b34fb"

# Legacy Renogy UUIDs (kept for backward compatibility)
RENOGY_RX_CHAR_UUID: Final = "0000cd02-0000-1000-8000-00805f9b34fb"
RENOGY_TX_CHAR_UUID: Final = "0000cd01-0000-1000-8000-00805f9b34fb"

# Register Addresses (for devices that support Modbus)
REG_DEVICE_MODEL = 0x000A
REG_SOFTWARE_VERSION = 0x000C
REG_HARDWARE_VERSION = 0x000E
REG_BATTERY_VOLTAGE = 0x0101
REG_BATTERY_CURRENT = 0x0102
REG_BATTERY_SOC = 0x0100
REG_BATTERY_TEMP = 0x0103
REG_SOLAR_VOLTAGE = 0x0107
REG_SOLAR_CURRENT = 0x0108
REG_SOLAR_POWER = 0x0109

# Sensor Descriptions - Updated for temperature/humidity device with mock energy sensors
DEVICE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="model_number",
        name="Model Number",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Mock energy sensors for testing energy dashboard (these will show calculated/demo values)
    SensorEntityDescription(
        key="solar_power",
        name="Solar Power (Demo)",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage (Demo)",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-outline",
    ),
    SensorEntityDescription(
        key="battery_current",
        name="Battery Current (Demo)",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    SensorEntityDescription(
        key="energy_consumption",
        name="Energy Consumption (Demo)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:lightning-bolt",
    ),
)

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

