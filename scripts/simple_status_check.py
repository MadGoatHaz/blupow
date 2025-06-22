#!/usr/bin/env python3
"""
Simple BluPow Status Check
Provides a status report without requiring Home Assistant imports
"""
import subprocess
import json
import requests
from datetime import datetime

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

def check_docker_status():
    """Check Docker container status"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=homeassistant', '--format', '{{.Status}}'], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Unknown"

def get_ha_logs():
    """Get recent Home Assistant logs related to BluPow"""
    try:
        result = subprocess.run([
            'docker', 'logs', 'homeassistant', '--since', '5m'
        ], capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        blupow_lines = [line for line in lines if 'blupow' in line.lower() or 'BluPow' in line]
        
        return blupow_lines[-15:]  # Last 15 relevant lines
    except:
        return ["Unable to retrieve logs"]

def analyze_logs(logs):
    """Analyze logs for key information"""
    errors = [line for line in logs if "ERROR" in line]
    warnings = [line for line in logs if "WARNING" in line]
    successes = [line for line in logs if "✅" in line or "successfully" in line.lower()]
    connections = [line for line in logs if "connect" in line.lower()]
    
    return {
        "total_lines": len(logs),
        "errors": len(errors),
        "warnings": len(warnings),
        "successes": len(successes),
        "connections": len(connections),
        "recent_errors": errors[-3:] if errors else [],
        "recent_successes": successes[-3:] if successes else []
    }

def main():
    """Main status check function"""
    print_header("BluPow Integration Status Check")
    print(f"🕐 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check Home Assistant status
    print_section("Home Assistant Status")
    ha_status = get_ha_status()
    docker_status = check_docker_status()
    
    print(f"🏠 Home Assistant API: {'✅ Running' if ha_status else '❌ Not accessible'}")
    print(f"🐳 Docker Container: {docker_status}")
    
    # 2. Check Home Assistant logs
    print_section("Recent Home Assistant Logs Analysis")
    logs = get_ha_logs()
    analysis = analyze_logs(logs)
    
    print(f"📝 Total BluPow log entries: {analysis['total_lines']}")
    print(f"❌ Errors: {analysis['errors']}")
    print(f"⚠️  Warnings: {analysis['warnings']}")
    print(f"✅ Successes: {analysis['successes']}")
    print(f"🔌 Connection attempts: {analysis['connections']}")
    
    # 3. Show recent important logs
    print_section("Recent Important Log Entries")
    
    if analysis['recent_errors']:
        print("❌ Recent Errors:")
        for error in analysis['recent_errors']:
            print(f"   {error}")
    
    if analysis['recent_successes']:
        print("✅ Recent Successes:")
        for success in analysis['recent_successes']:
            print(f"   {success}")
    
    # Show last few log entries
    print("\n📋 Last 10 BluPow Log Entries:")
    for log_line in logs[-10:]:
        if "ERROR" in log_line:
            print(f"❌ {log_line}")
        elif "WARNING" in log_line:
            print(f"⚠️  {log_line}")
        elif "INFO" in log_line or "✅" in log_line:
            print(f"ℹ️  {log_line}")
        else:
            print(f"📝 {log_line}")
    
    # 4. Integration status assessment
    print_section("Integration Status Assessment")
    
    if ha_status:
        if analysis['errors'] == 0 and analysis['successes'] > 0:
            print("🎉 EXCELLENT: Home Assistant running, integration appears successful!")
            status = "excellent"
        elif analysis['errors'] > 0 and analysis['successes'] > 0:
            print("⚠️  GOOD: Home Assistant running, some issues but also successes")
            status = "good"
        elif analysis['errors'] > analysis['successes']:
            print("❌ ISSUES: Home Assistant running but integration has problems")
            status = "issues"
        else:
            print("🔄 STARTING: Home Assistant running, integration may still be initializing")
            status = "starting"
    else:
        print("❌ CRITICAL: Home Assistant not accessible")
        status = "critical"
    
    # 5. Recommendations
    print_section("Recommendations")
    
    if status == "excellent":
        print("1. ✅ Check Home Assistant UI for BluPow sensors")
        print("2. ✅ Sensors should show real values every 2 minutes")
        print("3. ✅ Monitor for consistent updates")
    elif status == "good":
        print("1. 🔍 Monitor logs for recurring errors")
        print("2. ⏱️  Wait 2-5 minutes for next update cycle")
        print("3. 🔄 Consider restarting integration if issues persist")
    elif status == "issues":
        print("1. 🔧 Check recent error messages above")
        print("2. 🔄 Restart Home Assistant if needed")
        print("3. 📱 Verify BluPow device is powered and nearby")
    elif status == "starting":
        print("1. ⏱️  Wait 2-5 minutes for initialization")
        print("2. 🔄 Check status again after waiting")
        print("3. 📋 Monitor logs for progress")
    else:
        print("1. 🔧 Restart Home Assistant container")
        print("2. 🔍 Check Docker container status")
        print("3. 📋 Check system logs for issues")
    
    print_header("Status Check Complete")
    
    # Create summary report
    summary = {
        "timestamp": datetime.now().isoformat(),
        "home_assistant_status": ha_status,
        "docker_status": docker_status,
        "log_analysis": analysis,
        "overall_status": status
    }
    
    # Save report
    try:
        with open("results/status_check_report.json", "w") as f:
            json.dump(summary, f, indent=2)
        print(f"📄 Report saved to: results/status_check_report.json")
    except:
        print("📄 Could not save report file")
    
    return summary

if __name__ == "__main__":
    main() 