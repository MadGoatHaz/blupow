# 🛠️ **IMPLEMENTATION GUIDE**

**BluPow Subprocess Coordinator Pattern**  
**For Home Assistant Integration Developers**  

---

## 🎯 **OVERVIEW**

This guide provides step-by-step instructions for implementing the subprocess-based coordinator pattern that solved the BluPow Bluetooth integration challenges. This pattern can be adapted for other complex device integrations.

---

## 📋 **PREREQUISITES**

### **System Requirements**
- Home Assistant Core 2024.1+
- Python 3.11+
- Bluetooth adapter with BLE support
- Container/system with appropriate permissions

### **Development Environment**
```bash
# Required packages
pip install bleak>=0.20.0
pip install homeassistant>=2024.1.0

# Development tools
pip install pytest
pip install black
pip install isort
```

### **Permissions Setup**
```bash
# For Docker/Container environments
docker run --privileged \
  --device /dev/bus/usb \
  -v /run/dbus:/run/dbus:ro \
  homeassistant/home-assistant
```

---

## 🏗️ **ARCHITECTURE COMPONENTS**

### **1. Core Files Structure**
```
custom_components/blupow/
├── __init__.py              # Integration setup
├── coordinator.py           # Subprocess coordinator
├── blupow_client.py        # Device client
├── sensor.py               # Sensor definitions
├── config_flow.py          # Configuration flow
├── const.py                # Constants
└── manifest.json           # Integration manifest
```

### **2. Key Classes**
- `BluPowCoordinator`: Main subprocess coordinator
- `BluPowClient`: Bluetooth device client
- `BluPowSensor`: Individual sensor entities

---

## 🔧 **STEP-BY-STEP IMPLEMENTATION**

### **Step 1: Create the Device Client**

```python
# blupow_client.py
import asyncio
import logging
from bleak import BleakClient
from typing import Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

class BluPowClient:
    """Bluetooth client for BluPow devices."""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client: Optional[BleakClient] = None
        
    async def connect(self) -> bool:
        """Connect to the device."""
        try:
            self.client = BleakClient(
                self.mac_address,
                timeout=20.0  # Extended timeout
            )
            
            connected = await self.client.connect()
            if connected:
                _LOGGER.info(f"Connected to {self.mac_address}")
                return True
            else:
                _LOGGER.error(f"Failed to connect to {self.mac_address}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            _LOGGER.info(f"Disconnected from {self.mac_address}")
    
    async def read_device_info(self) -> Dict[str, Any]:
        """Read device information and sensor data."""
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Client not connected")
        
        data = {}
        
        # Read different register sections
        registers = [
            (4000, 12, "system_info"),
            (4109, 20, "battery_data"),
            (4311, 8, "load_data"),
            (4327, 4, "temperature_data"),
            (4408, 8, "inverter_data")
        ]
        
        for start_reg, count, section in registers:
            try:
                section_data = await self._read_registers(start_reg, count)
                data.update(section_data)
            except Exception as e:
                _LOGGER.warning(f"Failed to read {section}: {e}")
        
        return data
    
    async def _read_registers(self, start_register: int, count: int) -> Dict[str, Any]:
        """Read Modbus registers via Bluetooth."""
        # Construct Modbus RTU command
        command = self._build_modbus_command(start_register, count)
        
        # Send command and read response
        await self.client.write_gatt_char(
            "0000fff2-0000-1000-8000-00805f9b34fb",  # Write characteristic
            command
        )
        
        # Read response
        response = await self.client.read_gatt_char(
            "0000fff1-0000-1000-8000-00805f9b34fb"   # Read characteristic
        )
        
        # Parse response
        return self._parse_modbus_response(response, start_register)
    
    def _build_modbus_command(self, start_register: int, count: int) -> bytes:
        """Build Modbus RTU command."""
        # Device ID + Function Code + Register + Count + CRC
        command = bytearray([
            0xFF,  # Device ID
            0x03,  # Read Holding Registers
            (start_register >> 8) & 0xFF,  # Start register high
            start_register & 0xFF,         # Start register low
            (count >> 8) & 0xFF,          # Count high
            count & 0xFF                  # Count low
        ])
        
        # Add CRC
        crc = self._calculate_crc(command)
        command.extend(crc.to_bytes(2, 'little'))
        
        return bytes(command)
    
    def _parse_modbus_response(self, response: bytes, start_register: int) -> Dict[str, Any]:
        """Parse Modbus response into sensor data."""
        if len(response) < 5:
            return {}
        
        # Skip header bytes (Device ID, Function Code, Data Length)
        # CRITICAL: Start from byte 3, not byte 2
        data_start = 3
        data = {}
        
        # Parse based on register range
        if start_register == 4000:
            # System information
            data.update(self._parse_system_info(response[data_start:]))
        elif start_register == 4109:
            # Battery data
            data.update(self._parse_battery_data(response[data_start:]))
        # ... other register ranges
        
        return data
    
    def _parse_system_info(self, data: bytes) -> Dict[str, Any]:
        """Parse system information registers."""
        if len(data) < 24:
            return {}
        
        return {
            'model': self._decode_string(data[0:16]),
            'firmware_version': f"{data[16]}.{data[17]}",
            'serial_number': int.from_bytes(data[18:22], 'big'),
            'rated_power': int.from_bytes(data[22:24], 'big')
        }
    
    def _calculate_crc(self, data: bytearray) -> int:
        """Calculate Modbus CRC."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
```

