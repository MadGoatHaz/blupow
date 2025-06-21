#!/usr/bin/env python3
"""
MULTI-DEVICE INVESTIGATION
Investigates why both BluPow devices show identical data
Fixes device identification and data mapping issues
"""

import json
import subprocess
from datetime import datetime

def analyze_device_logs():
    """Analyze logs for both devices"""
    
    print("🔍 MULTI-DEVICE INVESTIGATION")
    print("=" * 60)
    
    devices = {
        "C4:D3:6A:66:7E:D4": {
            "name": "NEW Renogy Device",
            "status": "UNKNOWN",
            "connection_success": 0,
            "connection_failures": 0,
            "using_real_data": False,
            "device_name": "Unknown"
        },
        "D8:B6:73:BF:4F:75": {
            "name": "ORIGINAL Device", 
            "status": "UNKNOWN",
            "connection_success": 0,
            "connection_failures": 0,
            "using_real_data": False,
            "device_name": "Unknown"
        }
    }
    
    try:
        # Get recent logs
        result = subprocess.run(['docker', 'logs', 'homeassistant', '--since', '10m'], 
                              capture_output=True, text=True)
        logs = result.stdout + result.stderr
        
        # Analyze each device
        for mac_address, device_info in devices.items():
            print(f"\\n📱 ANALYZING DEVICE: {mac_address}")
            print(f"   Name: {device_info['name']}")
            
            # Count connections and failures
            connection_attempts = logs.count(f"Connecting to device: {mac_address}")
            connection_successes = logs.count(f"Connection successful") if mac_address in logs else 0
            connection_failures = logs.count(f"Connection failed") if mac_address in logs else 0
            real_data_retrievals = logs.count(f"Real device data retrieved") if mac_address in logs else 0
            fallback_data_uses = logs.count(f"fallback data system") if mac_address in logs else 0
            
            # Find device name
            device_name_line = ""
            for line in logs.split('\\n'):
                if f"Found BLE device:" in line and mac_address in logs:
                    # Look for the device name in nearby lines
                    lines = logs.split('\\n')
                    for i, log_line in enumerate(lines):
                        if mac_address in log_line and "Found BLE device:" in log_line:
                            device_name_line = log_line
                            break
            
            if "BT-TH-6A667ED4" in device_name_line:
                device_info["device_name"] = "BT-TH-6A667ED4"
            elif "BTRIC134000035" in device_name_line:
                device_info["device_name"] = "BTRIC134000035"
            
            # Update device info
            device_info["connection_attempts"] = connection_attempts
            device_info["connection_success"] = connection_successes
            device_info["connection_failures"] = connection_failures
            device_info["real_data_retrievals"] = real_data_retrievals
            device_info["fallback_data_uses"] = fallback_data_uses
            device_info["using_real_data"] = real_data_retrievals > 0
            
            # Determine status
            if connection_successes > 0:
                device_info["status"] = "WORKING" 
            elif connection_attempts > 0:
                device_info["status"] = "FAILING"
            else:
                device_info["status"] = "NOT_FOUND"
            
            print(f"   Status: {device_info['status']}")
            print(f"   Device Name: {device_info['device_name']}")
            print(f"   Connection Attempts: {connection_attempts}")
            print(f"   Successful Connections: {connection_successes}")
            print(f"   Failed Connections: {connection_failures}")
            print(f"   Real Data Retrievals: {real_data_retrievals}")
            print(f"   Fallback Data Uses: {fallback_data_uses}")
            print(f"   Using Real Data: {'✅ YES' if device_info['using_real_data'] else '❌ NO'}")
    
    except Exception as e:
        print(f"❌ Error analyzing logs: {e}")
    
    return devices

def identify_issues(devices):
    """Identify specific issues with multi-device setup"""
    
    print("\\n🔍 ISSUE IDENTIFICATION")
    print("=" * 60)
    
    issues = []
    
    # Check for identical data issue
    working_devices = [mac for mac, info in devices.items() if info["status"] == "WORKING"]
    failing_devices = [mac for mac, info in devices.items() if info["status"] == "FAILING"]
    
    if len(working_devices) >= 1 and len(failing_devices) >= 1:
        issues.append({
            "type": "IDENTICAL_DATA",
            "description": "Working device uses real data, failing device uses fallback data with same values",
            "severity": "HIGH",
            "devices_affected": working_devices + failing_devices
        })
    
    # Check for device identification issues
    device_names = [info["device_name"] for info in devices.values()]
    if "BTRIC134000035" in device_names and "BT-TH-6A667ED4" in device_names:
        issues.append({
            "type": "DEVICE_IDENTIFICATION", 
            "description": "Both devices use same hardcoded device_id 'BTRIC134000035'",
            "severity": "HIGH",
            "devices_affected": list(devices.keys())
        })
    
    # Check for connection issues
    for mac, info in devices.items():
        if info["connection_failures"] > info["connection_success"] and info["connection_attempts"] > 0:
            issues.append({
                "type": "CONNECTION_FAILURE",
                "description": f"Device {mac} consistently failing to connect",
                "severity": "MEDIUM",
                "devices_affected": [mac]
            })
    
    print(f"🚨 IDENTIFIED {len(issues)} ISSUES:")
    for i, issue in enumerate(issues, 1):
        print(f"\\n{i}. {issue['type']} ({issue['severity']} SEVERITY)")
        print(f"   Description: {issue['description']}")
        print(f"   Affected Devices: {', '.join(issue['devices_affected'])}")
    
    return issues

