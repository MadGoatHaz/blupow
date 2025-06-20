# BluPow Authentication Research - Critical Hardware Discovery

**MAJOR UPDATE**: Device is **Renogy RIV1230RCH-SPS INVERTER**, not charge controller!

## 🚨 **CRITICAL DISCOVERY: WRONG DEVICE TYPE**

### **Evidence from Old Working Setup**
Analysis of the user's original working configuration reveals a fundamental misunderstanding:

```ini
# From working config.ini (OldRenogyBTSetup)
[device]
mac_addr = D8:B6:73:BF:4F:75
alias = BTRIC134000035
type = RNG_INVT  # <-- INVERTER, not RNG_CTRL!
device_id = 255

# From working example.py
InverterClient(config, on_data_received, on_error).start()  # <-- InverterClient!
```

### **Hardware Configuration**
- **Device**: Renogy RIV1230RCH-SPS (3000w Inverter Charger)
- **Bluetooth Module**: BTRIC134000035 (Bluetooth Remote for Inverter Charger)
- **Functionality**: AC inverter + battery charger + transfer switch + MPPT solar controller

### **BTRIC134000035 Naming Convention**
- **BTRIC** = Bluetooth Remote for Inverter Charger
- **RIC** = Remote Inverter Charger (NOT charge controller!)
- This confirms it's an **inverter** Bluetooth module

---

## 📊 **Protocol Differences: Inverter vs Charge Controller**

### **Inverter Protocol (CORRECT)**
Based on cyrils/renogy-bt InverterClient implementation:

**Register Sections:**
- **4000**: Inverter stats (10 words) - AC input/output, frequency, temperature
- **4109**: Device ID (1 word)
- **4311**: Model information (8 words) - "RIV1230RCH-SPS"
- **4327**: Charging info (7 words) - battery percentage, solar input
- **4408**: Load info (6 words) - AC load power, current consumption

**Expected Data Structure:**
```json
{
  "input_voltage": 124.9,      // AC mains input
  "input_current": 2.2,
  "output_voltage": 124.9,     // AC load output  
  "output_current": 1.19,
  "output_frequency": 59.97,   // 50/60Hz frequency
  "battery_voltage": 14.4,     // DC battery bank
  "temperature": 30.0,         // Inverter temperature
  "model": "RIV1230RCH-SPS",
  "battery_percentage": 100,
  "charging_current": 0.7,
  "solar_voltage": 0.0,        // Solar input (if connected)
  "solar_current": 0.0,
  "charging_status": "deactivated",
  "load_active_power": 108,    // AC power consumption
  "load_percentage": 5
}
```

### **Charge Controller Protocol (WRONG)**
What we were previously using:
- **Registers**: 0x0100-0x0106 (256-262 decimal)
- **Data**: PV voltage, PV current, battery charging only
- **No AC monitoring**: Missing input/output voltage, frequency, load power

---

## 🔧 **Implemented Corrections**

### **1. Updated BluPowClient (blupow_client.py)**
✅ **Register Sections**: Changed to inverter register addresses (4000, 4109, 4311, 4327, 4408)
✅ **Parsing Methods**: Added inverter-specific parsers
✅ **Data Reading**: Sequential register section reading
✅ **Command Generation**: Correct inverter register commands

### **2. Updated Sensor Definitions (const.py)**
✅ **22 Inverter Sensors**: AC input/output, frequency, load power, battery status
✅ **Proper Device Classes**: Voltage, current, frequency, power, temperature
✅ **Energy Dashboard Ready**: Optimized for Home Assistant energy monitoring

### **3. Updated Documentation**
✅ **README.md**: Changed from charge controller to inverter
✅ **CURRENT_STATUS.md**: Reflects hardware discovery
✅ **NEXT_STEPS.md**: Updated implementation plan

---

## 📋 **Complete Sensor List (22 Sensors)**