### **Step 2: Create the Subprocess Coordinator**

```python
# coordinator.py
import asyncio
import logging
from datetime import timedelta
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class BluPowCoordinator(DataUpdateCoordinator):
    """Subprocess-based coordinator for BluPow integration."""
    
    def __init__(self, hass: HomeAssistant, mac_address: str):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="BluPow",
            update_interval=timedelta(seconds=30),
        )
        self.mac_address = mac_address
        self._last_successful_data = {}
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data using subprocess execution."""
        try:
            _LOGGER.debug(f"Starting subprocess data fetch for {self.mac_address}")
            
            # Generate subprocess script
            script = self._generate_subprocess_script()
            
            # Execute subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                'python3', '-c', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=20.0
                )
                
                # Parse results
                output = stdout.decode().strip()
                error_output = stderr.decode().strip()
                
                if error_output:
                    _LOGGER.debug(f"Subprocess stderr: {error_output}")
                
                if output.startswith("SUCCESS:"):
                    # Parse successful data
                    data_str = output[8:]  # Remove "SUCCESS:" prefix
                    data = eval(data_str)  # Safe since we control the format
                    
                    if isinstance(data, dict) and len(data) > 0:
                        _LOGGER.info(f"✅ SUBPROCESS SUCCESS: Retrieved {len(data)} fields")
                        self._last_successful_data = data
                        return data
                    else:
                        _LOGGER.warning("Subprocess returned empty data")
                        return self._get_fallback_data()
                        
                elif output.startswith("ERROR:"):
                    error_msg = output[6:]  # Remove "ERROR:" prefix
                    _LOGGER.error(f"Subprocess reported error: {error_msg}")
                    return self._get_fallback_data()
                    
                else:
                    _LOGGER.error(f"Unexpected subprocess output: {output}")
                    return self._get_fallback_data()
                    
            except asyncio.TimeoutError:
                _LOGGER.error("Subprocess timed out after 20 seconds")
                if process.returncode is None:
                    process.kill()
                    await process.wait()
                return self._get_fallback_data()
                
        except Exception as exc:
            _LOGGER.error(f"Subprocess execution failed: {exc}")
            return self._get_fallback_data()
        finally:
            # Ensure process cleanup
            if 'process' in locals() and process.returncode is None:
                process.terminate()
                await process.wait()
    
    def _generate_subprocess_script(self) -> str:
        """Generate the subprocess execution script."""
        return f'''
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Add custom component path
sys.path.append("/config/custom_components")

async def get_data():
    """Main data retrieval function."""
    try:
        from blupow.blupow_client import BluPowClient
        
        client = BluPowClient("{self.mac_address}")
        
        # Attempt connection
        connected = await client.connect()
        if not connected:
            print("ERROR:Connection failed")
            return False
        
        # Read device data
        data = await client.read_device_info()
        
        # Disconnect
        await client.disconnect()
        
        # Validate and return data
        if data and len(data) > 0:
            # Convert to JSON-serializable format
            json_data = {{}}
            for k, v in data.items():
                if v is not None:
                    # Convert complex types to strings
                    if isinstance(v, (int, float, bool, str)):
                        json_data[k] = v
                    else:
                        json_data[k] = str(v)
                else:
                    json_data[k] = None
            
            print("SUCCESS:" + str(json_data))
            return True
        else:
            print("ERROR:No data retrieved")
            return False
            
    except ImportError as e:
        print(f"ERROR:Import failed: {{str(e)}}")
        return False
    except Exception as e:
        print(f"ERROR:{{str(e)}}")
        return False

# Execute main function
try:
    result = asyncio.run(get_data())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"ERROR:Execution failed: {{str(e)}}")
    sys.exit(1)
'''
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data when subprocess fails."""
        if self._last_successful_data:
            _LOGGER.info("Using last successful data as fallback")
            # Mark data as offline
            fallback = self._last_successful_data.copy()
            fallback['connection_status'] = 'offline'
            return fallback
        else:
            _LOGGER.warning("No fallback data available")
            return {
                'connection_status': 'offline',
                'model': 'Unknown',
                'input_voltage': None,
                'battery_voltage': None,
                'battery_soc': None,
                'load_power': None,
                'temperature': None
            }
```

