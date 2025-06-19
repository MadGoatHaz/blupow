"""
BluPow BLE Client for Home Assistant Integration - Enhanced Renogy Protocol

Based on cyrils/renogy-bt: Direct connection without pairing, enhanced device discovery
Supports ESPHome Bluetooth Proxy for extended range
"""

import asyncio
import logging
import platform
import sys
import struct
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError
from bleak.backends.device import BLEDevice
from homeassistant.core import HomeAssistant
import homeassistant.components.bluetooth as bluetooth

from .const import (
    RENOGY_SERVICE_UUID,
    RENOGY_TX_CHAR_UUID,
    RENOGY_RX_CHAR_UUID,
    RENOGY_MANUFACTURER_ID,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
    DEVICE_SENSORS
)

_LOGGER = logging.getLogger(__name__)

class EnvironmentInfo:
    """Detect Home Assistant environment details"""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_version = sys.version_info
        self.is_docker = self._detect_docker()
        self.is_hassio = self._detect_hassio()
        self.ble_backend = self._detect_ble_backend()
        
    def _detect_docker(self) -> bool:
        """Detect if running in Docker"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except:
            return False
            
    def _detect_hassio(self) -> bool:
        """Detect if running in Home Assistant OS"""
        try:
            import os
            return os.path.exists('/usr/bin/hassio')
        except:
            return False
            
    def _detect_ble_backend(self) -> str:
        """Detect BLE backend in use"""
        if self.platform == "Linux":
            return "BlueZ"
        elif self.platform == "Windows":
            return "WinRT"
        elif self.platform == "Darwin":
            return "CoreBluetooth"
        else:
            return "Unknown"
    
    def __str__(self) -> str:
        return f"Platform: {self.platform}, Python: {self.python_version[:2]}, Docker: {self.is_docker}, HassIO: {self.is_hassio}, BLE: {self.ble_backend}"

class BluPowClient:
    """Enhanced BluPow client with proper Renogy protocol implementation"""
    
    def __init__(self, address: str, hass: HomeAssistant):
        self.address = address
        self.hass = hass
        self.name = address  # Default to address until device is found
        self.client: Optional[BleakClient] = None
        self.environment = EnvironmentInfo()
        self._connection_attempts = 0
        self._last_data = {}
        self._is_connected = False
        self._ble_device: Optional[BLEDevice] = None

        # ESPHome Bluetooth Proxy support
        # This will be checked later when device is available
        self._supports_esphome_proxy = False
        
        _LOGGER.info(f"Environment detected: {self.environment}")
        _LOGGER.info(f"BluPow client initialized for address: {self.address} - Environment: {self.environment}")
        
    def _detect_esphome_proxy(self) -> bool:
        """Detect if ESPHome Bluetooth Proxy is available for enhanced range"""
        if not self._ble_device:
            return False
        
        # Check if device is being accessed through ESPHome proxy
        # ESPHome proxies typically have specific characteristics in metadata
        try:
            # Check for ESPHome proxy indicators in device metadata
            if hasattr(self._ble_device, 'metadata'):
                metadata = str(self._ble_device.metadata).lower()
                if 'esphome' in metadata or 'proxy' in metadata:
                    _LOGGER.info(f"🌐 ESPHome Bluetooth Proxy detected for device {self.address}")
                    return True
            
            # Check if device is reachable through known proxy addresses
            # User's multi-proxy setup for extended coverage
            known_proxies = [
                ('esp32-bluetooth-proxy-2105e4', '192.168.51.151', 'Primary - Tested (+10 dB improvement)'),
                ('proxy-2', '192.168.51.207', 'Secondary - Available for testing'),
                ('proxy-3', '192.168.51.109', 'Tertiary - Available for testing'),
                ('a0:b7:65:21:05:e6', '192.168.51.151', 'Primary proxy MAC')
            ]
            
            # Log proxy detection attempt with all available proxies
            _LOGGER.debug(f"Checking for ESPHome proxy support for {self.address}")
            _LOGGER.info(f"📡 Available ESPHome Bluetooth Proxies:")
            for name, ip, description in known_proxies[:3]:  # Log first 3 (exclude MAC)
                _LOGGER.info(f"   🔹 {name} ({ip}) - {description}")
            
            # TODO: Future enhancement - actively test which proxy provides best signal
            # This would require integration with Home Assistant's Bluetooth component
            # to determine which proxy is actually being used for connections
            
            return False  # Will be True if proxy is actively being used
            
        except Exception as e:
            _LOGGER.debug(f"Error detecting ESPHome proxy: {e}")
            return False
    
    async def discover_renogy_devices(self, timeout: float = DEFAULT_SCAN_TIMEOUT) -> List[Tuple[str, str, int]]:
        """
        Enhanced device discovery for Renogy devices
        
        Returns:
            List of tuples: (address, name, rssi)
        """
        _LOGGER.info("🔍 Starting enhanced Renogy device discovery...")
        
        devices = []
        try:
            discovered = await BleakScanner.discover(timeout=timeout)
            
            for device in discovered:
                if self._is_potential_renogy_device(device):
                    rssi = getattr(device, 'rssi', -999)
                    devices.append((device.address, device.name or "Unknown", rssi))
                    _LOGGER.info(f"📱 Found potential Renogy device: {device.name} ({device.address}) RSSI: {rssi}")
                    
                    # Check for ESPHome proxy
                    if self._is_esphome_proxy(device):
                        _LOGGER.info(f"🌐 ESPHome Bluetooth Proxy detected: {device.name}")
                        
        except Exception as e:
            _LOGGER.error(f"Device discovery failed: {e}")
            
        _LOGGER.info(f"✅ Discovery completed: {len(devices)} potential Renogy devices found")
        return devices
    
    def _is_potential_renogy_device(self, device: BLEDevice) -> bool:
        """Check if device is potentially a Renogy device"""
        if not device.name:
            return False
            
        name = device.name.lower()
        
        # Renogy device name patterns
        renogy_patterns = [
            'bt-th',       # BT-TH-XXXXXXXX (common Renogy pattern)
            'btric',       # BTRIC134000035 (Renogy inverter)
            'renogy',      # Direct Renogy naming
            'rover',       # Rover series
            'wanderer',    # Wanderer series
            'rng-ctrl',    # Direct controller naming
        ]
        
        # Check manufacturer data for Renogy signature
        manufacturer_data = getattr(device, 'metadata', {}).get('manufacturer_data', {})
        if RENOGY_MANUFACTURER_ID in manufacturer_data:
            return True
            
        # Check service UUIDs
        service_uuids = getattr(device, 'metadata', {}).get('uuids', [])
        if RENOGY_SERVICE_UUID.lower() in [uuid.lower() for uuid in service_uuids]:
            return True
            
        # Check name patterns
        return any(pattern in name for pattern in renogy_patterns)
    
    def _is_esphome_proxy(self, device: BLEDevice) -> bool:
        """Check if device is an ESPHome Bluetooth Proxy"""
        if not device.name:
            return False
            
        name = device.name.lower()
        proxy_patterns = ['esphome', 'bluetooth-proxy', 'esp32-proxy']
        
        return any(pattern in name for pattern in proxy_patterns)
    
    async def check_device_availability(self) -> bool:
        """Check if device is available for connection"""
        try:
            _LOGGER.debug(f"Checking availability of device {self.address}")
            
            # Try to discover the specific device
            discovered = await BleakScanner.discover(timeout=5.0)
            
            for device in discovered:
                if device.address.upper() == self.address.upper():
                    _LOGGER.info(f"✅ Device {self.address} is available and advertising")
                    return True
                    
            _LOGGER.warning(f"⚠️ Device {self.address} not found in scan")
            return False
            
        except Exception as e:
            _LOGGER.error(f"Availability check failed: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to the Renogy device using cyrils/renogy-bt method with improved connection management"""
        if self._is_connected:
            return True

        self._ble_device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if not self._ble_device:
            _LOGGER.warning(f"Renogy device {self.address} not found, will retry.")
            return False

        self.name = self._ble_device.name or self.address
        self._supports_esphome_proxy = self._detect_esphome_proxy()

        try:
            _LOGGER.info(f"🔗 Connecting to Renogy device: {self.name} ({self.address})")
            
            # Ensure any existing connection is properly closed first
            if hasattr(self, 'client') and self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            # Use shorter timeout for connection attempts to avoid blocking
            connection_timeout = min(DEFAULT_CONNECT_TIMEOUT, 10.0)
            
            # Direct connection without pairing (cyrils method)
            self.client = BleakClient(self._ble_device, timeout=connection_timeout)
            
            # Retry connection with exponential backoff for connection slot issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.client.connect()
                    break
                except Exception as e:
                    if "connection slot" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        _LOGGER.warning(f"Connection slot unavailable, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            if self.client.is_connected:
                _LOGGER.info(f"✅ Successfully connected to {self.address}")
                
                # Discover services
                services = await self.client.get_services()
                _LOGGER.debug(f"Available services: {[str(s.uuid) for s in services]}")
                
                # Find Renogy communication characteristics
                tx_char = None
                rx_char = None
                
                for service in services:
                    for char in service.characteristics:
                        if char.uuid.lower() == RENOGY_TX_CHAR_UUID.lower():
                            tx_char = char
                            _LOGGER.debug(f"Found TX characteristic: {char.uuid}")
                        elif char.uuid.lower() == RENOGY_RX_CHAR_UUID.lower():
                            rx_char = char
                            _LOGGER.debug(f"Found RX characteristic: {char.uuid}")
                
                if tx_char and rx_char:
                    # Enable notifications for data reception
                    await self.client.start_notify(rx_char, self._notification_handler)
                    _LOGGER.info("📡 Notifications enabled for data reception")
                    
                    self._is_connected = True
                    self._connection_attempts = 0  # Reset on successful connection
                    return True
                else:
                    _LOGGER.error("❌ Required Renogy characteristics not found")
                    await self.client.disconnect()
                    return False
            else:
                _LOGGER.error(f"❌ Failed to establish connection to {self.address}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            self._connection_attempts += 1
            
            # Clean up failed connection
            if hasattr(self, 'client') and self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            return False
    
    def _notification_handler(self, sender, data: bytearray):
        """Handle notifications from Renogy device"""
        _LOGGER.debug(f"📨 Notification received: {data.hex()}")
        
        # Process Renogy Modbus response
        if len(data) >= 3 and data[0] == 0xFF and data[1] == 0x03:
            self._process_modbus_response(data)
    
    def _process_modbus_response(self, data: bytearray):
        """Process Modbus response from Renogy device"""
        try:
            if len(data) < 5:
                return
                
            # Parse Modbus response
            # Format: [0xFF, 0x03, length, data..., checksum]
            data_length = data[2]
            payload = data[3:3+data_length]
            
            _LOGGER.debug(f"Processing Modbus response: length={data_length}, payload={payload.hex()}")
            
            # Parse register values (16-bit big-endian)
            registers = []
            for i in range(0, len(payload), 2):
                if i + 1 < len(payload):
                    value = struct.unpack('>H', payload[i:i+2])[0]
                    registers.append(value)
            
            # Update last data with parsed values
            self._update_data_from_registers(registers)
            
        except Exception as e:
            _LOGGER.error(f"Error processing Modbus response: {e}")
    
    def _update_data_from_registers(self, registers: List[int]):
        """Update device data from register values"""
        try:
            # Map registers to sensor values based on Renogy specification
            # This is a simplified mapping - full implementation would need complete register map
            
            if len(registers) >= 7:
                self._last_data.update({
                    'battery_voltage': registers[0] / 10.0 if registers[0] != 0 else None,
                    'solar_voltage': registers[1] / 10.0 if registers[1] != 0 else None,
                    'battery_current': registers[2] / 100.0 if registers[2] != 0 else None,
                    'solar_current': registers[3] / 100.0 if registers[3] != 0 else None,
                    'solar_power': registers[4] if registers[4] != 0 else None,
                    'battery_soc': registers[5] if registers[5] != 0 else None,
                    'battery_temp': registers[6] - 40 if registers[6] != 0 else None,  # Celsius
                    'last_update': datetime.now().isoformat(),
                    'connection_status': 'connected',
                    'power_generation_today': registers[17],
                    'power_consumption_today': registers[18],
                    'power_generation_total': ((registers[21] << 16) + registers[20]) / 1000.0, # in kWh
                })
                
                _LOGGER.debug(f"Updated device data: {self._last_data}")
                
        except Exception as e:
            _LOGGER.error(f"Error updating data from registers: {e}")
    
    async def read_device_data(self) -> Dict[str, Any]:
        """Read data from Renogy device using Modbus protocol"""
        if not self._is_connected:
            if not await self.connect():
                return {}
        
        try:
            # Renogy Modbus read command
            # Format: [0xFF, 0x03, start_reg_high, start_reg_low, num_regs_high, num_regs_low, checksum_high, checksum_low]
            
            # Read basic device info (registers 0x0100 to 0x0106)
            start_register = 0x0100
            num_registers = 7
            
            command = bytearray([
                0xFF, 0x03,
                (start_register >> 8) & 0xFF,
                start_register & 0xFF,
                (num_registers >> 8) & 0xFF,
                num_registers & 0xFF
            ])
            
            # Calculate Modbus CRC16 checksum
            checksum = self._calculate_crc16(command)
            command.extend([(checksum >> 8) & 0xFF, checksum & 0xFF])
            
            _LOGGER.debug(f"Sending Modbus command: {command.hex()}")
            
            # Send command via TX characteristic
            if self.client:
                tx_char = None
                services = self.client.services
                if services:
                    for service in services:
                        for char in service.characteristics:
                            if char.uuid.lower() == RENOGY_TX_CHAR_UUID.lower():
                                tx_char = char
                                break
                
                if tx_char:
                    await self.client.write_gatt_char(tx_char, command)
                
                # Wait for response
                await asyncio.sleep(0.5)
                
                return self._last_data
            else:
                _LOGGER.error("TX characteristic not found")
                return {}
                
        except Exception as e:
            _LOGGER.error(f"Error reading device data: {e}")
            return {}
    
    def _calculate_crc16(self, data: bytearray) -> int:
        """Calculate Modbus CRC16 checksum"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    async def get_data(self) -> Dict[str, Any]:
        """Get current device data with improved error handling and fallback"""
        try:
            # Try to read fresh data
            fresh_data = await self.read_device_data()
            
            if fresh_data:
                # Enhance with additional computed values
                enhanced_data = fresh_data.copy()
                
                # Calculate power if not available
                if enhanced_data.get('solar_voltage') and enhanced_data.get('solar_current'):
                    if not enhanced_data.get('solar_power'):
                        enhanced_data['solar_power'] = round(
                            enhanced_data['solar_voltage'] * enhanced_data['solar_current'], 2
                        )
                
                # Add model information
                enhanced_data['model_number'] = 'RNG-CTRL-RVR40'  # Known from user confirmation
                enhanced_data['device_type'] = 'solar_charge_controller'
                enhanced_data['manufacturer'] = 'Renogy'
                enhanced_data['protocol_version'] = 'cyrils-renogy-bt'
                
                # Add energy dashboard compatible fields
                enhanced_data.update({
                    'load_power': enhanced_data.get('load_power', 0),
                    'daily_energy_generated': enhanced_data.get('daily_energy_generated', 0),
                    'total_energy_generated': enhanced_data.get('total_energy_generated', 0),
                    'max_power_today': enhanced_data.get('max_power_today', 0),
                    'charging_status': enhanced_data.get('charging_status', 'unknown'),
                    'error_count': self._connection_attempts,
                    'device_available': True,
                    'supports_esphome_proxy': self._supports_esphome_proxy,
                    'environment': str(self.environment)
                })
                
                # Add RSSI if available
                if hasattr(self._ble_device, 'rssi'):
                    enhanced_data['rssi'] = self._ble_device.rssi
                
                return enhanced_data
            else:
                # Return informative offline data
                return self._get_offline_data()
                
        except Exception as e:
            _LOGGER.error(f"Error getting data: {e}")
            return self._get_offline_data()
    
    def _get_offline_data(self) -> Dict[str, Any]:
        """Return offline/error state data with helpful status information"""
        # Determine connection status based on error type
        connection_status = "error"
        charging_status = "offline"
        
        if self._connection_attempts > 0:
            if self._connection_attempts < 3:
                connection_status = "connecting"
                charging_status = "connecting"
            else:
                connection_status = "failed"
                charging_status = "offline"
        
        return {
            'model_number': 'RNG-CTRL-RVR40',
            'battery_voltage': None,
            'solar_voltage': None,
            'battery_current': None,
            'solar_current': None,
            'battery_soc': None,
            'battery_temp': None,
            'solar_power': None,
            'load_power': None,
            'daily_energy_generated': None,
            'total_energy_generated': None,
            'max_power_today': None,
            'charging_status': charging_status,
            'connection_status': connection_status,
            'last_update': 'offline',
            'error_count': self._connection_attempts,
            'device_available': False,
            'supports_esphome_proxy': self._supports_esphome_proxy,
            'environment': str(self.environment)
        }
    
    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self._is_connected = False
        _LOGGER.info(f"Disconnected from {self.address}")
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'client') and self.client:
            try:
                asyncio.create_task(self.disconnect())
            except:
                pass 