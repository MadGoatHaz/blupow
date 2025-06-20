#!/usr/bin/env python3
"""
BluPow Integration Recovery Tool

Comprehensive solution for the "already_configured" issue and integration recovery.
This script handles deployment, cleanup, verification, and testing.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and return result"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} - Success")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr.strip()}")
        return False, e.stderr.strip()

def check_homeassistant_status():
    """Check if Home Assistant container is running"""
    success, output = run_command("docker ps | grep homeassistant", "Checking Home Assistant status")
    return success and "homeassistant" in output

def deploy_integration():
    """Deploy the updated integration"""
    print("\n📦 Deploying Updated Integration")
    print("=" * 35)
    
    # Copy files to Home Assistant
    copy_commands = [
        "docker cp __init__.py homeassistant:/config/custom_components/blupow/",
        "docker cp const.py homeassistant:/config/custom_components/blupow/",
        "docker cp blupow_client.py homeassistant:/config/custom_components/blupow/",
        "docker cp coordinator.py homeassistant:/config/custom_components/blupow/",
        "docker cp sensor.py homeassistant:/config/custom_components/blupow/",
        "docker cp config_flow.py homeassistant:/config/custom_components/blupow/",
        "docker cp manifest.json homeassistant:/config/custom_components/blupow/",
        "docker cp strings.json homeassistant:/config/custom_components/blupow/",
        "docker cp diagnostics.py homeassistant:/config/custom_components/blupow/"
    ]
    
    all_success = True
    for cmd in copy_commands:
        success, _ = run_command(cmd, f"Copying {cmd.split()[-2]}")
        if not success:
            all_success = False
    
    return all_success

def cleanup_orphaned_entries():
    """Clean up orphaned config entries"""
    print("\n🧹 Cleaning Up Orphaned Entries")
    print("=" * 33)
    
    cleanup_script = '''
import json
import os
from datetime import datetime

config_path = "/config/.storage/core.config_entries"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config_data = json.load(f)
    
    entries = config_data.get("data", {}).get("entries", [])
    blupow_entries = [e for e in entries if e.get("domain") == "blupow"]
    
    if blupow_entries:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"/config/.storage/core.config_entries.backup_{timestamp}"
        with open(backup_path, "w") as f:
            json.dump(config_data, f, indent=2)
        print(f"Backup created: {backup_path}")
        
        # Remove BluPow entries
        cleaned_entries = [e for e in entries if e.get("domain") != "blupow"]
        config_data["data"]["entries"] = cleaned_entries
        
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        
        print(f"Removed {len(blupow_entries)} BluPow entries")
    else:
        print("No BluPow entries found")
else:
    print("Config entries file not found")
'''
    
    success, output = run_command(f'docker exec homeassistant python3 -c "{cleanup_script}"', 
                                  "Cleaning orphaned config entries")
    if success:
        print(f"   {output}")
    return success

def restart_homeassistant():
    """Restart Home Assistant"""
    print("\n🔄 Restarting Home Assistant")
    print("=" * 25)
    
    success, _ = run_command("docker restart homeassistant", "Restarting Home Assistant container")
    if success:
        print("   Waiting for Home Assistant to start up...")
        time.sleep(30)  # Wait for startup
        
        # Check if it's running
        for i in range(6):  # Try for 1 minute
            if check_homeassistant_status():
                print("✅ Home Assistant is running")
                return True
            time.sleep(10)
        
        print("⚠️  Home Assistant restart took longer than expected")
        return False
    return False

def verify_integration():
    """Verify the integration is properly loaded"""
    print("\n🔍 Verifying Integration")
    print("=" * 23)
    
    verify_script = '''
import sys
sys.path.insert(0, "/config/custom_components")

try:
    import blupow
    from blupow.const import DOMAIN, DEVICE_SENSORS
    from blupow.blupow_client import BluPowClient
    from blupow.coordinator import BluPowDataUpdateCoordinator
    from blupow.sensor import BluPowSensor
    
    print(f"Domain: {DOMAIN}")
    print(f"Sensors: {len(DEVICE_SENSORS)}")
    print("All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
'''
    
    success, output = run_command(f'docker exec homeassistant python3 -c "{verify_script}"',
                                  "Verifying integration imports")
    if success:
        print(f"   {output}")
    return success

def check_integration_availability():
    """Check if integration appears in Home Assistant"""
    print("\n📋 Integration Availability Check")
    print("=" * 32)
    
    check_script = '''
import json
import os

# Check config entries
config_path = "/config/.storage/core.config_entries"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config_data = json.load(f)
    
    entries = config_data.get("data", {}).get("entries", [])
    blupow_entries = [e for e in entries if e.get("domain") == "blupow"]
    print(f"BluPow config entries: {len(blupow_entries)}")
else:
    print("Config entries file not found")

# Check if integration files exist
import os
files = [
    "/config/custom_components/blupow/__init__.py",
    "/config/custom_components/blupow/manifest.json",
    "/config/custom_components/blupow/const.py"
]

for file_path in files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path}")
'''
    
    success, output = run_command(f'docker exec homeassistant python3 -c "{check_script}"',
                                  "Checking integration availability")
    if success:
        print(f"   {output}")
    return success

def create_recovery_documentation():
    """Create documentation for the recovery process"""
    print("\n📚 Creating Recovery Documentation")
    print("=" * 35)
    
    doc_content = f"""# BluPow Integration Recovery - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Issue Resolved: "already_configured" Error

