# BluPow + Renogy-BT Integration Plan

**ETHOS**: Quality through understanding. Every component has its place. Document thoroughly without clutter. Full comprehension before action.

## Strategic Overview

BluPow will leverage the proven [cyrils/renogy-bt](https://github.com/cyrils/renogy-bt/tree/main/renogybt) library as its communication foundation, creating a future-ready, modular architecture for multi-device Renogy integration.

## Key Benefits of Renogy-BT Foundation

### ✅ **Proven Protocol Implementation**
- Correct Modbus-over-Bluetooth implementation
- Device identification and register mapping
- Robust error handling and connection management

### ✅ **Multi-Device Support**
- Inverter support (RIV1230RCH-SPS)
- Charge controller support (RNG-CTRL-RVR40)
- Battery management system integration

### ✅ **Future-Ready Architecture**
- Modular device classes
- Extensible for new device types
- Clean separation of concerns

## Integration Strategy

### **Option A: Dependency Integration (RECOMMENDED)**
- Add renogy-bt as a dependency
- Create BluPow wrapper classes
- Maintain our own Home Assistant integration layer
- Benefits: Automatic updates, community maintenance

### **Option B: Fork & Customize**
- Fork renogy-bt repository
- Customize for BluPow-specific needs
- Maintain our own version
- Benefits: Full control, custom features

### **Option C: Code Adaptation**
- Extract core communication logic
- Integrate directly into BluPow
- Benefits: No external dependencies

## Recommended Architecture

```python
# BluPow Integration Layer
class BluPowDevice:
    """Home Assistant integration wrapper"""
    
class BluPowInverter(BluPowDevice):
    """Wraps renogy-bt inverter functionality"""
    def __init__(self, mac_address):
        from renogybt import InverterClient
        self.client = InverterClient(mac_address)
    
class BluPowController(BluPowDevice):
    """Wraps renogy-bt controller functionality"""
    def __init__(self, mac_address):
        from renogybt import ControllerClient  
        self.client = ControllerClient(mac_address)
```

## Device Type Mapping

### **Inverter (RIV1230RCH-SPS)**
```python
INVERTER_CAPABILITIES = {
    "ac_input_monitoring": True,
    "ac_output_monitoring": True, 
    "battery_management": True,
    "solar_passthrough": True,
    "load_monitoring": True
}
```

### **Charge Controller (RNG-CTRL-RVR40)**
```python
CONTROLLER_CAPABILITIES = {
    "solar_mppt": True,
    "battery_charging": True,
    "generation_statistics": True,
    "dc_load_monitoring": True,
    "ac_monitoring": False  # Key difference
}
```

## Future Device Expansion

### **Modular Device Registry**
```python
DEVICE_REGISTRY = {
    # Current devices
    "D8:B6:73:BF:4F:75": {"type": "inverter", "model": "RIV1230RCH-SPS"},
    "C4:D3:6A:66:7E:D4": {"type": "controller", "model": "RNG-CTRL-RVR40"},
    
    # Future devices (examples)
    # "XX:XX:XX:XX:XX:XX": {"type": "battery", "model": "RBT100LFP12S"},
    # "YY:YY:YY:YY:YY:YY": {"type": "monitor", "model": "ONE-CORE"},
}
```

### **Extensible Device Factory**
```python
class DeviceFactory:
    @staticmethod
    def create_device(mac_address: str) -> BluPowDevice:
        device_info = DEVICE_REGISTRY.get(mac_address)
        device_type = device_info["type"]
        
        if device_type == "inverter":
            return BluPowInverter(mac_address)
        elif device_type == "controller":
            return BluPowController(mac_address)
        elif device_type == "battery":
            return BluPowBattery(mac_address)  # Future
        # Easy to add new types
```

## Implementation Phases

### **Phase 1: Foundation Setup**
1. Research renogy-bt library structure
2. Create integration wrapper classes
3. Test basic communication

### **Phase 2: Device-Specific Implementation**
1. Implement inverter wrapper
2. Implement controller wrapper  
3. Create device-specific sensor definitions

### **Phase 3: Home Assistant Integration**
1. Update coordinator for multi-device support
2. Implement device-specific sensors
3. Add dynamic device discovery

### **Phase 4: Testing & Validation**
1. Real device communication tests
2. Multi-device coordination tests
3. Home Assistant integration tests

### **Phase 5: Documentation & Deployment**
1. Update all documentation
2. Create migration guide
3. Deploy to production

## Technical Specifications

### **Communication Protocol**
- **Protocol**: Modbus over Bluetooth LE
- **Library**: renogy-bt handles protocol details
- **Connection**: Direct device communication
- **Fallback**: Maintain fallback for connection failures

### **Data Flow**
```
Renogy Device → renogy-bt → BluPow Wrapper → HA Coordinator → HA Sensors
```

### **Error Handling**
- Connection failures gracefully handled
- Device-specific error codes mapped
- Automatic retry mechanisms
- Fallback data when needed

## Future Considerations

### **New Device Types**
- Battery Management Systems
- Monitoring devices (Renogy ONE)
- DC-DC chargers
- Additional inverter models

### **Enhanced Features**
- Real-time parameter adjustment
- Advanced monitoring
- Energy dashboard integration
- Automation triggers

### **Scalability**
- Multiple device support
- Device grouping
- System-wide monitoring
- Performance optimization

## Success Metrics

1. **Real Device Communication**: 90%+ success rate
2. **Data Accuracy**: Real sensor readings, not fallback
3. **Device Differentiation**: Unique data per device type
4. **Future Ready**: Easy addition of new device types
5. **Maintainability**: Clean, modular codebase

**ETHOS REMINDER**: Every component has its place. Quality through understanding. Full comprehension before action. 