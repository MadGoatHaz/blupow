#!/usr/bin/env python3
"""
Final BluPow Connection Test
This script provides a comprehensive status report of the BluPow integration
"""
import asyncio
import sys
import json
import requests
from datetime import datetime
import subprocess
import time

# Add the project directory to the path
sys.path.insert(0, '/home/madgoat/opt/Projects/blupow')

from custom_components.blupow.blupow_client import BluPowClient

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n📊 {title}")
    print("-" * 40)

def get_ha_status():
    """Check Home Assistant status"""
    try:
        response = requests.get("http://localhost:8123/api/", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_ha_sensor_data():
    """Get BluPow sensor data from Home Assistant"""
    try:
        # Try to get sensor states (this would require authentication in real setup)
        return {"status": "Home Assistant API requires authentication"}
    except Exception as e:
        return {"error": str(e)}

def check_docker_status():
    """Check Docker container status"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=homeassistant', '--format', '{{.Status}}'], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Unknown"

async def test_direct_connection():
    """Test direct connection to BluPow device"""
    device_mac = "D8:B6:73:BF:4F:75"
    
    try:
        print(f"🔌 Attempting direct connection to {device_mac}...")
        client = BluPowClient(device_mac)
        
        # Test connection
        connected = await client.connect()
        if not connected:
            return {"success": False, "error": "Failed to connect"}
        
        print("✅ Connected successfully!")
        
        # Test data reading
        print("📡 Reading device data...")
        data = await client.read_device_info()
        
        await client.disconnect()
        
        return {
            "success": True,
            "data_fields": len(data),
            "sample_data": {k: v for k, v in list(data.items())[:5]},
            "connection_status": data.get("connection_status", "unknown")
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_ha_logs():
    """Get recent Home Assistant logs related to BluPow"""
    try:
        result = subprocess.run([
            'docker', 'logs', 'homeassistant', '--since', '10m'
        ], capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        blupow_lines = [line for line in lines if 'blupow' in line.lower() or 'BluPow' in line]
        
        return blupow_lines[-10:]  # Last 10 relevant lines
    except:
        return ["Unable to retrieve logs"]

async def main():
    """Main test function"""
    print_header("BluPow Integration Final Status Report")
    print(f"🕐 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check Home Assistant status
    print_section("Home Assistant Status")
    ha_status = get_ha_status()
    docker_status = check_docker_status()
    
    print(f"🏠 Home Assistant API: {'✅ Running' if ha_status else '❌ Not accessible'}")
    print(f"🐳 Docker Container: {docker_status}")
    
    # 2. Check direct device connection
    print_section("Direct Device Connection Test")
    connection_result = await test_direct_connection()
    
    if connection_result["success"]:
        print(f"✅ Direct connection: SUCCESS")
        print(f"📊 Data fields retrieved: {connection_result['data_fields']}")
        print(f"🔗 Connection status: {connection_result['connection_status']}")
        print(f"📝 Sample data: {json.dumps(connection_result['sample_data'], indent=2)}")
    else:
        print(f"❌ Direct connection: FAILED")
        print(f"💥 Error: {connection_result['error']}")
    
    # 3. Check Home Assistant logs
    print_section("Recent Home Assistant Logs")
    logs = get_ha_logs()
    
    if logs:
        for log_line in logs:
            if "ERROR" in log_line:
                print(f"❌ {log_line}")
            elif "WARNING" in log_line:
                print(f"⚠️  {log_line}")
            elif "INFO" in log_line:
                print(f"ℹ️  {log_line}")
            else:
                print(f"📝 {log_line}")
    else:
        print("📭 No recent BluPow logs found")
    
    # 4. Integration status summary
    print_section("Integration Status Summary")
    
    if ha_status and connection_result["success"]:
        print("🎉 EXCELLENT: Both Home Assistant and direct connection working!")
        print("💡 The integration should be functioning properly.")
        print("🔄 Sensors may take up to 2 minutes to update due to new timing settings.")
    elif ha_status:
        print("⚠️  PARTIAL: Home Assistant running but device connection issues")
        print("🔧 Check Bluetooth conflicts and device availability")
    elif connection_result["success"]:
        print("⚠️  PARTIAL: Device accessible but Home Assistant issues")
        print("🔧 Check Home Assistant configuration and restart if needed")
    else:
        print("❌ ISSUES: Both Home Assistant and device connection problems")
        print("🔧 Check device power, Bluetooth, and Home Assistant status")
    
    # 5. Next steps
    print_section("Recommended Next Steps")
    
    if ha_status and connection_result["success"]:
        print("1. ✅ Check Home Assistant UI for BluPow sensors")
        print("2. ✅ Wait 2-5 minutes for first data update")
        print("3. ✅ Verify sensors show real values (not 'Unavailable')")
        print("4. ✅ Monitor for consistent updates every 2 minutes")
    else:
        print("1. 🔧 Restart Home Assistant if needed")
        print("2. 🔧 Check device power and Bluetooth connectivity")
        print("3. 🔧 Verify no other Bluetooth tools are connecting to device")
        print("4. 🔧 Check Home Assistant logs for specific errors")
    
    print_header("Test Complete")
    
    # Create summary report
    summary = {
        "timestamp": datetime.now().isoformat(),
        "home_assistant_status": ha_status,
        "docker_status": docker_status,
        "direct_connection": connection_result,
        "recent_logs_count": len(logs),
        "overall_status": "success" if (ha_status and connection_result["success"]) else "partial" if (ha_status or connection_result["success"]) else "failed"
    }
    
    # Save report
    with open("results/final_integration_status.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Detailed report saved to: results/final_integration_status.json")
    
    return summary

if __name__ == "__main__":
    asyncio.run(main()) 