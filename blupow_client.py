"""
BluPow BLE Client for Home Assistant Integration - Enhanced Renogy Protocol

Based on cyrils/renogy-bt: Direct connection without pairing, enhanced device discovery
Enhanced with comprehensive error handling, logging, and self-monitoring
"""

import asyncio
import logging
import platform
import sys
import struct
import time
import traceback
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError
from bleak.backends.device import BLEDevice
if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

try:
    from .const import (
        RENOGY_SERVICE_UUID,
        RENOGY_TX_CHAR_UUID,
        RENOGY_RX_CHAR_UUID,
        RENOGY_MANUFACTURER_ID,
        DEFAULT_SCAN_TIMEOUT,
        DEFAULT_CONNECT_TIMEOUT,
    )
except ImportError:
    # Fallback for standalone testing
    RENOGY_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
    RENOGY_TX_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
    RENOGY_RX_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
    RENOGY_MANUFACTURER_ID = 0x7DE0
    DEFAULT_SCAN_TIMEOUT = 10.0
    DEFAULT_CONNECT_TIMEOUT = 20.0

_LOGGER = logging.getLogger(__name__)

class ConnectionHealth:
    """Track connection health and performance metrics"""
    
    def __init__(self):
        self.total_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.consecutive_failures = 0
        self.last_success_time = None
        self.last_failure_time = None
        self.average_connection_time = 0.0
        self.connection_times = []
        self.error_history = []
        self.data_retrieval_success = 0
        self.data_retrieval_failures = 0
        
    def record_connection_attempt(self, success: bool, duration: float = 0.0, error: str = None):
        """Record connection attempt results"""
        self.total_attempts += 1
        
        if success:
            self.successful_connections += 1
            self.consecutive_failures = 0
            self.last_success_time = time.time()
            if duration > 0:
                self.connection_times.append(duration)
                # Keep only last 50 connection times
                if len(self.connection_times) > 50:
                    self.connection_times.pop(0)
                self.average_connection_time = sum(self.connection_times) / len(self.connection_times)
        else:
            self.failed_connections += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            if error:
                self.error_history.append({
                    'timestamp': time.time(),
                    'error': error,
                    'consecutive_failures': self.consecutive_failures
                })
                # Keep only last 20 errors
                if len(self.error_history) > 20:
                    self.error_history.pop(0)
    
    def record_data_retrieval(self, success: bool):
        """Record data retrieval success/failure"""
        if success:
            self.data_retrieval_success += 1
        else:
            self.data_retrieval_failures += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_connections / self.total_attempts) * 100
    
    @property
    def data_success_rate(self) -> float:
        """Calculate data retrieval success rate"""
        total_data_attempts = self.data_retrieval_success + self.data_retrieval_failures
        if total_data_attempts == 0:
            return 0.0
        return (self.data_retrieval_success / total_data_attempts) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Determine if connection is considered healthy"""
        if self.total_attempts < 3:
            return True  # Not enough data yet
        
        # Healthy if success rate > 50% and consecutive failures < 5
        return self.success_rate > 50.0 and self.consecutive_failures < 5
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        return {
            'total_attempts': self.total_attempts,
            'success_rate': round(self.success_rate, 1),
            'consecutive_failures': self.consecutive_failures,
            'average_connection_time': round(self.average_connection_time, 2),
            'data_success_rate': round(self.data_success_rate, 1),
            'is_healthy': self.is_healthy,
            'last_success_age': time.time() - self.last_success_time if self.last_success_time else None,
            'recent_errors': self.error_history[-3:] if self.error_history else []
        }

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
    """Enhanced BluPow client with comprehensive error handling and monitoring"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self._client: Optional[BleakClient] = None
        self._device_name = None
        self._last_data = {}
        self._connected = False
        self._logger = logging.getLogger(__name__)
        
        # Enhanced monitoring and health tracking
        self.health = ConnectionHealth()
        self.environment = EnvironmentInfo()
        self._last_health_log = 0
        self._health_log_interval = 300  # Log health every 5 minutes
        
        # BLE Service and Characteristic UUIDs (from Renogy BT-2 protocol)
        self._service_uuid = "0000ffd0-0000-1000-8000-00805f9b34fb"
        self._tx_char_uuid = "0000ffd1-0000-1000-8000-00805f9b34fb"  # Write to device
        self._rx_char_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"  # Notifications from device
        
        # Response handling with enhanced error tracking
        self._response_data = bytearray()
        self._response_received = False
        self._response_timeout = 3.0
        self._operation_start_time = None
        
        # Renogy protocol constants
        self._device_id = 255  # Broadcast address for standalone devices
        
        # INVERTER-SPECIFIC: Register sections for RIV1230RCH-SPS
        self.sections = [
            {'register': 4000, 'words': 10, 'parser': self.parse_inverter_stats},
            {'register': 4109, 'words': 1, 'parser': self.parse_device_id},
            {'register': 4311, 'words': 8, 'parser': self.parse_inverter_model},
            {'register': 4327, 'words': 7, 'parser': self.parse_charging_info},
            {'register': 4408, 'words': 6, 'parser': self.parse_load_info}
        ]
        
        # Charging status mapping (inverter-specific)
        self._charging_status_map = {
            0: 'deactivated',
            1: 'constant current',
            2: 'constant voltage',
            4: 'floating',
            6: 'battery activation',
            7: 'battery disconnecting'
        }
        
        # Enhanced logging
        self._log_connection_health_if_needed()

    def _log_connection_health_if_needed(self):
        """Log connection health periodically"""
        current_time = time.time()
        if current_time - self._last_health_log >= self._health_log_interval:
            health_report = self.health.get_health_report()
            
            if self.health.total_attempts > 0:
                status = "🟢 HEALTHY" if self.health.is_healthy else "🔴 UNHEALTHY"
                self._logger.info(
                    f"📊 BluPow Health Report [{status}]: "
                    f"Success Rate: {health_report['success_rate']}%, "
                    f"Consecutive Failures: {health_report['consecutive_failures']}, "
                    f"Avg Connection Time: {health_report['average_connection_time']}s, "
                    f"Data Success: {health_report['data_success_rate']}%"
                )
                
                # Log recent errors if any
                if health_report['recent_errors']:
                    for error in health_report['recent_errors']:
                        self._logger.warning(f"Recent Error: {error['error']}")
            
            self._last_health_log = current_time

    def _safe_operation(self, operation_name: str):
        """Decorator-like context manager for safe operations with comprehensive error handling"""
        return SafeOperationContext(self, operation_name)