def create_fix_plan(devices, issues):
    """Create a comprehensive fix plan"""
    
    print("\\n🔧 CREATING FIX PLAN")
    print("=" * 60)
    
    fix_actions = []
    
    # Fix 1: Update client to use unique device identification
    fix_actions.append({
        "action": "UPDATE_DEVICE_IDENTIFICATION",
        "description": "Modify blupow_client.py to use MAC address as device_id instead of hardcoded value",
        "priority": 1,
        "files_to_modify": ["blupow_client.py"],
        "changes": [
            "Replace hardcoded device_id 'BTRIC134000035' with actual MAC address",
            "Ensure each device has unique identifiers",
            "Add device-specific data mapping"
        ]
    })
    
    # Fix 2: Improve device data differentiation
    fix_actions.append({
        "action": "DIFFERENTIATE_DEVICE_DATA",
        "description": "Ensure each device provides unique sensor data",
        "priority": 2,
        "files_to_modify": ["blupow_client.py", "coordinator.py"],
        "changes": [
            "Add device-specific data variations",
            "Include MAC address in all sensor unique IDs",
            "Prevent data collision between devices"
        ]
    })
    
    # Fix 3: Remove or fix non-working device
    failing_devices = [mac for mac, info in devices.items() if info["status"] == "FAILING"]
    if failing_devices:
        fix_actions.append({
            "action": "FIX_FAILING_DEVICE",
            "description": f"Address connection issues with {failing_devices[0]}",
            "priority": 3,
            "files_to_modify": ["coordinator.py"],
            "changes": [
                "Investigate why device cannot connect",
                "Improve connection retry logic",
                "Add device-specific connection parameters"
            ]
        })
    
    print("📋 FIX PLAN:")
    for i, action in enumerate(fix_actions, 1):
        print(f"\\n{i}. {action['action']} (Priority {action['priority']})")
        print(f"   Description: {action['description']}")
        print(f"   Files to modify: {', '.join(action['files_to_modify'])}")
        print(f"   Changes:")
        for change in action['changes']:
            print(f"     - {change}")
    
    return fix_actions

def save_investigation_report(devices, issues, fix_actions):
    """Save comprehensive investigation report"""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "investigation_type": "Multi-Device Analysis",
        "devices_found": len(devices),
        "devices": devices,
        "issues_identified": len(issues),
        "issues": issues,
        "fix_actions": len(fix_actions),
        "fix_plan": fix_actions,
        "summary": {
            "working_devices": len([d for d in devices.values() if d["status"] == "WORKING"]),
            "failing_devices": len([d for d in devices.values() if d["status"] == "FAILING"]),
            "using_real_data": len([d for d in devices.values() if d["using_real_data"]]),
            "using_fallback_data": len([d for d in devices.values() if not d["using_real_data"]])
        },
        "next_steps": [
            "Implement device identification fixes",
            "Test each device individually", 
            "Verify unique data from each device",
            "Monitor for data collision issues"
        ]
    }
    
    with open("results/reports/multi_device_investigation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\\n📊 INVESTIGATION SUMMARY:")
    print("=" * 60)
    print(f"✅ Devices Found: {report['devices_found']}")
    print(f"✅ Working Devices: {report['summary']['working_devices']}")
    print(f"❌ Failing Devices: {report['summary']['failing_devices']}")
    print(f"📊 Using Real Data: {report['summary']['using_real_data']}")
    print(f"⚠️ Using Fallback Data: {report['summary']['using_fallback_data']}")
    print(f"🚨 Issues Identified: {report['issues_identified']}")
    print(f"🔧 Fix Actions Planned: {report['fix_actions']}")
    
    print("\\n📝 Report saved: results/reports/multi_device_investigation_report.json")
    
    return report

if __name__ == "__main__":
    print("🔍 MULTI-DEVICE INVESTIGATION STARTING")
    print("=" * 60)
    print("Goal: Understand why both devices show identical data")
    print()
    
    # Run investigation
    devices = analyze_device_logs()
    issues = identify_issues(devices)
    fix_actions = create_fix_plan(devices, issues)
    report = save_investigation_report(devices, issues, fix_actions)
    
    print("\\n🎯 INVESTIGATION COMPLETE!")
    print("=" * 60)
    print("Next: Implement the fix plan to resolve device data issues") 