### **Step 3: Integration Setup**

```python
# __init__.py
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .coordinator import BluPowCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BluPow from a config entry."""
    
    # Get MAC address from config
    mac_address = entry.data["mac_address"]
    
    # Create coordinator
    coordinator = BluPowCoordinator(hass, mac_address)
    
    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
```

### **Step 4: Sensor Definitions**

```python
# sensor.py
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_TYPES = {
    "input_voltage": {
        "name": "Input Voltage",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "icon": "mdi:flash",
    },
    "battery_voltage": {
        "name": "Battery Voltage", 
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "icon": "mdi:battery",
    },
    "battery_soc": {
        "name": "Battery SOC",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging",
    },
    "load_power": {
        "name": "Load Power",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:lightning-bolt",
    },
    "temperature": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
    },
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up BluPow sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(BluPowSensor(coordinator, sensor_type))
    
    async_add_entities(entities, True)

class BluPowSensor(CoordinatorEntity, SensorEntity):
    """BluPow sensor entity."""
    
    def __init__(self, coordinator, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self._attr_name = f"BluPow {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"blupow_{coordinator.mac_address}_{sensor_type}"
        
        # Set sensor properties
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.sensor_type)
        return None
    
    @property
    def available(self):
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success 
            and self.coordinator.data 
            and self.coordinator.data.get('connection_status') != 'offline'
        )
```

---

## 🔍 **DEBUGGING AND TROUBLESHOOTING**

### **Common Issues**

#### **1. Import Errors in Subprocess**
```python
# Problem: Module not found in subprocess
# Solution: Verify sys.path addition
sys.path.append("/config/custom_components")

# Debug: Add path verification
import sys
print(f"Python path: {sys.path}")
```

#### **2. Subprocess Timeout**
```python
# Problem: Subprocess hangs
# Solution: Increase timeout and add debug logging
try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(), timeout=30.0  # Increased timeout
    )
except asyncio.TimeoutError:
    _LOGGER.error("Subprocess timeout - check Bluetooth connectivity")
```

#### **3. Data Parsing Errors**
```python
# Problem: eval() fails on subprocess output
# Solution: Add validation
try:
    data = eval(data_str)
    if not isinstance(data, dict):
        raise ValueError("Invalid data format")
except (SyntaxError, ValueError) as e:
    _LOGGER.error(f"Data parsing failed: {e}")
    return fallback_data()
```

### **Debug Logging Setup**

```python
# Enable debug logging in configuration.yaml
logger:
  default: info
  logs:
    custom_components.blupow: debug
    custom_components.blupow.coordinator: debug
    custom_components.blupow.blupow_client: debug
```

### **Testing Commands**