class SafeOperationContext:
    """Context manager for safe operations with error handling and logging"""
    
    def __init__(self, client: BluPowClient, operation_name: str):
        self.client = client
        self.operation_name = operation_name
        self.start_time = None
        self.success = False
        
    def __enter__(self):
        self.start_time = time.time()
        self.client._logger.debug(f"🔄 Starting {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.success = True
            self.client._logger.debug(f"✅ {self.operation_name} completed successfully in {duration:.2f}s")
        else:
            self.success = False
            error_msg = f"{exc_type.__name__}: {exc_val}"
            self.client._logger.error(f"❌ {self.operation_name} failed after {duration:.2f}s: {error_msg}")
            
            # Record error for health tracking
            if hasattr(self.client, 'health'):
                if 'connection' in self.operation_name.lower():
                    self.client.health.record_connection_attempt(False, duration, error_msg)
                elif 'data' in self.operation_name.lower():
                    self.client.health.record_data_retrieval(False)
        
        # Log health periodically
        self.client._log_connection_health_if_needed()
        
        return False  # Don't suppress exceptions

    def _calculate_crc(self, data: bytes) -> int:
        """Calculate Modbus CRC16 for command validation"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _create_read_command(self, start_register: int, num_registers: int) -> bytes:
        """Create Renogy-compatible read command"""
        # Renogy command format: [0xFF, 0x03, start_reg_high, start_reg_low, count_high, count_low, crc_high, crc_low]
        command = bytearray([
            0xFF,  # Device ID (broadcast)
            0x03,  # Function code (read holding registers)
            (start_register >> 8) & 0xFF,  # Start register high byte
            start_register & 0xFF,          # Start register low byte
            (num_registers >> 8) & 0xFF,    # Number of registers high byte
            num_registers & 0xFF             # Number of registers low byte
        ])
        
        # Calculate CRC16 and append (Renogy uses little-endian CRC)
        crc = self._calculate_crc(bytes(command))
        command.append(crc & 0xFF)         # CRC low byte first
        command.append((crc >> 8) & 0xFF)  # CRC high byte second
        
        return bytes(command)

    async def _notification_handler(self, sender, data: bytearray):
        """Handle notifications from the device"""
        self._logger.info(f"📨 Notification received: {data.hex()}")
        
        # Extend response buffer
        self._response_data.extend(data)
        
        # Check if we have a complete Renogy response
        if len(self._response_data) >= 3:
            if self._response_data[0] == 0xFF and self._response_data[1] == 0x03:
                expected_length = self._response_data[2] + 5  # Data length + header + CRC
                if len(self._response_data) >= expected_length:
                    self._logger.info(f"✅ Complete Renogy response received: {self._response_data[:expected_length].hex()}")
                    self._response_received = True
                    
                    # Send ACK (based on cyrils/renogy-bt research)
                    await self._send_ack(self._response_data[0])

    async def _send_ack(self, first_byte: int):
        """Send ACK message after receiving data (based on Renogy protocol)"""
        try:
            if self._client and self._client.is_connected:
                ack_message = f"main recv data[{first_byte:02x}] [".encode()
                await self._client.write_gatt_char(self._tx_char_uuid, ack_message)
                self._logger.debug(f"📤 ACK sent: {ack_message}")
        except Exception as e:
            self._logger.warning(f"Failed to send ACK: {e}")

    def _parse_renogy_response(self, data: bytes) -> Dict[str, Any]:
        """Parse Renogy response data into sensor values"""
        if len(data) < 5 or data[0] != 0xFF or data[1] != 0x03:
            self._logger.error(f"Invalid Renogy response format: {data.hex()}")
            return {}
            
        data_length = data[2]
        if len(data) < data_length + 5:
            self._logger.error(f"Incomplete response: expected {data_length + 5}, got {len(data)}")
            return {}
            
        # Extract payload (skip header, get data, skip CRC)
        payload = data[3:3+data_length]
        self._logger.info(f"Response payload: {payload.hex()}")
        
        # Parse registers based on Renogy protocol
        parsed_data = {}
        
        try:
            if len(payload) >= 14:  # Device info response (7 registers)
                # Parse device info registers (0x0100-0x0106)
                parsed_data['battery_soc'] = struct.unpack('>H', payload[0:2])[0]  # Battery SOC %
                parsed_data['battery_voltage'] = struct.unpack('>H', payload[2:4])[0] / 10.0  # Battery voltage
                parsed_data['battery_current'] = struct.unpack('>H', payload[4:6])[0] / 100.0  # Battery current
                parsed_data['controller_temp'] = struct.unpack('>H', payload[6:8])[0]  # Controller temp
                parsed_data['battery_temp'] = struct.unpack('>H', payload[8:10])[0]  # Battery temp
                parsed_data['solar_voltage'] = struct.unpack('>H', payload[10:12])[0] / 10.0  # Solar voltage
                parsed_data['solar_current'] = struct.unpack('>H', payload[12:14])[0] / 100.0  # Solar current
                
                # Calculate derived values
                parsed_data['solar_power'] = parsed_data['solar_voltage'] * parsed_data['solar_current']
                parsed_data['model_number'] = "RNG-CTRL-ROVER"  # Default model
                parsed_data['connection_status'] = 'connected'
                parsed_data['last_update'] = datetime.now().isoformat()
                
            self._logger.info(f"Parsed data: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            self._logger.error(f"Error parsing Renogy response: {e}")
            return {}

    # INVERTER-SPECIFIC PARSING METHODS
    def parse_inverter_stats(self, payload: bytes) -> Dict[str, Any]:
        """Parse inverter statistics (register 4000, 10 words)"""
        data = {}
        if len(payload) >= 23:  # 3 header + 20 data + 2 CRC
            # Data starts at byte 3 (after device_id, function_code, data_length)
            data_start = 3
            data['input_voltage'] = struct.unpack('>H', payload[data_start:data_start+2])[0] / 10.0
            data['input_current'] = struct.unpack('>H', payload[data_start+2:data_start+4])[0] / 100.0
            data['output_voltage'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0] / 10.0
            data['output_current'] = struct.unpack('>H', payload[data_start+6:data_start+8])[0] / 100.0
            data['output_frequency'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0] / 100.0
            data['battery_voltage'] = struct.unpack('>H', payload[data_start+10:data_start+12])[0] / 10.0
            data['temperature'] = struct.unpack('>H', payload[data_start+12:data_start+14])[0] / 10.0
            data['input_frequency'] = struct.unpack('>H', payload[data_start+16:data_start+18])[0] / 100.0
        return data

    def parse_device_id(self, payload: bytes) -> Dict[str, Any]:
        """Parse device ID (register 4109, 1 word)"""
        data = {}
        if len(payload) >= 7:  # 3 header + 2 data + 2 CRC
            data_start = 3
            data['device_id'] = struct.unpack('>H', payload[data_start:data_start+2])[0]
        return data

    def parse_inverter_model(self, payload: bytes) -> Dict[str, Any]:
        """Parse inverter model (register 4311, 8 words)"""
        data = {}
        if len(payload) >= 21:  # 3 header + 16 data + 2 CRC
            data_start = 3
            model_bytes = payload[data_start:data_start+16]
            data['model'] = model_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
        return data

    def parse_charging_info(self, payload: bytes) -> Dict[str, Any]:
        """Parse charging information (register 4327, 7 words)"""
        data = {}
        if len(payload) >= 19:  # 3 header + 14 data + 2 CRC
            data_start = 3
            data['battery_percentage'] = struct.unpack('>H', payload[data_start:data_start+2])[0]
            data['charging_current'] = struct.unpack('>h', payload[data_start+2:data_start+4])[0] / 10.0  # signed
            data['solar_voltage'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0] / 10.0
            data['solar_current'] = struct.unpack('>H', payload[data_start+6:data_start+8])[0] / 10.0
            data['solar_power'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0]
            charging_status_code = struct.unpack('>H', payload[data_start+10:data_start+12])[0]
            data['charging_status'] = self._charging_status_map.get(charging_status_code, 'unknown')
            data['charging_power'] = struct.unpack('>H', payload[data_start+12:data_start+14])[0]
        return data

    def parse_load_info(self, payload: bytes) -> Dict[str, Any]:
        """Parse load information (register 4408, 6 words)"""
        data = {}
        if len(payload) >= 17:  # 3 header + 12 data + 2 CRC
            data_start = 3
            data['load_current'] = struct.unpack('>H', payload[data_start:data_start+2])[0] / 10.0
            data['load_active_power'] = struct.unpack('>H', payload[data_start+2:data_start+4])[0]
            data['load_apparent_power'] = struct.unpack('>H', payload[data_start+4:data_start+6])[0]
            data['line_charging_current'] = struct.unpack('>H', payload[data_start+8:data_start+10])[0] / 10.0
            data['load_percentage'] = struct.unpack('>H', payload[data_start+10:data_start+12])[0]
        return data

    async def read_device_info(self) -> Dict[str, Any]:
        """Read all inverter data using multiple register sections"""
        if not self._client or not self._client.is_connected:
            self._logger.error("Device not connected")
            return {}
            
        self._logger.info("📋 Reading inverter data from all register sections...")
        combined_data = {}
        
        try:
            for section in self.sections:
                register = section['register']
                words = section['words']
                parser = section['parser']
                
                self._logger.info(f"📤 Reading register {register}, {words} words")
                
                # Clear previous response
                self._response_data.clear()
                self._response_received = False
                
                # Create command for this register section
                command = self._create_read_command(register, words)
                self._logger.debug(f"Command: {command.hex()}")
                
                # Send command
                await self._client.write_gatt_char(self._tx_char_uuid, command)
                
                # Wait for response
                timeout_start = asyncio.get_event_loop().time()
                while not self._response_received and (asyncio.get_event_loop().time() - timeout_start) < 2.0:
                    await asyncio.sleep(0.1)
                
                if self._response_received and len(self._response_data) > 0:
                    # Parse this section's data
                    section_data = parser(bytes(self._response_data))
                    combined_data.update(section_data)
                    self._logger.info(f"✅ Section {register}: {len(section_data)} fields")
                else:
                    self._logger.warning(f"❌ No response from register {register}")
                
                # Small delay between register reads
                await asyncio.sleep(0.5)
            
            # Add metadata
            combined_data['connection_status'] = 'connected'
            combined_data['last_update'] = datetime.now().isoformat()
            
            # Cache results so coordinator can access the latest values
            if combined_data:
                self._last_data.update(combined_data)

            self._logger.info(f"🎉 Total inverter data collected: {len(combined_data)} fields")
            return combined_data
            
        except Exception as e:
            self._logger.error(f"Error reading inverter data: {e}")
            return {}

    async def read_realtime_data(self) -> Dict[str, Any]:
        """Read real-time data using proper Renogy protocol"""
        if not self._client or not self._client.is_connected:
            self._logger.error("Device not connected")
            return {}
            
        try:
            # Clear previous response
            self._response_data.clear()
            self._response_received = False
            
            # Create real-time data command (read registers 0x0107-0x0110, 10 registers)
            command = self._create_read_command(0x0107, 10)
            self._logger.debug(f"📤 Sending real-time data command: {command.hex()}")
            
            # Send command
            await self._client.write_gatt_char(self._tx_char_uuid, command)
            
            # Wait for response
            timeout_start = asyncio.get_event_loop().time()
            while not self._response_received and (asyncio.get_event_loop().time() - timeout_start) < self._response_timeout:
                await asyncio.sleep(0.1)
                
            if not self._response_received:
                self._logger.warning("⏰ Timeout waiting for real-time data response")
                return {}
                
            # Parse response and cache it
            parsed = self._parse_renogy_response(bytes(self._response_data))
            if parsed:
                self._last_data.update(parsed)
            return parsed
            
        except Exception as e:
            self._logger.error(f"Error reading real-time data: {e}")
            return {}

    async def connect(self) -> bool:
        """Connect to the Renogy device"""
        try:
            self._logger.info(f"🔗 Connecting to Renogy device: {self._device_name} ({self.mac_address})")
            
            self._client = BleakClient(self.mac_address)
            await self._client.connect()
            
            if not self._client.is_connected:
                self._logger.error("Failed to establish connection")
                return False
                
            self._logger.info("Connection status: True")
            self._logger.info("Connection successful. Starting notification handler.")
            
            # Start notifications on RX characteristic
            self._logger.info(f"Starting notifications on {self._rx_char_uuid}")
            await self._client.start_notify(self._rx_char_uuid, self._notification_handler)
            
            self._connected = True
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect: {e}")
            return False

    def _get_offline_data(self) -> Dict[str, Any]:
        """
        Return a dictionary with default values for all sensors when the device is offline.
        This ensures that the entities are still created in Home Assistant but appear as 'Unavailable'.
        """
        offline_data = {}
        
        try:
            from .const import DEVICE_SENSORS
        except ImportError:
            try:
                from const import DEVICE_SENSORS
            except ImportError:
                # Fallback sensor structure if imports fail
                DEVICE_SENSORS = []
        
        # Extract sensor keys from DEVICE_SENSORS tuple
        for sensor_desc in DEVICE_SENSORS:
            offline_data[sensor_desc.key] = None
        
        offline_data['connection_status'] = 'disconnected'
        offline_data['last_update'] = datetime.now().isoformat()
        _LOGGER.debug("Returning offline data structure.")
        return offline_data

    def get_data(self) -> Dict[str, Any]:
        """Return the latest device data."""
        if not self._connected:
            return self._get_offline_data()
        return self._last_data

    def get_test_data(self) -> Dict[str, Any]:
        """Return simulated test data for debugging purposes."""
        test_data = {
            'model_number': 'BTRIC-Test-Device',
            'battery_voltage': 12.6,
            'battery_current': 15.2,
            'battery_soc': 85,
            'battery_temp': 22,
            'solar_voltage': 18.4,
            'solar_current': 8.5,
            'solar_power': 156,
            'load_voltage': 12.5,
            'load_current': 3.2,
            'load_power': 40,
            'controller_temp': 28,
            'daily_power_generation': 1250,
            'daily_power_consumption': 850,
            'charging_status': 'MPPT',
            'power_generation_total': 145.67,
            'charging_amp_hours_today': 45.2,
            'discharging_amp_hours_today': 32.1,
            'connection_status': 'test_mode',
            'last_update': datetime.now().isoformat()
        }
        _LOGGER.info("Returning test data for debugging")
        return test_data

    @property
    def address(self) -> str:
        """Return the device MAC address"""
        return self.mac_address

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to device"""
        return self._client is not None and self._client.is_connected

    async def disconnect(self) -> None:
        """Disconnect from the device"""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            self._logger.info("🔌 Disconnected from device")
        self._connected = False

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_client') and self._client:
            try:
                asyncio.create_task(self._client.disconnect())
            except:
                pass 