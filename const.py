"""Constants for the BluPow: Renogy Bluetooth integration."""
from homeassistant.const import Platform

DOMAIN = "blupow"
PLATFORMS: list[Platform] = [Platform.SENSOR]

# --- Discovered GATT Service and Characteristic UUIDs ---

# The characteristic for reading the device's model number
MODEL_NUMBER_CHAR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"

# The primary service for Renogy communication
RENOGY_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"

# The characteristic to WRITE commands to (Transmit)
RENOGY_TX_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"

# The characteristic to listen for NOTIFY data on (Receive)
RENOGY_RX_CHAR_UUID = "0000ffd2-0000-1000-8000-00805f9b34fb"

# Renogy BT-2 RX Service UUID
RENOGY_RX_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

# --- Modbus Register Addresses ---
# (Translated from https://github.com/floreno/renogy-rover-modbus)

REG_BATTERY_SOC = 0x0100
REG_BATTERY_VOLTAGE = 0x0101
REG_LOAD_VOLTAGE = 0x0104
REG_LOAD_CURRENT = 0x0105
REG_LOAD_POWER = 0x0106
REG_SOLAR_VOLTAGE = 0x0107
REG_SOLAR_CURRENT = 0x0108
REG_SOLAR_POWER = 0x0109
REG_BATTERY_TEMP = 0x0103 # Special handling needed for this one
REG_CONTROLLER_TEMP = 0x0103 # Special handling needed for this one

