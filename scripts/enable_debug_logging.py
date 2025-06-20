#!/usr/bin/env python3
"""
Enable debug logging for BluPow integration

This script adds debug logging configuration to Home Assistant 
to help diagnose integration setup issues.
"""

import json
import os
import sys
from datetime import datetime

def enable_blupow_debug_logging():
    """Enable debug logging for BluPow components"""
    
    # Home Assistant logging configuration path
    config_path = '/config/configuration.yaml'
    
    print("🔧 Enabling Debug Logging for BluPow")
    print("=" * 40)
    
    # Check if configuration.yaml exists
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    # Read current configuration
    try:
        with open(config_path, 'r') as f:
            config_content = f.read()
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False
    
    # Check if logger section exists
    logger_config = """
# BluPow Debug Logging
logger:
  default: info
  logs:
    custom_components.blupow: debug
    custom_components.blupow.blupow_client: debug
    custom_components.blupow.coordinator: debug
    custom_components.blupow.sensor: debug
    custom_components.blupow.config_flow: debug
"""
    
    # Check if BluPow logging is already configured
    if 'custom_components.blupow' in config_content:
        print("ℹ️  BluPow debug logging already configured")
        return True
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/config/configuration.yaml.backup_{timestamp}'
    
    try:
        with open(backup_path, 'w') as f:
            f.write(config_content)
        print(f"✅ Configuration backup created: {backup_path}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Add logger configuration
    updated_config = config_content + logger_config
    
    try:
        with open(config_path, 'w') as f:
            f.write(updated_config)
        print("✅ Debug logging configuration added")
        print("   Restart Home Assistant to enable debug logging")
        return True
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def main():
    print("🔍 BluPow Debug Logging Setup")
    print("=" * 30)
    
    if enable_blupow_debug_logging():
        print("\n📋 Next Steps:")
        print("   1. Restart Home Assistant")
        print("   2. Try adding BluPow integration")
        print("   3. Check logs: docker logs homeassistant | grep blupow")
        return 0
    else:
        print("\n❌ Failed to enable debug logging")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 