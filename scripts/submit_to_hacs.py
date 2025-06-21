#!/usr/bin/env python3
"""
BluPow HACS Default Store Submission Helper

This script helps prepare and submit BluPow to the HACS default store.
"""

import json
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """Check if all HACS requirements are met."""
    print("🔍 Checking HACS Requirements...")
    
    requirements = {
        "GitHub Topics": False,
        "GitHub Issues": False,
        "GitHub Release": False,
        "HACS Action": False,
        "Hassfest Action": False,
        "Home Assistant Brands": False,
        "Valid hacs.json": False,
        "Valid manifest.json": False
    }
    
    # Check if files exist
    if Path("hacs.json").exists():
        requirements["Valid hacs.json"] = True
        print("✅ hacs.json exists")
    else:
        print("❌ hacs.json missing")
    
    if Path("manifest.json").exists():
        requirements["Valid manifest.json"] = True
        print("✅ manifest.json exists")
    else:
        print("❌ manifest.json missing")
    
    if Path(".github/workflows/hacs.yaml").exists():
        requirements["HACS Action"] = True
        print("✅ HACS Action workflow exists")
    else:
        print("❌ HACS Action workflow missing")
    
    if Path(".github/workflows/hassfest.yaml").exists():
        requirements["Hassfest Action"] = True
        print("✅ Hassfest Action workflow exists")
    else:
        print("❌ Hassfest Action workflow missing")
    
    # Check GitHub settings via CLI
    try:
        result = subprocess.run(["gh", "repo", "view", "--json", "hasIssuesEnabled,latestRelease"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            repo_info = json.loads(result.stdout)
            if repo_info.get("hasIssuesEnabled"):
                requirements["GitHub Issues"] = True
                print("✅ GitHub Issues enabled")
            else:
                print("❌ GitHub Issues not enabled")
            
            if repo_info.get("latestRelease"):
                requirements["GitHub Release"] = True
                print("✅ GitHub Release exists")
            else:
                print("❌ No GitHub Release found")
    except Exception as e:
        print(f"⚠️  Could not check GitHub settings: {e}")
    
    # Summary
    passed = sum(requirements.values())
    total = len(requirements)
    print(f"\n📊 Requirements Check: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All requirements met! Ready for HACS submission.")
        return True
    else:
        print("⚠️  Some requirements not met. Please address the issues above.")
        return False

def create_hacs_submission():
    """Create the HACS default store submission entry."""
    print("\n📝 Creating HACS Submission Entry...")
    
    entry = '"MadGoatHaz/blupow"'
    
    print(f"Add this line to the HACS default repository:")
    print(f"Repository: https://github.com/hacs/default")
    print(f"File: integration")
    print(f"Entry: {entry}")
    print(f"Location: Add alphabetically in the list")
    
    # Create submission instructions
    instructions = f"""
# HACS Default Store Submission

## Step 1: Fork the HACS Default Repository
```bash
gh repo fork hacs/default
cd default
```

## Step 2: Add BluPow Entry
Edit the `integration` file and add this line alphabetically:
```
{entry}
```

## Step 3: Create Pull Request
```bash
git add integration
git commit -m "Add BluPow integration

- Renogy solar device integration via Bluetooth
- Production ready with comprehensive documentation
- All validation checks passing
- Repository: https://github.com/MadGoatHaz/blupow"

git push origin main
gh pr create --title "Add BluPow integration" --body "Add BluPow integration for Renogy solar devices"
```

## Validation Checklist
Before submitting, ensure:
- [ ] All GitHub Actions are passing
- [ ] Home Assistant Brands PR is submitted/merged
- [ ] Integration is tested and working
- [ ] Documentation is complete
- [ ] Repository meets all HACS requirements
"""
    
    with open("brand_assets/hacs_submission_instructions.md", "w") as f:
        f.write(instructions)
    
    print("📄 Instructions saved to brand_assets/hacs_submission_instructions.md")

def main():
    """Main submission helper function."""
    print("🚀 BluPow HACS Submission Helper")
    print("=" * 40)
    
    if check_requirements():
        create_hacs_submission()
        print("\n✅ Submission preparation complete!")
        print("📋 Next steps:")
        print("1. Submit Home Assistant Brands PR (see brand_assets/brands_submission_instructions.md)")
        print("2. Wait for GitHub Actions to pass")
        print("3. Submit HACS Default Store PR (see brand_assets/hacs_submission_instructions.md)")
    else:
        print("\n❌ Please fix the requirements before submitting to HACS.")
        sys.exit(1)

if __name__ == "__main__":
    main() 