# BluPow Multi-Device Home Assistant Integration

**ETHOS**: Quality through understanding. Every component has its place. Document thoroughly without clutter. Full comprehension before action.

## Project Overview

BluPow is a comprehensive Home Assistant integration for Renogy devices that provides real-time monitoring and control of multiple device types through Bluetooth Low Energy communication. Built on the proven [cyrils/renogy-bt](https://github.com/cyrils/renogy-bt) foundation, BluPow offers a modular, future-ready architecture for expanding solar energy system monitoring.

## Current Device Support

### **Inverter Devices**
- **RIV1230RCH-SPS** (Built-in BLE)
  - MAC: D8:B6:73:BF:4F:75
  - Device ID: 32
  - **Capabilities**: AC Input/Output monitoring, Battery management, Load monitoring, Solar pass-through
  - **Unique Sensors**: AC voltage/current/frequency, Load active/apparent power, Line charging

### **Charge Controllers**  
- **RNG-CTRL-RVR40** (BT-2 Module)
  - MAC: C4:D3:6A:66:7E:D4
  - Device ID: 96
  - **Capabilities**: Solar MPPT, Battery charging, Generation statistics, DC load monitoring
  - **Unique Sensors**: PV voltage/current/power, Charging algorithms, Generation stats

## Architecture Principles

### **1. Device Type Segregation**
- **Strict Type Isolation**: Each device type has completely separate data structures
- **Capability-Based Access**: Devices only expose sensors they actually support  
- **No Cross-Contamination**: Inverter data never mixes with controller data

### **2. Protocol Foundation**
- **Base Protocol**: Modbus over Bluetooth LE
- **Library Foundation**: [cyrils/renogy-bt](https://github.com/cyrils/renogy-bt) proven implementation
- **Communication**: Direct device communication with robust fallback system

### **3. Future-Ready Design**
- **Modular Device Classes**: Easy addition of new device types
- **Extensible Sensor Framework**: Dynamic sensor loading based on device capabilities
- **Device Registry**: Centralized device type and capability management

## Technical Architecture

### **Data Flow**
```
Renogy Device → renogy-bt → BluPow Wrapper → HA Coordinator → HA Sensors
```

### **Component Structure**
```
BluPow/
├── blupow_client.py          # Current legacy client (to be replaced)
├── coordinator.py            # Multi-device coordinator
├── sensor.py                 # Dynamic sensor framework
├── const.py                  # Device definitions and constants
├── device_factory.py         # Device type factory (future)
├── devices/
│   ├── blupow_inverter.py    # Inverter wrapper (future)
│   ├── blupow_controller.py  # Controller wrapper (future)
│   └── blupow_battery.py     # Battery wrapper (future)
└── docs/                     # Comprehensive documentation
```

## Current Status

### **✅ What's Working**
1. **Multi-Device Detection**: Both devices properly detected and configured
2. **Home Assistant Integration**: Fully loaded with 22-23 entities per device
3. **Fallback System**: Robust fallback prevents "Unavailable" sensors
4. **Project Organization**: Comprehensive tooling and documentation

### **❌ Critical Issues**
1. **Connection Failures**: 90%+ Bluetooth connection failures on both devices
2. **Fake Data**: Integration using hardcoded fallback data instead of real device communication
3. **Device Confusion**: Both devices showing similar data instead of device-specific information
4. **Protocol Mismatch**: Current client doesn't use proper Modbus-over-Bluetooth protocol

## Integration Roadmap

### **Phase 1: Foundation Setup** (Week 1)
1. **Install renogy-bt dependency**
2. **Create BluPow wrapper classes**
3. **Test basic device communication**
4. **Verify protocol compatibility**

**Deliverables:**
- `blupow_renogy_client.py` - New client based on renogy-bt
- `device_factory.py` - Device type factory
- `communication_test.py` - Real device communication tests

### **Phase 2: Device-Specific Implementation** (Week 2)
1. **Implement inverter wrapper**
2. **Implement controller wrapper**
3. **Create device-specific sensors**
4. **Map register data to HA entities**

**Deliverables:**
- `blupow_inverter.py` - Inverter device class
- `blupow_controller.py` - Controller device class
- `const_inverter.py` - Inverter sensor definitions
- `const_controller.py` - Controller sensor definitions

### **Phase 3: Home Assistant Integration** (Week 3)
1. **Update coordinator for multi-device support**
2. **Implement dynamic sensor loading**
3. **Add device discovery**
4. **Create migration from current system**

**Deliverables:**
- `multi_device_coordinator.py` - New coordinator
- `dynamic_sensor_loader.py` - Capability-based sensor loading
- `migration_script.py` - Migration from current system

### **Phase 4: Testing & Deployment** (Week 4)
1. **Real device communication tests**
2. **Multi-device coordination tests**
3. **Home Assistant integration tests**
4. **Production deployment**

## Device Capabilities Matrix

| Feature | Inverter (RIV1230RCH-SPS) | Controller (RNG-CTRL-RVR40) |
|---------|---------------------------|------------------------------|
| **AC Input Monitoring** | ✅ Voltage, Current, Frequency | ❌ Not applicable |
| **AC Output Monitoring** | ✅ Voltage, Current, Frequency, Power | ❌ Not applicable |
| **Load Monitoring** | ✅ Active Power, Apparent Power, % | ✅ DC Load only |
| **Solar MPPT** | ✅ Pass-through only | ✅ Full MPPT control |
| **Battery Management** | ✅ Charging, Voltage, SOC | ✅ Charging algorithms |
| **Generation Statistics** | ✅ Basic stats | ✅ Daily/Total generation |
| **Temperature Monitoring** | ✅ Inverter temp | ✅ Controller temp |

## Future Expansion Plan

### **Additional Device Types**
- **Battery Management Systems**: RBT100LFP12S, RBT200LFP12-BT
- **DC-DC Chargers**: DCC50S, RBC50D1S-G1
- **Monitoring Devices**: Renogy ONE, Smart Shunt
- **Additional Inverters**: RIV4835CSH1S, other models

### **Enhanced Features**
- **Real-time Parameter Adjustment**: Change device settings via HA
- **Advanced Monitoring**: Historical data, trend analysis
- **Energy Dashboard Integration**: Native HA energy dashboard support
- **Automation Triggers**: Device state-based automations

## Success Metrics

1. **Real Device Communication**: 90%+ success rate for Bluetooth connections
2. **Data Accuracy**: Real sensor readings from actual devices, not fallback data
3. **Device Differentiation**: Unique, device-specific data for each device type
4. **Future Ready**: Easy addition of new device types with minimal code changes
5. **Maintainability**: Clean, modular codebase with comprehensive documentation

## Documentation Structure

### **Core Documentation**
- `PROJECT_OVERVIEW.md` - This comprehensive overview
- `TECHNICAL_ARCHITECTURE.md` - Detailed technical specifications
- `DEVICE_DISCOVERY_GUIDE.md` - Multi-device setup and configuration
- `RENOGY_BT_INTEGRATION_PLAN.md` - Integration strategy and implementation

### **Implementation Guides**
- `IMPLEMENTATION_GUIDE.md` - Step-by-step implementation
- `DEVELOPER_GUIDE.md` - Development standards and practices
- `VERIFICATION_GUIDE.md` - Testing and validation procedures

### **Troubleshooting**
- `TROUBLESHOOTING.md` - Common issues and solutions
- `BLUETOOTH_CONNECTION_GUIDE.md` - Bluetooth-specific troubleshooting

## Key Principles

1. **Quality Through Understanding**: Full comprehension before making changes
2. **Modular Design**: Every component has its specific place and purpose
3. **Device Type Respect**: Never mix data between different device types
4. **Future-Ready**: Architecture supports easy expansion to new device types
5. **Documentation First**: Comprehensive documentation for all components
6. **Real Data Priority**: Always prefer real device communication over fallback data

## Next Steps

1. **Review and approve** the renogy-bt integration approach
2. **Begin Phase 1 implementation** with dependency integration
3. **Set up development environment** for testing with real devices
4. **Create backup** of current working system before major changes

**ETHOS REMINDER**: Quality through understanding. Every component has its place. Document thoroughly without clutter. Full comprehension before action.

---

<p align="center">
  <strong>🚀 Welcome to the BluPow Revolution!</strong><br/>
  <em>Transform your energy monitoring experience today</em>
</p>

---

*This overview represents years of development, breakthrough innovations, and community collaboration. BluPow continues to evolve as the definitive Bluetooth power monitoring solution for Home Assistant.* 