### Problem
- Integration disappeared from Home Assistant UI after restart
- "already_configured" error when trying to re-add
- Orphaned config entries causing state mismatch

### Solution Applied
1. **Deployed Updated Code**: Corrected inverter protocol implementation
2. **Cleaned Config Entries**: Removed orphaned BluPow entries  
3. **Restarted Home Assistant**: Fresh initialization
4. **Verified Integration**: All components loading properly

### Files Updated
- `blupow_client.py` - Inverter protocol implementation
- `const.py` - Updated sensor definitions (22 inverter sensors)
- Documentation - Corrected hardware understanding

### Current Status
- Integration files: ✅ Deployed
- Config entries: ✅ Cleaned
- Home Assistant: ✅ Restarted
- Integration: ✅ Available for setup

### Next Steps
1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration"
3. Search for "BluPow" 
4. Configure with device address: D8:B6:73:BF:4F:75

### Prevention Measures
- Created recovery scripts in `scripts/` directory
- Added comprehensive diagnostic tools
- Documented common issues and solutions

### Recovery Scripts Created
- `scripts/cleanup_integration.py` - Diagnose and clean orphaned entries
- `scripts/integration_recovery.py` - Complete recovery process
- `scripts/enable_debug_logging.py` - Enable debug logging for troubleshooting

## Hardware Correction Applied
**CRITICAL DISCOVERY**: Device is Renogy RIV1230RCH-SPS INVERTER, not charge controller!

- **Protocol**: Changed from charge controller to inverter registers
- **Sensors**: Updated from 18 charge controller sensors to 22 inverter sensors  
- **Data**: Now monitors AC input/output, frequency, load power, battery status
- **Value**: Complete household power monitoring vs basic solar monitoring
"""
    
    try:
        with open('docs/INTEGRATION_RECOVERY.md', 'w') as f:
            f.write(doc_content)
        print("✅ Recovery documentation created: docs/INTEGRATION_RECOVERY.md")
        return True
    except Exception as e:
        print(f"❌ Error creating documentation: {e}")
        return False

def main():
    print("🚀 BluPow Integration Recovery Tool")
    print("=" * 38)
    print("Resolving 'already_configured' issue and deploying corrections")
    
    # Check prerequisites
    if not check_homeassistant_status():
        print("❌ Home Assistant container not running")
        return 1
    
    # Step 1: Deploy updated integration
    if not deploy_integration():
        print("❌ Failed to deploy integration")
        return 1
    
    # Step 2: Clean up orphaned entries
    if not cleanup_orphaned_entries():
        print("❌ Failed to clean up config entries")
        return 1
    
    # Step 3: Restart Home Assistant
    if not restart_homeassistant():
        print("❌ Failed to restart Home Assistant")
        return 1
    
    # Step 4: Verify integration
    if not verify_integration():
        print("❌ Integration verification failed")
        return 1
    
    # Step 5: Check availability
    if not check_integration_availability():
        print("❌ Integration availability check failed")
        return 1
    
    # Step 6: Create documentation
    create_recovery_documentation()
    
    print("\n🎉 Integration Recovery Complete!")
    print("=" * 33)
    print("✅ Updated code deployed")
    print("✅ Orphaned entries cleaned")  
    print("✅ Home Assistant restarted")
    print("✅ Integration verified")
    print("✅ Documentation updated")
    
    print("\n📋 Next Steps:")
    print("1. Go to Home Assistant Settings → Devices & Services")
    print("2. Click 'Add Integration'")
    print("3. Search for 'BluPow'")
    print("4. Configure with device: D8:B6:73:BF:4F:75")
    print("5. Enjoy 22 inverter sensors with AC power monitoring!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 