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
    UnitOfFrequency,
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
DEFAULT_CONNECT_TIMEOUT: Final = 20.0

# --- Renogy Modbus Register Definitions ---
# Based on reverse-engineering of cyrils/renogy-bt and official documentation.

class RenogyRegisters:
    """Register addresses for Renogy devices."""
    
    # --- Device Information (Read in a separate, initial query) ---
    MODEL = 0x000A
    SOFTWARE_VERSION = 0x000C
    HARDWARE_VERSION = 0x000E
    
    # --- Real-time Data Block (Read in a single query) ---
    READ_BLOCK_START = 0x0100
    READ_BLOCK_SIZE = 34 # Number of registers to read from the start address
    
    # --- Register Offsets from READ_BLOCK_START (0x0100) ---
    # These are indices into the list of registers returned by the block read
    BATTERY_SOC = 0
    BATTERY_VOLTAGE = 1
    BATTERY_CURRENT_RAW = 2  # Combined with next register
    SOLAR_VOLTAGE = 3
    SOLAR_CURRENT = 4
    SOLAR_POWER = 5
    LOAD_VOLTAGE = 6
    LOAD_CURRENT = 7
    LOAD_POWER = 8
    CONTROLLER_TEMP = 9
    BATTERY_TEMP = 10
    
    # Daily Statistics (relative to 0x0100)
    BATTERY_MIN_VOLTAGE_TODAY = 11
    BATTERY_MAX_VOLTAGE_TODAY = 12
    CHARGER_MAX_CURRENT_TODAY = 13
    DISCHARGER_MAX_CURRENT_TODAY = 14
    CHARGER_MAX_POWER_TODAY = 15
    DISCHARGER_MAX_POWER_TODAY = 16
    CHARGING_AMP_HOURS_TODAY = 17
    DISCHARGING_AMP_HOURS_TODAY = 18
    POWER_GENERATION_TODAY = 19
    POWER_CONSUMPTION_TODAY = 20
    
    # Historical Data (relative to 0x0100)
    TOTAL_OPERATING_DAYS = 21
    TOTAL_BATTERY_OVER_DISCHARGES = 22
    TOTAL_BATTERY_FULL_CHARGES = 23
    TOTAL_CHARGING_AMP_HOURS = 24 # 2 registers
    TOTAL_POWER_GENERATED = 26 # 2 registers
    
    # Status and Settings (relative to 0x0100)
    CHARGING_STATUS = 28
    
    # Aliases for correct mapping
    DAILY_POWER_GENERATION = POWER_GENERATION_TODAY
    DAILY_POWER_CONSUMPTION = POWER_CONSUMPTION_TODAY
    POWER_GENERATION_TOTAL_L = TOTAL_POWER_GENERATED
    POWER_GENERATION_TOTAL_H = TOTAL_POWER_GENERATED + 1


# Sensor Descriptions - RENOGY INVERTER (RIV1230RCH-SPS) OPTIMIZED FOR ENERGY DASHBOARD
DEVICE_SENSORS: tuple[SensorEntityDescription, ...] = (
    # Inverter Model Information
    SensorEntityDescription(
        key="model",
        name="Inverter Model",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="device_id",
        name="Device ID",
        icon="mdi:identifier",
    ),
    
    # AC Input (Mains Power)
    SensorEntityDescription(
        key="input_voltage",
        name="AC Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="input_current",
        name="AC Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="input_frequency",
        name="AC Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    
    # AC Output (Load Power)
    SensorEntityDescription(
        key="output_voltage",
        name="AC Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="output_current",
        name="AC Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="output_frequency",
        name="AC Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    
    # Load Monitoring
    SensorEntityDescription(
        key="load_active_power",
        name="AC Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="load_apparent_power",
        name="AC Apparent Power",
        native_unit_of_measurement="VA",
        icon="mdi:flash",
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
        key="load_percentage",
        name="Load Percentage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="line_charging_current",
        name="Line Charging Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    
    # Battery Bank
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="battery_percentage",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="charging_current",
        name="Battery Charging Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="charging_status",
        name="Charging Status",
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="charging_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    
    # Solar Input (if connected)
    SensorEntityDescription(
        key="solar_voltage",
        name="Solar Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="solar_current",
        name="Solar Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="solar_power",
        name="Solar Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    
    # System Health
    SensorEntityDescription(
        key="temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
)

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

