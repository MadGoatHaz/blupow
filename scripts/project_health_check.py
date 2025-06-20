#!/usr/bin/env python3
"""
BluPow Project Health Check

This script provides a comprehensive health check of the entire BluPow project,
including code consistency, documentation completeness, and system readiness.
Designed for both human review and AI/automation systems.

Usage:
    python3 scripts/project_health_check.py [options]

Options:
    --json              Output detailed results in JSON format
    --brief             Show only summary results
    --fix-issues        Attempt to automatically fix minor issues
    --device ADDRESS    Use specific device MAC address for hardware tests
    --skip-hardware     Skip hardware connection tests
    --help              Show this help message
"""

import asyncio
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HealthCheckResult:
    """Comprehensive health check results"""
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.overall_health = "UNKNOWN"
        self.categories = {}
        self.summary = {}
        self.recommendations = []
        self.critical_issues = []
        self.warnings = []
        
    def add_category(self, name: str, status: str, details: Dict[str, Any]):
        """Add a category result"""
        self.categories[name] = {
            'status': status,
            'details': details
        }
        
    def calculate_overall_health(self):
        """Calculate overall project health score"""
        if not self.categories:
            self.overall_health = "UNKNOWN"
            return
            
        statuses = [cat['status'] for cat in self.categories.values()]
        
        if 'CRITICAL' in statuses:
            self.overall_health = "CRITICAL"
        elif 'WARNING' in statuses:
            self.overall_health = "WARNING"
        elif all(status == 'HEALTHY' for status in statuses):
            self.overall_health = "HEALTHY"
        else:
            self.overall_health = "MIXED"
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'overall_health': self.overall_health,
            'categories': self.categories,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings
        }

