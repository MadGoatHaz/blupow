#!/usr/bin/env python3
"""
BluPow Integration Cleanup and Diagnostic Script

This script addresses the "already_configured" issue where Home Assistant
config entries exist but the integration doesn't appear in the UI.

Usage:
    python3 cleanup_integration.py [--dry-run] [--force-cleanup]
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

def load_config_entries():
    """Load Home Assistant config entries"""
    config_path = '/config/.storage/core.config_entries'
    if not os.path.exists(config_path):
        print("❌ Config entries file not found")
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config entries: {e}")
        return None

def backup_config_entries():
    """Create backup of config entries"""
    config_path = '/config/.storage/core.config_entries'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/config/.storage/core.config_entries.backup_{timestamp}'
    
    try:
        with open(config_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"✅ Config backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def save_config_entries(config_data):
    """Save config entries back to file"""
    config_path = '/config/.storage/core.config_entries'
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        print("✅ Config entries updated")
        return True
    except Exception as e:
        print(f"❌ Error saving config entries: {e}")
        return False

def analyze_blupow_entries(config_data):
    """Analyze BluPow config entries"""
    entries = config_data.get('data', {}).get('entries', [])
    blupow_entries = [entry for entry in entries if entry.get('domain') == 'blupow']
    
    print(f"\n📊 BluPow Integration Analysis:")
    print(f"   Total entries found: {len(blupow_entries)}")
    
    for i, entry in enumerate(blupow_entries):
        print(f"\n   Entry {i+1}:")
        print(f"     ID: {entry.get('entry_id')}")
        print(f"     Title: {entry.get('title')}")
        print(f"     State: {entry.get('state', 'None')}")
        print(f"     Created: {entry.get('created_at', 'Unknown')}")
        print(f"     Modified: {entry.get('modified_at', 'Unknown')}")
        print(f"     Data: {entry.get('data', {})}")
        print(f"     Options: {entry.get('options', {})}")
        
        # Check for issues
        issues = []
        if not entry.get('data', {}).get('address'):
            issues.append("Missing device address")
        if entry.get('state') not in [None, 'loaded']:
            issues.append(f"Unusual state: {entry.get('state')}")
        if not entry.get('title'):
            issues.append("Missing title")
            
        if issues:
            print(f"     ⚠️  Issues: {', '.join(issues)}")
        else:
            print(f"     ✅ Entry appears valid")
    
    return blupow_entries

def cleanup_blupow_entries(config_data, force=False):
    """Remove BluPow config entries"""
    entries = config_data.get('data', {}).get('entries', [])
    original_count = len(entries)
    
    # Filter out BluPow entries
    cleaned_entries = [entry for entry in entries if entry.get('domain') != 'blupow']
    removed_count = original_count - len(cleaned_entries)
    
    if removed_count > 0:
        config_data['data']['entries'] = cleaned_entries
        print(f"🧹 Removed {removed_count} BluPow config entries")
        return True
    else:
        print("ℹ️  No BluPow entries to remove")
        return False

def check_integration_files():
    """Check if BluPow integration files are properly installed"""
    print("\n🔍 Integration File Check:")
    
    required_files = [
        '/config/custom_components/blupow/__init__.py',
        '/config/custom_components/blupow/manifest.json',
        '/config/custom_components/blupow/config_flow.py',
        '/config/custom_components/blupow/const.py',
        '/config/custom_components/blupow/sensor.py',
        '/config/custom_components/blupow/coordinator.py',
        '/config/custom_components/blupow/blupow_client.py'
    ]
    
    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_present = False
    
    return all_present

def test_integration_import():
    """Test if BluPow integration can be imported"""
    print("\n🧪 Integration Import Test:")
    
    try:
        sys.path.insert(0, '/config/custom_components')
        import blupow
        print("   ✅ Main module imports successfully")
        
        # Test key components
        from blupow.const import DOMAIN, DEVICE_SENSORS
        print(f"   ✅ Constants: Domain={DOMAIN}, Sensors={len(DEVICE_SENSORS)}")
        
        from blupow.blupow_client import BluPowClient
        print("   ✅ BluPowClient imports")
        
        from blupow.coordinator import BluPowDataUpdateCoordinator
        print("   ✅ Coordinator imports")
        
        from blupow.sensor import BluPowSensor
        print("   ✅ Sensor imports")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='BluPow Integration Cleanup Tool')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--force-cleanup', action='store_true',
                       help='Remove all BluPow config entries')
    
    args = parser.parse_args()
    
    print("🔧 BluPow Integration Diagnostic and Cleanup Tool")
    print("=" * 50)
    
    # Check integration files
    files_ok = check_integration_files()
    
    # Test imports
    import_ok = test_integration_import()
    
    # Load and analyze config entries
    config_data = load_config_entries()
    if not config_data:
        return 1
    
    blupow_entries = analyze_blupow_entries(config_data)
    
    # Determine action
    if not blupow_entries:
        print("\n✅ No BluPow config entries found - integration should be addable")
        return 0
    
    if args.force_cleanup or len(blupow_entries) > 0:
        print(f"\n🧹 Cleanup Action:")
        
        if args.dry_run:
            print("   DRY RUN: Would remove all BluPow config entries")
            print("   To actually perform cleanup, run without --dry-run")
        else:
            # Create backup
            backup_path = backup_config_entries()
            if not backup_path:
                print("❌ Could not create backup - aborting")
                return 1
            
            # Perform cleanup
            if cleanup_blupow_entries(config_data):
                if save_config_entries(config_data):
                    print("\n✅ Cleanup completed successfully!")
                    print("   You can now restart Home Assistant and re-add the BluPow integration")
                    print(f"   Config backup: {backup_path}")
                else:
                    print("❌ Failed to save cleaned config")
                    return 1
            else:
                print("ℹ️  No cleanup needed")
    
    # Final recommendations
    print(f"\n📋 Recommendations:")
    if not files_ok:
        print("   1. Fix missing integration files")
    if not import_ok:
        print("   2. Fix import errors in integration code")
    if blupow_entries and not args.force_cleanup:
        print("   3. Run with --force-cleanup to remove orphaned entries")
    if files_ok and import_ok and not blupow_entries:
        print("   1. Integration should be ready to add through Home Assistant UI")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 