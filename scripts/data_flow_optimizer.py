#!/usr/bin/env python3
"""
🎯 DATA FLOW OPTIMIZER
Enhance the 25-field data stream for optimal Home Assistant presentation

The BT-TH device is providing rich data - let's make it shine in HA!
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blupow_client import BluPowClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFlowOptimizer:
    """Optimize the data flow for Home Assistant presentation"""
    
    def __init__(self):
        self.mac_address = "C4:D3:6A:66:7E:D4"  # Working BT-TH device
        self.optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'device_mac': self.mac_address,
            'data_analysis': {},
            'sensor_mapping': {},
            'ha_optimization': {}
        }
    
    def analyze_data_quality(self, data: dict) -> dict:
        """Analyze the quality and meaning of sensor data"""
        analysis = {
            'total_fields': len(data),
            'meaningful_sensors': 0,
            'data_types': {},
            'sensor_categories': {}
        }
        
        # Categorize the data fields
        power_sensors = []
        environmental_sensors = []
        status_sensors = []
        battery_sensors = []
        
        for key, value in data.items():
            if key.startswith('_'):
                continue
                
            analysis['meaningful_sensors'] += 1
            
            # Categorize by key name patterns
            key_lower = key.lower()
            if any(term in key_lower for term in ['voltage', 'current', 'power', 'watt']):
                power_sensors.append(key)
            elif any(term in key_lower for term in ['temp', 'humid', 'pressure']):
                environmental_sensors.append(key)
            elif any(term in key_lower for term in ['battery', 'charge', 'capacity', 'soc']):
                battery_sensors.append(key)
            else:
                status_sensors.append(key)
            
            # Analyze value types
            if isinstance(value, (int, float)):
                if key_lower not in analysis['data_types']:
                    analysis['data_types'][key_lower] = 'numeric'
            elif isinstance(value, str):
                analysis['data_types'][key_lower] = 'string'
        
        analysis['sensor_categories'] = {
            'power_sensors': power_sensors,
            'environmental_sensors': environmental_sensors,
            'battery_sensors': battery_sensors,
            'status_sensors': status_sensors
        }
        
        return analysis
    
    def create_ha_sensor_mapping(self, data: dict, analysis: dict) -> dict:
        """Create optimal sensor mapping for Home Assistant"""
        sensor_mapping = {
            'device_class_mapping': {},
            'unit_mapping': {},
            'friendly_names': {},
            'sensor_groups': {}
        }
        
        # Map sensors to HA device classes and units
        for category, sensors in analysis['sensor_categories'].items():
            for sensor in sensors:
                if sensor in data:
                    value = data[sensor]
                    
                    # Power-related sensors
                    if 'voltage' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'voltage'
                        sensor_mapping['unit_mapping'][sensor] = 'V'
                        sensor_mapping['friendly_names'][sensor] = f"Battery Voltage"
                    elif 'current' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'current'
                        sensor_mapping['unit_mapping'][sensor] = 'A'
                        sensor_mapping['friendly_names'][sensor] = f"Battery Current"
                    elif 'power' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'power'
                        sensor_mapping['unit_mapping'][sensor] = 'W'
                        sensor_mapping['friendly_names'][sensor] = f"Power Output"
                    elif 'energy' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'energy'
                        sensor_mapping['unit_mapping'][sensor] = 'Wh'
                        sensor_mapping['friendly_names'][sensor] = f"Energy Total"
                    
                    # Environmental sensors
                    elif 'temp' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'temperature'
                        sensor_mapping['unit_mapping'][sensor] = '°C'
                        sensor_mapping['friendly_names'][sensor] = f"Temperature"
                    elif 'humid' in sensor.lower():
                        sensor_mapping['device_class_mapping'][sensor] = 'humidity'
                        sensor_mapping['unit_mapping'][sensor] = '%'
                        sensor_mapping['friendly_names'][sensor] = f"Humidity"
                    
                    # Battery sensors
                    elif any(term in sensor.lower() for term in ['battery', 'soc', 'charge']):
                        sensor_mapping['device_class_mapping'][sensor] = 'battery'
                        sensor_mapping['unit_mapping'][sensor] = '%'
                        sensor_mapping['friendly_names'][sensor] = f"Battery Level"
                    
                    # Default for unknown sensors
                    else:
                        sensor_mapping['device_class_mapping'][sensor] = 'measurement'
                        sensor_mapping['unit_mapping'][sensor] = ''
                        sensor_mapping['friendly_names'][sensor] = sensor.replace('_', ' ').title()
        
        # Group sensors for HA dashboard organization
        sensor_mapping['sensor_groups'] = {
            'Power Monitoring': analysis['sensor_categories']['power_sensors'],
            'Environmental': analysis['sensor_categories']['environmental_sensors'],
            'Battery Status': analysis['sensor_categories']['battery_sensors'],
            'Device Status': analysis['sensor_categories']['status_sensors']
        }
        
        return sensor_mapping
    
    def generate_ha_config_yaml(self, sensor_mapping: dict) -> str:
        """Generate Home Assistant YAML configuration"""
        yaml_config = f"""# BluPow BT-TH Sensor Configuration
