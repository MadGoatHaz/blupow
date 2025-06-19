BluPow Project Handover & Workflow
Last Updated: 2025-06-19

## 1. Project Status
**Current State: DEBUGGING - PERSISTENT DEPLOYMENT ISSUES**

The BluPow integration has encountered persistent deployment and initialization issues that need systematic resolution.

### Critical Issues Identified:
1. **ImportError: `async_get_connectable_bleak_client`** - This function doesn't exist in the current Home Assistant version
2. **AttributeError: 'NoneType' object has no attribute 'get'** - Coordinator data is None when sensors are initialized
3. **Deployment Issues** - Code changes not properly propagating to Home Assistant

### Accomplishments:
- ✅ Basic integration structure is correct
- ✅ Config flow works for device discovery
- ✅ Bluetooth device detection functional
- ❌ Sensor initialization fails due to coordinator timing
- ❌ Import compatibility issues with current HA version

## 2. Development Workflow (Mandatory)

### CRITICAL: Deployment Process
1. **ALWAYS** delete the old integration completely: `sudo rm -rf /config/custom_components/blupow`
2. **ALWAYS** copy fresh files: `sudo cp -r . /config/custom_components/blupow/`
3. **ALWAYS** restart Home Assistant completely (not just UI restart)
4. **NEVER** rely on file edits - always replace entire files

### Error Resolution Protocol:
1. **Import Errors**: Check Home Assistant version compatibility first
2. **NoneType Errors**: Ensure coordinator data is available before sensor creation
3. **Persistent Errors**: Complete deletion and redeployment required

## 3. Core Rules & Precautions

**RULE: COMPLETE FILE REPLACEMENT**
- Never edit existing files in-place
- Always replace entire files with corrected versions
- Use `sudo` for deployment commands

**RULE: VERSION COMPATIBILITY**
- Check Home Assistant version before using new APIs
- Use fallback methods for version-specific functions
- Test with minimal, compatible code first

**RULE: COORDINATOR TIMING**
- Always call `await coordinator.async_config_entry_first_refresh()` before sensor setup
- Make sensor initialization resilient to missing data
- Use proper error handling for None values

## 4. Environment Notes

### Operating System: Ubuntu 24.04
### Home Assistant Installation: Docker Compose
### Key docker-compose.yaml settings:
```yaml
services:
  homeassistant:
    network_mode: host
    group_add:
      - '107'  # The GID of the 'bluetooth' group on the host
    volumes:
      - /home/madgoat/opt/homeassistant/config:/config
      - /run/dbus:/run/dbus:ro
```

## 5. Current Blocking Issues

### Issue 1: Import Compatibility
- **Problem**: `async_get_connectable_bleak_client` doesn't exist
- **Solution**: Use standard `BleakClient` with proper error handling
- **Status**: Partially resolved, needs testing

### Issue 2: Coordinator Data Timing
- **Problem**: Sensors try to access `coordinator.data` before it's populated
- **Solution**: Add `async_config_entry_first_refresh()` and resilient sensor initialization
- **Status**: Partially resolved, needs testing

### Issue 3: Deployment Reliability
- **Problem**: Code changes not consistently applied
- **Solution**: Complete deletion and redeployment process
- **Status**: Process established, needs validation

## 6. Next Steps
1. Implement minimal, working version with standard BleakClient
2. Add proper coordinator timing
3. Test deployment process
4. Gradually add features once basic functionality works

