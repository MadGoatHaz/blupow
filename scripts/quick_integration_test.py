#!/usr/bin/env python3
"""
Quick BluPow Integration Test

Focused test to identify and fix the critical issues from the Home Assistant logs.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

def test_critical_issues():
    """Test the critical issues identified in the logs"""
    print("🔍 BluPow Critical Issues Test")
    print("=" * 50)
    
    issues_found = []
    fixes_needed = []
    
    # Issue 1: Check for deprecated constants in const.py
    print("\n1. Checking const.py for deprecated constants...")
    try:
        with open('const.py', 'r') as f:
            const_content = f.read()
        
        deprecated_constants = [
            'ELECTRIC_CURRENT_AMPERE',
            'ELECTRIC_POTENTIAL_VOLT', 
            'ENERGY_KILO_WATT_HOUR',
            'POWER_WATT',
            'TEMPERATURE_CELSIUS',
            'TIME_DAYS',
            'FREQUENCY_HERTZ'
        ]
        
        found_deprecated = []
        for const in deprecated_constants:
            if const in const_content:
                found_deprecated.append(const)
        
        if found_deprecated:
            issues_found.append(f"Deprecated constants found: {found_deprecated}")
            fixes_needed.append("Remove deprecated constants from const.py imports")
        else:
            print("✅ No deprecated constants found")
            
    except Exception as e:
        issues_found.append(f"Could not check const.py: {e}")
    
    # Issue 2: Check sensor device class/unit mismatches
    print("\n2. Checking for device class/unit mismatches...")
    
    # Common mismatches from the logs
    problematic_patterns = [
        ('power', 'A'),  # Power device class with Ampere unit
        ('power', 'V'),  # Power device class with Volt unit  
        ('power', '%'),  # Power device class with Percentage unit
        ('power', 'C'),  # Power device class with Celsius unit
        ('temperature', 'C'),  # Should be '°C'
    ]
    
    try:
        with open('const.py', 'r') as f:
            const_content = f.read()
            
        mismatches_found = []
        for device_class, unit in problematic_patterns:
            if f'device_class=SensorDeviceClass.{device_class.upper()}' in const_content and f"'{unit}'" in const_content:
                mismatches_found.append(f"{device_class} device class with {unit} unit")
        
        if mismatches_found:
            issues_found.append(f"Device class/unit mismatches: {mismatches_found}")
            fixes_needed.append("Fix sensor device class and unit combinations")
        else:
            print("✅ No obvious device class/unit mismatches found")
            
    except Exception as e:
        issues_found.append(f"Could not check device classes: {e}")
    
    # Issue 3: Check import structure in blupow_client.py
    print("\n3. Checking import structure...")
    try:
        with open('blupow_client.py', 'r') as f:
            client_content = f.read()
        
        import_issues = []
        
        # Check for relative import fallback
        if 'from const import' in client_content and 'try:' not in client_content.split('from const import')[0][-50:]:
            import_issues.append("Missing try/except for relative imports")
        
        # Check for proper fallback constants
        required_fallbacks = ['RENOGY_SERVICE_UUID', 'RENOGY_TX_CHAR_UUID', 'RENOGY_RX_CHAR_UUID']
        for fallback in required_fallbacks:
            if fallback not in client_content:
                import_issues.append(f"Missing fallback for {fallback}")
        
        if import_issues:
            issues_found.append(f"Import issues: {import_issues}")
            fixes_needed.append("Fix import structure with proper fallbacks")
        else:
            print("✅ Import structure looks good")
            
    except Exception as e:
        issues_found.append(f"Could not check imports: {e}")
    
    # Issue 4: Check manifest.json compatibility
    print("\n4. Checking manifest.json...")
    try:
        import json
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
        
        manifest_issues = []
        
        # Check version compatibility
        if 'version' not in manifest:
            manifest_issues.append("Missing version in manifest")
        
        # Check dependencies
        if 'dependencies' in manifest and 'bluetooth' not in manifest['dependencies']:
            manifest_issues.append("Missing bluetooth dependency")
        
        # Check requirements
        if 'requirements' in manifest:
            requirements = manifest['requirements']
            if not any('bleak' in req for req in requirements):
                manifest_issues.append("Missing bleak requirement")
        
        if manifest_issues:
            issues_found.append(f"Manifest issues: {manifest_issues}")
            fixes_needed.append("Fix manifest.json configuration")
        else:
            print("✅ Manifest.json looks good")
            
    except Exception as e:
        issues_found.append(f"Could not check manifest: {e}")
    
    # Issue 5: Test basic file structure
    print("\n5. Checking file structure...")
    required_files = [
        '__init__.py',
        'const.py',
        'blupow_client.py', 
        'coordinator.py',
        'sensor.py',
        'manifest.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        issues_found.append(f"Missing files: {missing_files}")
        fixes_needed.append("Ensure all required integration files are present")
    else:
        print("✅ All required files present")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} critical issues:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n🔧 Fixes needed:")
        for i, fix in enumerate(fixes_needed, 1):
            print(f"   {i}. {fix}")
            
        return False
    else:
        print("✅ No critical issues found!")
        return True

def suggest_specific_fixes():
    """Suggest specific fixes for the most common issues"""
    print("\n🔧 SPECIFIC FIX SUGGESTIONS")
    print("=" * 50)
    
    fixes = [
        {
            'issue': 'Deprecated constants in const.py',
            'file': 'const.py',
            'fix': 'Remove deprecated imports like ELECTRIC_CURRENT_AMPERE and use UnitOfElectricCurrent.AMPERE instead'
        },
        {
            'issue': 'Device class/unit mismatches',
            'file': 'const.py', 
            'fix': 'Ensure sensors with device_class="power" use UnitOfPower.WATT, not amperes or volts'
        },
        {
            'issue': 'Import failures',
            'file': 'blupow_client.py',
            'fix': 'Add proper try/except blocks for relative imports with fallback constants'
        },
        {
            'issue': 'Template errors with unknown values',
            'file': 'sensor.py',
            'fix': 'Add better null value handling in sensor native_value property'
        }
    ]
    
    for fix in fixes:
        print(f"\n📝 {fix['issue']}:")
        print(f"   File: {fix['file']}")
        print(f"   Fix: {fix['fix']}")

if __name__ == "__main__":
    success = test_critical_issues()
    
    if not success:
        suggest_specific_fixes()
        print(f"\n💡 Run this test again after applying fixes to verify resolution.")
        sys.exit(1)
    else:
        print(f"\n🎉 All critical issues resolved! Integration should be working correctly.")
        sys.exit(0) 