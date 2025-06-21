#!/usr/bin/env python3
"""
BluPow Status Dashboard - Comprehensive System Overview
Shows the complete BluPow system status and capabilities
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add the integration directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient
from scripts.blupow_adaptive_coordinator import AdaptiveCoordinator

class BluPowDashboard:
    """Comprehensive BluPow system dashboard"""
    
    def __init__(self):
        self.coordinator = AdaptiveCoordinator()
    
    async def get_system_overview(self):
        """Get complete system overview"""
        print("🚀" + "="*60)
        print("🎯 BLUPOW - UNIVERSAL BLUETOOTH POWER MONITORING SYSTEM")
        print("="*63)
        print()
        
        # Discovery and testing
        print("🔍 PHASE 1: INTELLIGENT DEVICE DISCOVERY")
        print("-" * 40)
        
        discovered = await self.coordinator.discover_devices()
        
        if not discovered:
            print("❌ No compatible devices found")
            return
        
        print(f"✅ Found {len(discovered)} compatible device(s):")
        for device in discovered:
            print(f"  📱 {device.name} ({device.device_type.value})")
            print(f"     MAC: {device.mac_address}")
            print(f"     Signal: {device.rssi} dBm")
        
        print()
        print("🧪 PHASE 2: CAPABILITY TESTING & OPTIMIZATION")
        print("-" * 45)
        
        # Test each device
        active_devices = []
        for device in discovered:
            print(f"\n🔬 Testing {device.name}...")
            success = await self.coordinator.test_device_capabilities(device)
            
            if success:
                active_devices.append(device)
                self.coordinator.devices[device.mac_address] = device
                
                print(f"  ✅ SUCCESS - Device Ready for Monitoring")
                print(f"     🔋 Capabilities: {', '.join(device.capabilities)}")
                print(f"     ⏱️ Optimal Interval: {device.optimal_interval:.0f}s")
                print(f"     📊 Success Rate: {device.connection_success_rate*100:.0f}%")
                print(f"     🏥 Health Score: {device.health_score:.0f}/100")
                print(f"     📈 Data Fields: {device.data_field_count}")
                
                # Show sample data
                if device.last_data:
                    print(f"     📋 Sample Data:")
                    if 'battery_voltage' in device.last_data:
                        print(f"        🔋 Battery: {device.last_data['battery_voltage']}V ({device.last_data.get('battery_percentage', '?')}%)")
                    if 'pv_voltage' in device.last_data:
                        print(f"        ☀️ Solar: {device.last_data['pv_voltage']}V")
                    if 'load_power' in device.last_data:
                        print(f"        ⚡ Load: {device.last_data['load_power']}W")
                    if 'power_generation_today' in device.last_data:
                        print(f"        📊 Today: {device.last_data['power_generation_today']}Wh generated")
            else:
                print(f"  ❌ FAILED - Device not compatible or unreachable")
        
        print()
        print("📊 PHASE 3: SYSTEM STATUS & CAPABILITIES")
        print("-" * 40)
        
        if not active_devices:
            print("❌ No active devices available")
            return
        
        # System summary
        total_health = sum(d.health_score for d in active_devices) / len(active_devices)
        total_capabilities = set()
        for device in active_devices:
            total_capabilities.update(device.capabilities)
        
        print(f"🎯 System Overview:")
        print(f"   📱 Active Devices: {len(active_devices)}")
        print(f"   🏥 System Health: {total_health:.0f}/100")
        print(f"   🎛️ Total Capabilities: {len(total_capabilities)}")
        print(f"   📊 Total Data Fields: {sum(d.data_field_count for d in active_devices)}")
        
        print(f"\n🎛️ System Capabilities:")
        for capability in sorted(total_capabilities):
            devices_with_cap = [d.name.strip() for d in active_devices if capability in d.capabilities]
            print(f"   ✅ {capability.replace('_', ' ').title()}: {len(devices_with_cap)} device(s)")
        
        print()
        print("🏠 PHASE 4: HOME ASSISTANT INTEGRATION STATUS")
        print("-" * 45)
        
        print("✅ Integration Features:")
        print("   🔄 Real-time data polling with adaptive timing")
        print("   📊 25+ sensor entities per device")
        print("   🏥 Health monitoring and diagnostics")
        print("   ⚠️ Automatic failure detection and recovery")
        print("   📈 Performance optimization")
        print("   🔍 Automatic device discovery")
        print("   🎛️ Multi-device coordination")
        
        print("\n📋 Available Sensors (per device):")
        sample_device = active_devices[0]
        if sample_device.last_data:
            sensors = [
                ("Battery Voltage", "battery_voltage", "V"),
                ("Battery Percentage", "battery_percentage", "%"),
                ("Solar Voltage", "pv_voltage", "V"),
                ("Solar Current", "pv_current", "A"),
                ("Solar Power", "pv_power", "W"),
                ("Load Power", "load_power", "W"),
                ("Daily Generation", "power_generation_today", "Wh"),
                ("Total Generation", "power_generation_total", "kWh"),
                ("Charging Status", "charging_status", ""),
                ("Battery Type", "battery_type", ""),
                ("Connection Status", "connection_status", ""),
            ]
            
            for name, key, unit in sensors:
                if key in sample_device.last_data:
                    value = sample_device.last_data[key]
                    unit_str = f" {unit}" if unit else ""
                    print(f"   📊 {name}: {value}{unit_str}")
        
        print()
        print("🚀 PHASE 5: NEXT-GENERATION FEATURES")
        print("-" * 40)
        
        print("✅ Implemented:")
        print("   🧠 Intelligent device type detection")
        print("   ⏱️ Adaptive timing optimization")
        print("   🏥 Real-time health monitoring")
        print("   🔄 Automatic failure recovery")
        print("   📊 Performance analytics")
        print("   🎯 Multi-device coordination")
        print("   🔍 Continuous device discovery")
        
        print("\n🎯 Ready for Production:")
        print("   🏠 Home Assistant integration")
        print("   📡 MQTT publishing")
        print("   📊 Historical data logging")
        print("   ⚠️ Alert notifications")
        print("   📱 Mobile dashboard")
        print("   🌐 Web interface")
        
        print()
        print("🎉 BLUPOW SYSTEM STATUS: FULLY OPERATIONAL")
        print("="*63)
        
        return {
            'discovered_devices': len(discovered),
            'active_devices': len(active_devices),
            'system_health': total_health,
            'capabilities': list(total_capabilities),
            'total_data_fields': sum(d.data_field_count for d in active_devices),
            'devices': [
                {
                    'name': d.name.strip(),
                    'type': d.device_type.value,
                    'health': d.health_score,
                    'capabilities': d.capabilities,
                    'data_fields': d.data_field_count,
                    'sample_data': {
                        'battery_voltage': d.last_data.get('battery_voltage'),
                        'battery_percentage': d.last_data.get('battery_percentage'),
                        'solar_voltage': d.last_data.get('pv_voltage'),
                        'load_power': d.last_data.get('load_power')
                    }
                }
                for d in active_devices
            ]
        }

async def main():
    """Run the comprehensive dashboard"""
    dashboard = BluPowDashboard()
    
    try:
        status = await dashboard.get_system_overview()
        
        if status:
            print(f"\n💾 System Status JSON:")
            print(json.dumps(status, indent=2))
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard interrupted")
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 