# Generated by Data Flow Optimizer
# Device: {self.mac_address} (BT-TH-6A667ED4)

sensor:
  - platform: blupow
    mac_address: "{self.mac_address}"
    name: "BluPow Power Monitor"
    scan_interval: 30
    sensors:
"""
        
        # Add each sensor with proper configuration
        for sensor_key, device_class in sensor_mapping['device_class_mapping'].items():
            friendly_name = sensor_mapping['friendly_names'].get(sensor_key, sensor_key)
            unit = sensor_mapping['unit_mapping'].get(sensor_key, '')
            
            yaml_config += f"""      - name: "{friendly_name}"
        key: "{sensor_key}"
        device_class: "{device_class}"
        unit_of_measurement: "{unit}"
        state_class: "measurement"
"""
        
        # Add sensor groups for dashboard
        yaml_config += f"""
# Sensor Groups for Dashboard Organization
group:
"""
        for group_name, sensors in sensor_mapping['sensor_groups'].items():
            if sensors:
                yaml_config += f"""  {group_name.lower().replace(' ', '_')}:
    name: "{group_name}"
    entities:
"""
                for sensor in sensors:
                    friendly_name = sensor_mapping['friendly_names'].get(sensor, sensor)
                    yaml_config += f"""      - sensor.{friendly_name.lower().replace(' ', '_').replace('-', '_')}
"""
        
        return yaml_config
    
    async def optimize_data_flow(self) -> dict:
        """Run complete data flow optimization"""
        logger.info(f"🚀 Optimizing data flow for {self.mac_address}")
        
        try:
            # Connect and get current data
            client = BluPowClient(self.mac_address)
            connected = await asyncio.wait_for(client.connect(), timeout=15)
            
            if not connected:
                logger.error("Failed to connect to device")
                return self.optimization_results
            
            logger.info("✅ Connected to BT-TH device")
            
            # Get data
            await client.read_device_info()
            data = client.get_data()
            await client.disconnect()
            
            if not data or len(data) < 10:
                logger.error("Insufficient data received")
                return self.optimization_results
            
            logger.info(f"📊 Analyzing {len(data)} data fields...")
            
            # Analyze data quality
            analysis = self.analyze_data_quality(data)
            self.optimization_results['data_analysis'] = analysis
            
            # Create HA sensor mapping
            sensor_mapping = self.create_ha_sensor_mapping(data, analysis)
            self.optimization_results['sensor_mapping'] = sensor_mapping
            
            # Generate HA config
            ha_yaml = self.generate_ha_config_yaml(sensor_mapping)
            self.optimization_results['ha_optimization']['yaml_config'] = ha_yaml
            
            # Sample current data
            self.optimization_results['sample_data'] = {k: v for k, v in data.items() if not k.startswith('_')}
            
            logger.info("🎉 Data flow optimization complete!")
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
        
        return self.optimization_results

async def main():
    """Run data flow optimization"""
    optimizer = DataFlowOptimizer()
    results = await optimizer.optimize_data_flow()
    
    print("\n" + "="*60)
    print("🎯 DATA FLOW OPTIMIZATION RESULTS")
    print("="*60)
    
    if 'data_analysis' in results:
        analysis = results['data_analysis']
        print(f"📊 Data Quality Analysis:")
        print(f"   Total Fields: {analysis['total_fields']}")
        print(f"   Meaningful Sensors: {analysis['meaningful_sensors']}")
        
        if 'sensor_categories' in analysis:
            categories = analysis['sensor_categories']
            print(f"   Power Sensors: {len(categories['power_sensors'])}")
            print(f"   Environmental Sensors: {len(categories['environmental_sensors'])}")
            print(f"   Battery Sensors: {len(categories['battery_sensors'])}")
            print(f"   Status Sensors: {len(categories['status_sensors'])}")
    
    if 'sample_data' in results and results['sample_data']:
        print(f"\n🔋 Sample Live Data:")
        count = 0
        for key, value in results['sample_data'].items():
            if count < 5:  # Show first 5 sensors
                print(f"   {key}: {value}")
                count += 1
    
    # Save results
    with open("data_flow_optimization_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save HA config if generated
    if 'ha_optimization' in results and 'yaml_config' in results['ha_optimization']:
        with open("blupow_ha_config.yaml", 'w') as f:
            f.write(results['ha_optimization']['yaml_config'])
        print(f"\n📄 Home Assistant config saved to: blupow_ha_config.yaml")
    
    print(f"\n📄 Full results saved to: data_flow_optimization_results.json")
    print(f"\n🎯 Ready for enhanced Home Assistant integration!")

if __name__ == "__main__":
    asyncio.run(main()) 