class ProjectHealthChecker:
    """Comprehensive project health checker"""
    
    def __init__(self, device_address: str = "D8:B6:73:BF:4F:75"):
        self.device_address = device_address
        self.result = HealthCheckResult()
        
    async def run_full_check(self, skip_hardware: bool = False) -> HealthCheckResult:
        """Run all health checks"""
        print("🏥 BluPow Project Health Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target Device: {self.device_address}")
        print("-" * 50)
        
        # 1. Project Structure Check
        await self._check_project_structure()
        
        # 2. Code Consistency Check
        await self._check_code_consistency()
        
        # 3. Documentation Completeness
        await self._check_documentation()
        
        # 4. Configuration Validation
        await self._check_configuration()
        
        # 5. Hardware Tests (if not skipped)
        if not skip_hardware:
            await self._check_hardware_connectivity()
        
        # Calculate overall health
        self.result.calculate_overall_health()
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.result
    
    async def _check_project_structure(self):
        """Check project file structure and organization"""
        print("\n📁 Checking Project Structure...")
        
        required_files = {
            'Core Integration': [
                'blupow_client.py', 'coordinator.py', 'sensor.py', 
                'const.py', 'manifest.json', '__init__.py', 'config_flow.py'
            ],
            'Documentation': [
                'README.md', 'docs/PROJECT_HISTORY.md', 
                'docs/guides/VERIFICATION_GUIDE.md',
                'docs/guides/CONTAINER_SETUP_GUIDE.md'
            ],
            'Scripts': [
                'scripts/verify_connection.py', 'scripts/diagnostics.py'
            ]
        }
        
        missing_files = []
        found_files = []
        
        for category, files in required_files.items():
            for file_path in files:
                if Path(file_path).exists():
                    found_files.append(file_path)
                else:
                    missing_files.append(file_path)
        
        status = "HEALTHY" if not missing_files else "WARNING"
        if len(missing_files) > 3:
            status = "CRITICAL"
            
        details = {
            'total_required': sum(len(files) for files in required_files.values()),
            'found': len(found_files),
            'missing': missing_files,
            'completeness_percentage': (len(found_files) / sum(len(files) for files in required_files.values())) * 100
        }
        
        self.result.add_category('Project Structure', status, details)
        
        if missing_files:
            self.result.warnings.extend([f"Missing file: {f}" for f in missing_files])
        
        print(f"   Structure: {status} ({details['completeness_percentage']:.1f}% complete)")
    
    async def _check_code_consistency(self):
        """Check code consistency across the project"""
        print("\n🔍 Checking Code Consistency...")
        
        issues = []
        
        try:
            # Check if const.py has the correct sensor count
            from const import DEVICE_SENSORS
            sensor_count = len(DEVICE_SENSORS)
            
            if sensor_count != 22:
                issues.append(f"Expected 22 sensors, found {sensor_count}")
            
            # Check manifest version
            import json as json_module
            with open('manifest.json', 'r') as f:
                manifest = json_module.load(f)
            
            if 'Rover' in manifest.get('name', ''):
                issues.append("Manifest still references 'Rover' (charge controller)")
            
            # Check for version consistency
            version = manifest.get('version', '0.0.0')
            if version.startswith('0.'):
                issues.append(f"Version {version} suggests pre-release status")
                
        except Exception as e:
            issues.append(f"Code analysis failed: {str(e)}")
        
        status = "HEALTHY" if not issues else "WARNING"
        if len(issues) > 2:
            status = "CRITICAL"
            
        details = {
            'sensor_count': sensor_count if 'sensor_count' in locals() else 0,
            'issues_found': issues,
            'version': version if 'version' in locals() else 'unknown'
        }
        
        self.result.add_category('Code Consistency', status, details)
        
        if issues:
            self.result.warnings.extend(issues)
            
        print(f"   Code: {status} ({len(issues)} issues found)")
    
    async def _check_documentation(self):
        """Check documentation completeness and consistency"""
        print("\n📚 Checking Documentation...")
        
        doc_files = [
            'README.md',
            'docs/PROJECT_HISTORY.md',
            'docs/guides/VERIFICATION_GUIDE.md',
            'docs/guides/CONTAINER_SETUP_GUIDE.md',
            'docs/troubleshooting/TROUBLESHOOTING.md'
        ]
        
        issues = []
        word_counts = {}
        
        for doc_file in doc_files:
            if Path(doc_file).exists():
                try:
                    content = Path(doc_file).read_text()
                    word_count = len(content.split())
                    word_counts[doc_file] = word_count
                    
                    # Check for placeholder content
                    if word_count < 50:
                        issues.append(f"{doc_file} appears to be a stub ({word_count} words)")
                        
                    # Check for consistency
                    if 'charge controller' in content.lower() and 'inverter' not in content.lower():
                        issues.append(f"{doc_file} may contain outdated charge controller references")
                        
                except Exception as e:
                    issues.append(f"Could not analyze {doc_file}: {str(e)}")
            else:
                issues.append(f"Missing documentation file: {doc_file}")
        
        status = "HEALTHY" if not issues else "WARNING"
        if len(issues) > 3:
            status = "CRITICAL"
            
        details = {
            'files_checked': len(doc_files),
            'word_counts': word_counts,
            'issues': issues,
            'total_documentation_words': sum(word_counts.values())
        }
        
        self.result.add_category('Documentation', status, details)
        
        if issues:
            self.result.warnings.extend(issues)
            
        print(f"   Documentation: {status} ({sum(word_counts.values())} total words)")
    
    async def _check_configuration(self):
        """Check configuration files and settings"""
        print("\n⚙️  Checking Configuration...")
        
        issues = []
        
        try:
            # Check manifest.json
            with open('manifest.json', 'r') as f:
                manifest = json.load(f)
            
            required_manifest_fields = ['domain', 'name', 'version', 'requirements', 'dependencies']
            for field in required_manifest_fields:
                if field not in manifest:
                    issues.append(f"Missing manifest field: {field}")
            
            # Check if bluetooth dependency is present
            if 'bluetooth' not in manifest.get('dependencies', []):
                issues.append("Bluetooth dependency missing from manifest")
            
            # Check strings.json
            if Path('strings.json').exists():
                with open('strings.json', 'r') as f:
                    strings = json.load(f)
                    
                if 'config' not in strings:
                    issues.append("strings.json missing config section")
            else:
                issues.append("strings.json file missing")
                
        except Exception as e:
            issues.append(f"Configuration check failed: {str(e)}")
        
        status = "HEALTHY" if not issues else "WARNING"
        
        details = {
            'manifest_valid': 'manifest.json' in [str(p) for p in Path('.').glob('*.json')],
            'issues': issues
        }
        
        self.result.add_category('Configuration', status, details)
        
        if issues:
            self.result.warnings.extend(issues)
            
        print(f"   Configuration: {status}")
    
    async def _check_hardware_connectivity(self):
        """Check hardware connectivity and sensor data"""
        print("\n🔌 Checking Hardware Connectivity...")
        
        try:
            # Import and run the verification script logic
            from verify_connection import run_verification
            
            verification_result = await run_verification(self.device_address, quiet=True)
            
            if verification_result.success:
                status = "HEALTHY"
                details = {
                    'connection_successful': True,
                    'sensor_count': verification_result.sensor_count,
                    'data_sample': dict(list(verification_result.data.items())[:5])  # First 5 items
                }
            else:
                status = "WARNING"
                details = {
                    'connection_successful': False,
                    'error': verification_result.error_message,
                    'connected': verification_result.connected,
                    'data_received': verification_result.data_received
                }
                self.result.warnings.append(f"Hardware connectivity issue: {verification_result.error_message}")
                
        except Exception as e:
            status = "CRITICAL"
            details = {
                'connection_successful': False,
                'error': str(e)
            }
            self.result.critical_issues.append(f"Hardware test failed: {str(e)}")
        
        self.result.add_category('Hardware Connectivity', status, details)
        print(f"   Hardware: {status}")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # Structure recommendations
        if self.result.categories.get('Project Structure', {}).get('status') != 'HEALTHY':
            recommendations.append("Run 'python3 scripts/diagnostics.py --test structure' for detailed file analysis")
        
        # Code recommendations
        if self.result.categories.get('Code Consistency', {}).get('status') != 'HEALTHY':
            recommendations.append("Review const.py and manifest.json for consistency with inverter hardware")
        
        # Documentation recommendations
        if self.result.categories.get('Documentation', {}).get('status') != 'HEALTHY':
            recommendations.append("Update documentation to remove charge controller references")
        
        # Hardware recommendations
        if self.result.categories.get('Hardware Connectivity', {}).get('status') != 'HEALTHY':
            recommendations.append("Run 'python3 scripts/verify_connection.py' for detailed connection diagnostics")
            recommendations.append("Check docs/troubleshooting/TROUBLESHOOTING.md for connectivity solutions")
        
        self.result.recommendations = recommendations
    
    def print_summary(self, brief: bool = False):
        """Print a human-readable summary"""
        print(f"\n{'='*50}")
        print("📋 HEALTH CHECK SUMMARY")
        print(f"{'='*50}")
        print(f"Overall Health: {self.result.overall_health}")
        print(f"Timestamp: {self.result.timestamp}")
        
        if not brief:
            print(f"\n📊 Category Results:")
            for category, data in self.result.categories.items():
                status_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "❌"}.get(data['status'], "❓")
                print(f"  {status_emoji} {category}: {data['status']}")
        
        if self.result.critical_issues:
            print(f"\n🚨 Critical Issues ({len(self.result.critical_issues)}):")
            for issue in self.result.critical_issues:
                print(f"  • {issue}")
        
        if self.result.warnings and not brief:
            print(f"\n⚠️  Warnings ({len(self.result.warnings)}):")
            for warning in self.result.warnings[:5]:  # Show first 5
                print(f"  • {warning}")
            if len(self.result.warnings) > 5:
                print(f"  ... and {len(self.result.warnings) - 5} more")
        
        if self.result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in self.result.recommendations:
                print(f"  • {rec}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BluPow Project Health Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/project_health_check.py                    # Full interactive check
    python3 scripts/project_health_check.py --json             # JSON output for AI
    python3 scripts/project_health_check.py --brief            # Brief summary only
    python3 scripts/project_health_check.py --skip-hardware    # Skip hardware tests
        """
    )
    
    parser.add_argument('--json', action='store_true',
                        help='Output detailed results in JSON format')
    parser.add_argument('--brief', action='store_true',
                        help='Show only summary results')
    parser.add_argument('--device', default="D8:B6:73:BF:4F:75",
                        help='Device MAC address for hardware tests')
    parser.add_argument('--skip-hardware', action='store_true',
                        help='Skip hardware connection tests')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    checker = ProjectHealthChecker(args.device)
    result = await checker.run_full_check(skip_hardware=args.skip_hardware)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        checker.print_summary(brief=args.brief)
    
    # Return appropriate exit code
    if result.overall_health == "CRITICAL":
        return 2
    elif result.overall_health == "WARNING":
        return 1
    else:
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nHealth check cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(2) 