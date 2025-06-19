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

# Correct Renogy UUIDs from cyrils/renogy-bt protocol
RENOGY_SERVICE_UUID: Final = "0000ffd0-0000-1000-8000-00805f9b34fb"  # Main service
RENOGY_TX_CHAR_UUID: Final = "0000ffd1-0000-1000-8000-00805f9b34fb"  # TX (write to device)
RENOGY_RX_CHAR_UUID: Final = "0000fff1-0000-1000-8000-00805f9b34fb"  # RX (notifications)
RX_SERVICE_UUID: Final = "0000fff0-0000-1000-8000-00805f9b34fb"  # RX service
RENOGY_MANUFACTURER_ID: Final = 0x7DE0  # Renogy manufacturer ID

# Connection timeouts
DEFAULT_SCAN_TIMEOUT: Final = 10.0
DEFAULT_CONNECT_TIMEOUT: Final = 15.0

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

# Sensor Descriptions - REAL RENOGY DATA OPTIMIZED FOR ENERGY DASHBOARD
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
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="solar_voltage",
        name="Solar Voltage", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="solar_current",
        name="Solar Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="battery_soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="battery_temp",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="solar_power",
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    # Additional sensors for comprehensive energy monitoring
    SensorEntityDescription(
        key="load_power",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="load_current",
        name="Load Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="load_voltage",
        name="Load Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="daily_power_generation",
        name="Daily Power Generation",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="daily_power_consumption",
        name="Daily Power Consumption", 
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="charging_status",
        name="Charging Status",
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="controller_temp",
        name="Controller Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
)

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