### **AC Power Monitoring**
1. **AC Input Voltage** - Mains power input (120V)
2. **AC Input Current** - Mains current draw
3. **AC Input Frequency** - Grid frequency (60Hz)
4. **AC Output Voltage** - Load power output (120V)
5. **AC Output Current** - Load current consumption
6. **AC Output Frequency** - Output frequency stability
7. **AC Load Power** - Active power consumption (W)
8. **AC Apparent Power** - Total power draw (VA)
9. **Load Current** - AC load current
10. **Load Percentage** - Load as % of capacity
11. **Line Charging Current** - AC charging current

### **Battery Bank Monitoring**
12. **Battery Voltage** - DC battery voltage
13. **Battery SOC** - State of charge percentage
14. **Battery Charging Current** - DC charging current
15. **Charging Status** - Charging mode (float/bulk/absorption)
16. **Charging Power** - Battery charging power

### **Solar Input (if connected)**
17. **Solar Input Voltage** - PV array voltage
18. **Solar Input Current** - PV array current
19. **Solar Input Power** - Solar power generation

### **System Health**
20. **Inverter Temperature** - Internal temperature monitoring
21. **Inverter Model** - Device model identification
22. **Device ID** - Modbus device identifier

---

## 🎯 **Expected Results After Correction**

### **Connection Success**
- Device should connect immediately with correct inverter protocol
- No more `ESP_GATT_CONN_FAIL_ESTABLISH` errors
- All 5 register sections should read successfully

### **Rich Data Flow**
- **AC Monitoring**: Real-time household power consumption
- **Battery Status**: SOC, voltage, charging status
- **Solar Integration**: PV input monitoring (if connected)
- **System Health**: Temperature, frequency stability

### **Home Assistant Integration**
- **Energy Dashboard**: Complete AC power monitoring
- **22 Sensors**: All populated with real inverter data
- **Update Frequency**: 30-second refresh cycles
- **Automation Ready**: Sensors available for automations

---

## 🚀 **Next Testing Steps**

### **1. Deploy Updated Code**
```bash
./scripts/deploy.sh
```

### **2. Monitor Connection**
```bash
docker logs homeassistant | grep -i blupow | tail -20
```

### **3. Look for Success Indicators**
```
✅ Reading register 4000, 10 words
✅ Section 4000: 8 fields  
✅ Reading register 4109, 1 words
✅ Section 4109: 1 fields
✅ Reading register 4311, 8 words  
✅ Section 4311: 1 fields (model: "RIV1230RCH-SPS")
✅ Total inverter data collected: 22 fields
```

### **4. Verify Sensor Population**
- Check Home Assistant sensor dashboard
- All 22 sensors should show real values instead of "Unavailable"
- AC voltages should show ~120V
- Frequency should show ~60Hz

---

## 📈 **Value Proposition Enhancement**

### **Before (Incorrect)**
- Basic solar charge controller monitoring
- Limited to PV input and battery charging
- Narrow use case

### **After (Correct)**  
- **Complete household AC power monitoring**
- **Whole-house energy consumption tracking**
- **Grid/battery/solar power flow monitoring**
- **Integration with Home Assistant Energy Dashboard**
- **Foundation for home energy automation**

**This transforms the project from a niche solar monitoring tool to a comprehensive household energy management system!**

---

## 💡 **Why This Makes Perfect Sense**

1. **Device Naming**: BTRIC = Bluetooth Remote for Inverter Charger
2. **3000w Capacity**: Way beyond typical charge controller range
3. **AC Functionality**: Inverters handle AC input/output, not charge controllers  
4. **Multiple Functions**: Inverter + charger + transfer switch + MPPT solar
5. **Connection Issues**: Inverters have different sleep patterns than charge controllers

The user's original working setup was correctly configured for an inverter. Our new implementation should connect immediately and provide comprehensive AC power monitoring.

# BluPow Authentication Research & Implementation Plan

