---
name: Bug Report
about: Report a bug or issue with BluPow
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ['MadGoatHaz']
---

## 🐛 **Bug Description**
A clear and concise description of what the bug is.

## 🔄 **Steps to Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## ✅ **Expected Behavior**
A clear and concise description of what you expected to happen.

## ❌ **Actual Behavior**
A clear and concise description of what actually happened.

## 📊 **Environment Information**

### **Home Assistant**
- Home Assistant Version: [e.g. 2024.1.0]
- Installation Type: [e.g. Docker, Supervised, Core, OS]
- Operating System: [e.g. Ubuntu 22.04, Raspberry Pi OS]

### **BluPow Integration**
- BluPow Version: [e.g. 2.0.0]
- Installation Method: [e.g. HACS, Manual]
- Configuration Method: [e.g. UI, YAML]

### **Device Information**
- Device Model: [e.g. Renogy RIV1230RCH-SPS]
- Device MAC Address: [e.g. D8:B6:73:BF:4F:75]
- Firmware Version: [if known]
- Bluetooth Adapter: [e.g. Built-in, USB dongle model]

## 📋 **Logs**

### **Home Assistant Logs**
```
Paste your Home Assistant logs here (Settings > System > Logs)
Filter for 'blupow' or 'custom_components.blupow'
```

### **BluPow Debug Logs**
```
Enable debug logging by adding to configuration.yaml:
logger:
  logs:
    custom_components.blupow: debug

Then paste the debug logs here
```

## 📸 **Screenshots**
If applicable, add screenshots to help explain your problem.

## 🔧 **Configuration**

### **Configuration.yaml** (if applicable)
```yaml
# Paste your BluPow configuration here
```

### **Integration Configuration**
- [ ] Configured via UI
- [ ] Configured via YAML
- [ ] Using default settings
- [ ] Using custom settings

**Custom Settings:**
```
List any custom configuration options you've set
```

## 🧪 **Troubleshooting Attempted**
- [ ] Restarted Home Assistant
- [ ] Reloaded the integration
- [ ] Checked Bluetooth connectivity
- [ ] Ran diagnostic tools
- [ ] Reviewed documentation
- [ ] Searched existing issues

**Details:**
```
Describe what troubleshooting steps you've already tried
```

## 📈 **Sensor Status**
- [ ] All sensors working
- [ ] Some sensors working
- [ ] No sensors working
- [ ] Sensors showing "Unavailable"
- [ ] Sensors showing incorrect values

**Affected Sensors:**
```
List which specific sensors are affected
```

## 🔗 **Related Issues**
- Link to any related issues or discussions
- Reference any similar problems you've found

## 📝 **Additional Context**
Add any other context about the problem here.

## ✅ **Checklist**
- [ ] I have searched existing issues for this problem
- [ ] I have provided all requested information
- [ ] I have included relevant logs
- [ ] I have tried basic troubleshooting steps
- [ ] I am running a supported version of Home Assistant
- [ ] My device is compatible with BluPow

---

**💡 Tip:** For faster resolution, provide as much detail as possible. The more information you give us, the quicker we can help! 