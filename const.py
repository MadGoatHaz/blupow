"""Constants for the BluPow: Renewable Energy Management Integration."""
from __future__ import annotations

import logging
from typing import Final, Dict

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfFrequency,
    UnitOfEnergy,
)

DOMAIN: Final = "blupow"

# Connection and BLE UUIDs
MODEL_NUMBER_CHAR_UUID: Final = "00002a24-0000-1000-8000-00805f9b34fb"
MANUFACTURER_CHAR_UUID: Final = "00002a29-0000-1000-8000-00805f9b34fb"

DEVICE_SERVICE_UUID: Final = "0000ffd0-0000-1000-8000-00805f9b34fb"
DEVICE_READ_WRITE_CHAR: Final = "0000ffd1-0000-1000-8000-00805f9b34fb"
DEVICE_NOTIFY_CHAR: Final = "0000ffd2-0000-1000-8000-00805f9b34fb"

RENOGY_SERVICE_UUID: Final = "0000ffd0-0000-1000-8000-00805f9b34fb"
RENOGY_TX_CHAR_UUID: Final = "0000ffd1-0000-1000-8000-00805f9b34fb"
RENOGY_RX_CHAR_UUID: Final = "0000fff1-0000-1000-8000-00805f9b34fb"
RX_SERVICE_UUID: Final = "0000fff0-0000-1000-8000-00805f9b34fb"

# Connection timeouts
DEFAULT_SCAN_TIMEOUT: Final = 10.0
DEFAULT_CONNECT_TIMEOUT: Final = 20.0
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

# DEVICE IDENTIFICATION
DEVICE_TYPES: Dict[str, str] = {
    "D8:B6:73:BF:4F:75": "inverter",    # RIV1230RCH-SPS Inverter
    "C4:D3:6A:66:7E:D4": "controller"   # RNG-CTRL-RVR40 Controller
}

# ============================================================================
# INVERTER SENSORS - RIV1230RCH-SPS (AC Power Management System)
# ============================================================================
INVERTER_SENSORS: tuple[SensorEntityDescription, ...] = (
    # Device Information
    SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="device_id", 
        name="Device ID",
        icon="mdi:identifier",
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    
    # AC INPUT MONITORING (Grid/Line Power)
    SensorEntityDescription(
        key="ac_input_voltage",
        name="AC Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="ac_input_current",
        name="AC Input Current", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="ac_input_frequency",
        name="AC Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
    ),
    
    # AC OUTPUT MONITORING (Inverter Output)
    SensorEntityDescription(
        key="ac_output_voltage",
        name="AC Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:flash-outline",
    ),
    SensorEntityDescription(
        key="ac_output_current",
        name="AC Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="ac_output_frequency",
        name="AC Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
    ),
    
    # LOAD MONITORING (AC Loads Connected to Inverter)
    SensorEntityDescription(
        key="load_active_power",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:lightning-bolt",
    ), 
    SensorEntityDescription(
        key="load_apparent_power",
        name="Load Apparent Power", 
        native_unit_of_measurement="VA",
        icon="mdi:flash-triangle",
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
        icon="mdi:current-dc",
    ),
    SensorEntityDescription(
        key="load_percentage",
        name="Load Percentage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    
    # BATTERY MANAGEMENT (Connected to Inverter)
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:battery",
    ),
    SensorEntityDescription(
        key="battery_soc",
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:battery-80",
    ),
    SensorEntityDescription(
        key="charging_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="charging_status",
        name="Charging Status", 
        icon="mdi:battery-charging-outline",
    ),
    SensorEntityDescription(
        key="charging_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:battery-plus",
    ),
    SensorEntityDescription(
        key="line_charging_current",
        name="Line Charging Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:current-dc",
    ),
    
    # SOLAR INPUT (Solar panels connected to inverter - usually none)
    SensorEntityDescription(
        key="solar_voltage",
        name="Solar Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:solar-panel",
    ),
    SensorEntityDescription(
        key="solar_current",
        name="Solar Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:solar-panel",
    ),
    SensorEntityDescription(
        key="solar_power",
        name="Solar Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:solar-power",
    ),
    
    # SYSTEM HEALTH
    SensorEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
)

# ============================================================================
# CONTROLLER SENSORS - RNG-CTRL-RVR40 (Solar MPPT Charge Controller)
# ============================================================================
CONTROLLER_SENSORS: tuple[SensorEntityDescription, ...] = (
    # Device Information
    SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="device_id",
        name="Device ID", 
        icon="mdi:identifier",
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    
    # SOLAR PV INPUT (Solar Panels)
    SensorEntityDescription(
        key="pv_voltage",
        name="Solar Panel Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:solar-panel",
    ),
    SensorEntityDescription(
        key="pv_current",
        name="Solar Panel Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:solar-panel",
    ),
    SensorEntityDescription(
        key="pv_power",
        name="Solar Panel Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:solar-power",
    ),
    
    # BATTERY MANAGEMENT (Connected to Controller)
    SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:battery",
    ),
    SensorEntityDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="battery_soc",
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:battery-80",
    ),
    SensorEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="battery_type",
        name="Battery Type",
        icon="mdi:battery-outline",
    ),
    
    # CHARGING CONTROL
    SensorEntityDescription(
        key="charging_status",
        name="Charging Status",
        icon="mdi:battery-charging-outline",
    ),
    SensorEntityDescription(
        key="charging_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:battery-plus",
    ),
    SensorEntityDescription(
        key="max_charging_power_today",
        name="Max Charging Power Today",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:battery-plus-outline",
    ),
    
    # ENERGY STATISTICS  
    SensorEntityDescription(
        key="charging_amp_hours_today",
        name="Charging Amp Hours Today",
        native_unit_of_measurement="Ah",
        icon="mdi:battery-plus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="discharging_amp_hours_today",
        name="Discharging Amp Hours Today",
        native_unit_of_measurement="Ah",
        icon="mdi:battery-minus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="power_generation_today",
        name="Power Generation Today",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        icon="mdi:solar-power",
    ),
    SensorEntityDescription(
        key="power_consumption_today",
        name="Power Consumption Today",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        icon="mdi:flash-outline",
    ),
    SensorEntityDescription(
        key="power_generation_total",
        name="Total Power Generation",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        icon="mdi:solar-power-variant",
    ),
    
    # DC LOAD MONITORING (12V Loads)
    SensorEntityDescription(
        key="load_status",
        name="Load Status",
        icon="mdi:power-plug",
    ),
    SensorEntityDescription(
        key="load_voltage",
        name="Load Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:flash-outline",
    ),
    SensorEntityDescription(
        key="load_current",
        name="Load Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:current-dc",
    ),
    SensorEntityDescription(
        key="load_power",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:lightning-bolt-outline",
    ),
    
    # CONTROLLER HEALTH
    SensorEntityDescription(
        key="controller_temperature",
        name="Controller Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
)

# ============================================================================
# DEVICE SENSOR MAPPING FUNCTION
# ============================================================================
def get_device_sensors(mac_address: str) -> tuple[SensorEntityDescription, ...]:
    """Return appropriate sensors based on device MAC address."""
    device_type = DEVICE_TYPES.get(mac_address, "inverter")
    
    if device_type == "controller":
        return CONTROLLER_SENSORS
    else:
        return INVERTER_SENSORS