**Created:** June 19, 2025
**Status:** 🔬 **Research Phase**
**Priority:** 🚨 **Critical - Blocking all data reading**

## 🎯 **Problem Statement**

The BluPow integration successfully connects to Renogy devices but cannot read data due to Bluetooth GATT authentication/authorization issues. This document outlines the research and implementation plan to resolve these issues.

## 📊 **Current Evidence**

### **Connection Success Indicators**
```
✅ Device discovery: "Found BLE device: BTRIC134000035"
✅ Connection establishment: "Connection successful. Starting notification handler."
✅ Service discovery: "Starting notifications on 0000ffd0-0000-1000-8000-00805f9b34fb"
```

### **Authentication Failure Indicators**
```
❌ Data reading blocked: "Insufficient authorization (8)"
❌ GATT errors: "Bluetooth GATT Error handle=29 error=133 description=Error"
❌ Characteristic access: "TX characteristic not found"
❌ Write failures: "BluetoothGATTErrorResponse: Insufficient authorization (8)"
```

## 🔍 **Research Areas**

### **1. Renogy BT-2 Module Security Model**

**Research Questions:**
- Does the BT-2 module require explicit pairing/bonding?
- Is there a PIN/passkey authentication mechanism?
- Are there specific security commands or handshakes required?
- Does the device need to be put in "pairing mode"?

**Sources to Investigate:**
- Renogy BT-2 module manual and documentation
- `cyrils/renogy-bt` implementation analysis
- Other successful Renogy Bluetooth implementations
- Renogy official app behavior analysis

### **2. Bluetooth LE Security Levels**

**Current Understanding:**
- GATT Error 133 typically indicates authentication/authorization failure
- "Insufficient authorization (8)" suggests the characteristic requires higher security level
- Device may require bonding before allowing data access

**Research Needed:**
- What security level does the Renogy device require?
- Does it need encryption, authentication, or both?
- Are there specific GATT security descriptors to check?

### **3. Service and Characteristic Analysis**

**Current Status:**
- Service UUID: `0000ffd0-0000-1000-8000-00805f9b34fb` (detected)
- TX characteristic: Not found after connection
- RX characteristic: Status unknown

**Research Needed:**
- Complete service discovery and characteristic enumeration
- Identify security requirements for each characteristic
- Map characteristics to their required security levels

## 🛠️ **Implementation Plan**

### **Phase 1: Enhanced Service Discovery (1-2 days)**

**Objective:** Properly discover and analyze all GATT services and characteristics

**Tasks:**
1. **Implement comprehensive service discovery**
   ```python
   async def _discover_services_detailed(self):
       """Comprehensive service and characteristic discovery"""
       services = await self._client.get_services()
       for service in services:
           _LOGGER.debug(f"Service: {service.uuid}")
           for char in service.characteristics:
               _LOGGER.debug(f"  Characteristic: {char.uuid}")
               _LOGGER.debug(f"    Properties: {char.properties}")
               _LOGGER.debug(f"    Descriptors: {len(char.descriptors)}")
               for desc in char.descriptors:
                   _LOGGER.debug(f"      Descriptor: {desc.uuid}")
   ```

2. **Analyze characteristic properties and security requirements**
3. **Document the complete GATT structure**

### **Phase 2: Authentication Implementation (2-3 days)**

**Objective:** Implement proper device authentication/pairing

**Tasks:**
1. **Research Renogy-specific authentication sequence**
   - Study `cyrils/renogy-bt` for authentication patterns
   - Analyze successful implementations
   - Document required authentication steps

2. **Implement pairing/bonding support**
   ```python
   async def _authenticate_device(self):
       """Implement device authentication based on research"""
       try:
           # Method 1: Try explicit pairing
           await self._client.pair()
           
           # Method 2: Try PIN/passkey if required
           # await self._handle_pin_authentication()
           
           # Method 3: Try Renogy-specific auth sequence
           # await self._renogy_auth_sequence()
           
       except Exception as e:
           _LOGGER.error(f"Authentication failed: {e}")
           return False
       return True
   ```