```bash
# Test subprocess execution manually
python3 -c "
import asyncio
import sys
sys.path.append('/config/custom_components')

async def test():
    from blupow.blupow_client import BluPowClient
    client = BluPowClient('D8:B6:73:BF:4F:75')
    connected = await client.connect()
    if connected:
        data = await client.read_device_info()
        await client.disconnect()
        print(f'SUCCESS: {data}')
    else:
        print('ERROR: Connection failed')

asyncio.run(test())
"
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Bluetooth permissions configured
- [ ] MAC address validated
- [ ] Device pairing completed
- [ ] All dependencies installed
- [ ] Debug logging enabled

### **Integration Testing**
- [ ] Config flow completes successfully
- [ ] Coordinator starts without errors
- [ ] First data fetch succeeds
- [ ] Sensors appear in Home Assistant
- [ ] Sensor values update correctly
- [ ] Error handling works (device offline test)

### **Production Deployment**
- [ ] Update interval optimized
- [ ] Error logging configured
- [ ] Fallback data handling verified
- [ ] Resource usage monitored
- [ ] Integration stability confirmed

---

## 📊 **PERFORMANCE MONITORING**

### **Key Metrics to Track**

```python
# Add to coordinator for monitoring
class BluPowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, mac_address: str):
        super().__init__(...)
        self._metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'avg_execution_time': 0.0,
            'last_success_time': None,
        }
    
    async def _async_update_data(self):
        start_time = time.time()
        self._metrics['total_updates'] += 1
        
        try:
            result = await self._subprocess_update()
            self._metrics['successful_updates'] += 1
            self._metrics['last_success_time'] = time.time()
            return result
        except Exception:
            self._metrics['failed_updates'] += 1
            raise
        finally:
            execution_time = time.time() - start_time
            # Update rolling average
            self._metrics['avg_execution_time'] = (
                self._metrics['avg_execution_time'] * 0.9 + execution_time * 0.1
            )
```

### **Health Check Script**

```python
# scripts/health_check.py
import asyncio
import sys
sys.path.append("/config/custom_components")

async def health_check():
    """Check integration health."""
    from blupow.blupow_client import BluPowClient
    
    mac_address = "D8:B6:73:BF:4F:75"  # Replace with your device
    client = BluPowClient(mac_address)
    
    print("🔍 BluPow Health Check")
    print(f"Device: {mac_address}")
    
    try:
        print("📡 Attempting connection...")
        connected = await client.connect()
        
        if connected:
            print("✅ Connection successful")
            
            print("📊 Reading data...")
            data = await client.read_device_info()
            
            if data:
                print(f"✅ Data retrieved: {len(data)} fields")
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print("❌ No data retrieved")
            
            await client.disconnect()
            print("✅ Disconnected cleanly")
            
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## 🔧 **CUSTOMIZATION OPTIONS**

### **Adjustable Parameters**

```python
# coordinator.py - Customizable settings
class BluPowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, mac_address: str, **options):
        # Configurable update interval
        update_interval = options.get('update_interval', 30)
        
        # Configurable timeout
        self.subprocess_timeout = options.get('subprocess_timeout', 20.0)
        
        # Configurable retry attempts
        self.max_retries = options.get('max_retries', 3)
        
        super().__init__(
            hass,
            _LOGGER,
            name="BluPow",
            update_interval=timedelta(seconds=update_interval),
        )
```

### **Advanced Configuration**

```yaml
# configuration.yaml
blupow:
  mac_address: "D8:B6:73:BF:4F:75"
  update_interval: 30
  subprocess_timeout: 20.0
  max_retries: 3
  fallback_enabled: true
  debug_subprocess: false
```

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation References**
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Bleak Bluetooth Library](https://bleak.readthedocs.io/)
- [Modbus Protocol Specification](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)

### **Example Integrations**
- [Bluetooth LE Device Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/bluetooth_le_tracker)
- [Modbus Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus)

### **Testing Tools**
- `bluetoothctl` - Bluetooth device management
- `hcitool` - Bluetooth adapter tools
- `nmap` - Network/Bluetooth scanning
- Home Assistant Developer Tools

---

**Implementation Guide Version**: 1.0  
**Last Updated**: June 20, 2025  
**Compatibility**: Home Assistant 2024.1+ 