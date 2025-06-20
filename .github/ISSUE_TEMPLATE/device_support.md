---
name: Device Support Request
about: Request support for a new device model
title: '[DEVICE] Support for [Device Model]'
labels: ['device-support', 'enhancement', 'needs-triage']
assignees: ['MadGoatHaz']
---

## 📱 **Device Information**

### **Basic Details**
- **Manufacturer:** [e.g. Renogy, AIMS, etc.]
- **Model:** [e.g. RIV1230RCH-SPS]
- **Product Name:** [Full product name]
- **SKU/Part Number:** [if available]

### **Technical Specifications**
- **Input Voltage Range:** [e.g. 12V, 24V, 48V]
- **Output Power:** [e.g. 1200W, 2000W]
- **Battery Type Support:** [e.g. LiFePO4, AGM, Gel]
- **Communication Protocol:** [e.g. Bluetooth, RS485, CAN]

### **Connectivity**
- **Bluetooth:** 
  - [ ] Yes - BLE (Bluetooth Low Energy)
  - [ ] Yes - Classic Bluetooth
  - [ ] No
  - [ ] Unknown
- **Other Interfaces:**
  - [ ] RS485/Modbus RTU
  - [ ] CAN Bus
  - [ ] WiFi
  - [ ] USB
  - [ ] Other: _____________

## 🔍 **Device Discovery**

### **Bluetooth Information** (if applicable)
- **Device Name:** [as shown in Bluetooth scan]
- **MAC Address:** [e.g. D8:B6:73:BF:4F:75]
- **Manufacturer Data:** [if visible in scan]
- **Service UUIDs:** [if known]

### **Detection Method**
- [ ] Appears in Home Assistant Bluetooth integration
- [ ] Visible in phone/computer Bluetooth scan
- [ ] Requires special pairing process
- [ ] Not detectable yet

## 📊 **Available Data/Sensors**
What data does this device provide? Check all that apply:

### **Power Metrics**
- [ ] Input Voltage
- [ ] Input Current
- [ ] Input Power
- [ ] Output Voltage
- [ ] Output Current
- [ ] Output Power
- [ ] Load Power
- [ ] Load Percentage

### **Battery Metrics**
- [ ] Battery Voltage
- [ ] Battery Current
- [ ] Battery Power
- [ ] Battery SOC (State of Charge)
- [ ] Battery Temperature
- [ ] Battery Type Detection

### **System Metrics**
- [ ] Device Temperature
- [ ] Fan Speed
- [ ] Operating Mode
- [ ] Fault Codes
- [ ] Efficiency Rating
- [ ] Runtime Statistics

### **Solar/Charging (if applicable)**
- [ ] Solar Voltage
- [ ] Solar Current
- [ ] Solar Power
- [ ] Charging Status
- [ ] Charging Mode

## 🔧 **Technical Documentation**

### **Available Documentation**
- [ ] User Manual
- [ ] Technical Specification Sheet
- [ ] Communication Protocol Documentation
- [ ] API Documentation
- [ ] Mobile App Available
- [ ] PC Software Available

### **Documentation Links**
```
Provide links to any available documentation:
- User Manual: 
- Spec Sheet: 
- Protocol Docs: 
- Other: 
```

## 🧪 **Testing Availability**

### **Device Access**
- [ ] I own this device and can test
- [ ] I can borrow this device for testing
- [ ] I know someone who has this device
- [ ] I'm planning to purchase this device
- [ ] I don't have access but want support

### **Testing Commitment**
- [ ] I can provide detailed testing feedback
- [ ] I can run diagnostic scripts
- [ ] I can capture Bluetooth traffic
- [ ] I can test development versions
- [ ] I can help with documentation

## 📱 **Existing Software**

### **Manufacturer Apps**
- **Mobile App:** [Name and platform]
- **PC Software:** [Name and OS]
- **Web Interface:** [Yes/No]

### **Third-Party Support**
- [ ] Works with other Home Assistant integrations
- [ ] Compatible with other home automation platforms
- [ ] Has unofficial API/protocol documentation
- [ ] Community reverse-engineering efforts

## 💻 **Protocol Investigation**

### **Communication Analysis** (if attempted)
- [ ] Bluetooth traffic captured
- [ ] Protocol partially reverse-engineered  
- [ ] Similar to existing supported devices
- [ ] Completely unknown protocol

### **Technical Details**
```
If you have any technical information about the communication protocol:
- Service UUIDs:
- Characteristic UUIDs:
- Data format:
- Command structure:
- Response format:
```

## 🎯 **Priority and Impact**

### **User Demand**
- [ ] High - Many users requesting this device
- [ ] Medium - Some interest in community
- [ ] Low - Personal request
- [ ] Unknown - First request

### **Market Presence**
- [ ] Popular/common device
- [ ] Newer model gaining popularity
- [ ] Niche/specialized device
- [ ] Legacy device

## 🤝 **Contribution Offer**

### **How I Can Help**
- [ ] Device testing and validation
- [ ] Documentation creation
- [ ] Code contribution (if I have skills)
- [ ] Community support and feedback
- [ ] Financial support for development
- [ ] Device loan/donation for development

### **Development Support**
- [ ] I can provide remote access to device
- [ ] I can ship device to developer
- [ ] I can collaborate on protocol analysis
- [ ] I can help with user documentation

## 📸 **Device Photos/Screenshots**
Please include:
- Photos of the device (front, back, labels)
- Screenshots of any existing apps
- Bluetooth scan results
- Any relevant technical labels/stickers

## 🔗 **Related Information**
- Link to manufacturer's product page
- Related forum discussions
- Similar device support requests
- Compatible device models

## 📝 **Additional Context**
Any other information that might be helpful for implementing support for this device.

## ✅ **Checklist**
- [ ] I have provided complete device information
- [ ] I have checked if this device is already supported
- [ ] I have searched for existing requests for this device
- [ ] I am willing to help with testing if needed
- [ ] I understand this may take time to implement

---

**💡 Note:** Device support requests require significant development and testing effort. Providing detailed information and offering to help with testing greatly increases the chances of implementation! 