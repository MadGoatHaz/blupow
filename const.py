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