3. **Add authentication retry logic**
4. **Handle different authentication methods**

### **Phase 3: Characteristic Access Fix (1 day)**

**Objective:** Resolve "TX characteristic not found" and access issues

**Tasks:**
1. **Fix characteristic discovery and caching**
2. **Implement proper characteristic access with security**
3. **Add characteristic write/read with authentication**

### **Phase 4: Testing and Validation (1 day)**

**Objective:** Validate authentication and data reading

**Tasks:**
1. **Create standalone authentication test script**
2. **Test data reading after successful authentication**
3. **Validate sensor data population**

## 🔬 **Research Methodology**

### **1. Code Analysis**
- **Primary Source:** `cyrils/renogy-bt` repository
- **Focus:** Authentication sequences, security handling, characteristic access
- **Extract:** Working authentication patterns and security requirements

### **2. Protocol Analysis**
- **Bluetooth LE specification review**
- **GATT security model analysis**
- **Renogy-specific protocol documentation**

### **3. Experimental Testing**
- **Try different authentication methods**
- **Test various security levels**
- **Analyze device responses to different approaches**

## 📋 **Research Tasks**

### **Immediate Tasks (Next 2 days)**
- [ ] Analyze `cyrils/renogy-bt` authentication implementation
- [ ] Research Renogy BT-2 module documentation
- [ ] Implement comprehensive service discovery
- [ ] Document current GATT structure and security requirements

### **Implementation Tasks (Days 3-5)**
- [ ] Implement authentication methods based on research
- [ ] Fix characteristic discovery and access
- [ ] Add proper error handling for authentication failures
- [ ] Test authentication with real device

### **Validation Tasks (Days 6-7)**
- [ ] Create comprehensive test suite
- [ ] Validate data reading after authentication
- [ ] Test integration stability
- [ ] Document authentication requirements

## 🎯 **Success Criteria**

### **Phase 1 Success: Service Discovery**
- Complete enumeration of all services and characteristics
- Documentation of security requirements for each characteristic
- Clear understanding of authentication requirements

### **Phase 2 Success: Authentication**
- Device authenticates successfully without authorization errors
- All characteristics are accessible for read/write operations
- No "Insufficient authorization" or GATT error 133

### **Phase 3 Success: Data Reading**
- Raw sensor data is successfully read from device
- All 18 sensors populate with real data
- Regular updates work reliably

## 📚 **Documentation Requirements**

### **Research Documentation**
- Complete analysis of Renogy authentication requirements
- GATT security model documentation
- Characteristic security requirements mapping

### **Implementation Documentation**
- Authentication sequence documentation
- Error handling and retry logic
- Testing procedures and validation methods

### **User Documentation**
- Troubleshooting guide updates
- Authentication failure resolution steps
- Device pairing instructions if required

## ⚠️ **Risk Assessment**

### **High Risk**
- Renogy devices may require proprietary authentication not documented publicly
- Authentication may require physical device interaction (pairing button, etc.)
- Security requirements may vary between device firmware versions

### **Medium Risk**
- Implementation complexity may exceed initial estimates
- Authentication may require specific timing or sequence
- Device may need to be reset or put in special mode

### **Low Risk**
- Standard Bluetooth LE authentication methods should work
- Existing implementations provide good reference
- GATT security model is well-documented

## 📈 **Timeline**

**Week 1 (Days 1-7):**
- Research and analysis phase
- Authentication implementation
- Initial testing and validation

**Week 2 (Days 8-14):**
- Refinement and optimization
- Comprehensive testing
- Documentation and integration

**Target Completion:** End of Week 2
**Fallback Plan:** If authentication proves more complex, extend to Week 3 with additional research

---

**Next Action:** Begin analysis of `cyrils/renogy-bt` authentication implementation and Renogy BT-2 documentation. 