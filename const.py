"""Constants for the BluPow: Renogy Bluetooth integration."""
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

# Characteristic UUIDs
MODEL_NUMBER_CHAR_UUID: Final = "00002a24-0000-1000-8000-00805f9b34fb"
RENOGY_RX_CHAR_UUID: Final = "0000cd02-0000-1000-8000-00805f9b34fb"
RENOGY_TX_CHAR_UUID: Final = "0000cd01-0000-1000-8000-00805f9b34fb"

# Register Addresses
# Controller info
REG_DEVICE_MODEL = 0x000A
REG_SOFTWARE_VERSION = 0x000C
REG_HARDWARE_VERSION = 0x000E
# Battery Info
REG_BATTERY_VOLTAGE = 0x0101
REG_BATTERY_CURRENT = 0x0102
REG_BATTERY_SOC = 0x0100
REG_BATTERY_TEMP = 0x0103
# Solar Info
REG_SOLAR_VOLTAGE = 0x0107
REG_SOLAR_CURRENT = 0x0108
REG_SOLAR_POWER = 0x0109

# Sensor Descriptions
DEVICE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="model_number",
        name="Model Number",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="solar_voltage",
        name="Solar Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="solar_current",
        name="Solar Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_temp",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="solar_power",
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

