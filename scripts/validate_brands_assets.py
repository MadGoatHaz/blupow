#!/usr/bin/env python3
"""
Home Assistant Brands Assets Validation Script

Validates that BluPow brand assets meet all Home Assistant brands requirements.
"""

import json
import os
from pathlib import Path
from PIL import Image

def validate_brands_assets():
    """Validate Home Assistant brands assets compliance."""
    print("🎨 Home Assistant Brands Assets Validation")
    print("=" * 50)
    
    brands_dir = Path("brand_assets/home_assistant_brands/custom_integrations/blupow")
    
    if not brands_dir.exists():
        print("❌ Brands directory not found")
        return False
    
    print(f"📁 Checking directory: {brands_dir}")
    
    # Check required files
    required_files = {
        "icon.png": (256, 256),
        "icon@2x.png": (512, 512),
        "manifest.json": None
    }
    
    all_valid = True
    
    for filename, expected_size in required_files.items():
        filepath = brands_dir / filename
        
        if not filepath.exists():
            print(f"❌ Missing file: {filename}")
            all_valid = False
            continue
        
        if filename.endswith('.png'):
            # Validate PNG image
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    format_type = img.format
                    mode = img.mode
                    
                    print(f"📸 {filename}:")
                    print(f"   Size: {width}x{height} pixels")
                    print(f"   Format: {format_type}")
                    print(f"   Mode: {mode}")
                    
                    # Check size requirements
                    if expected_size and (width, height) != expected_size:
                        print(f"   ❌ Size mismatch. Expected: {expected_size[0]}x{expected_size[1]}")
                        all_valid = False
                    else:
                        print(f"   ✅ Size correct: {width}x{height}")
                    
                    # Check format
                    if format_type != 'PNG':
                        print(f"   ❌ Wrong format. Expected PNG, got {format_type}")
                        all_valid = False
                    else:
                        print(f"   ✅ Format correct: PNG")
                    
                    # Check aspect ratio for icons
                    if 'icon' in filename:
                        if width != height:
                            print(f"   ❌ Not square. Icons must be 1:1 aspect ratio")
                            all_valid = False
                        else:
                            print(f"   ✅ Square aspect ratio")
                    
                    # Check transparency support
                    if mode in ('RGBA', 'LA') or 'transparency' in img.info:
                        print(f"   ✅ Transparency support")
                    else:
                        print(f"   ⚠️  No transparency detected")
                    
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
                all_valid = False
        
        elif filename == 'manifest.json':
            # Validate manifest.json
            try:
                with open(filepath, 'r') as f:
                    manifest = json.load(f)
                
                print(f"📄 {filename}:")
                
                required_keys = ['domain', 'name', 'integrations']
                for key in required_keys:
                    if key in manifest:
                        print(f"   ✅ {key}: {manifest[key]}")
                    else:
                        print(f"   ❌ Missing key: {key}")
                        all_valid = False
                
                # Check domain matches directory
                if manifest.get('domain') != 'blupow':
                    print(f"   ❌ Domain mismatch. Expected 'blupow', got '{manifest.get('domain')}'")
                    all_valid = False
                else:
                    print(f"   ✅ Domain matches directory name")
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in {filename}: {e}")
                all_valid = False
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
                all_valid = False
    
    # Final validation summary
    print("\n📊 Validation Summary")
    print("-" * 30)
    
    if all_valid:
        print("🎉 All Home Assistant brands requirements met!")
        print("✅ Ready for submission to home-assistant/brands")
        print("\n📋 Next Steps:")
        print("1. Fork https://github.com/home-assistant/brands")
        print("2. Copy files to custom_integrations/blupow/")
        print("3. Submit pull request")
        print("4. Wait for review and merge")
        return True
    else:
        print("❌ Some requirements not met. Please fix the issues above.")
        return False

if __name__ == "__main__":
    try:
        from PIL import Image
        validate_brands_assets()
    except ImportError:
        print("❌ PIL (Pillow) not installed. Install with: pip install Pillow")
        print("Running basic validation without image analysis...")
        
        # Basic file existence check
        brands_dir = Path("brand_assets/home_assistant_brands/custom_integrations/blupow")
        required_files = ["icon.png", "icon@2x.png", "manifest.json"]
        
        print("📁 Basic File Check:")
        all_exist = True
        for filename in required_files:
            filepath = brands_dir / filename
            if filepath.exists():
                print(f"✅ {filename} exists")
            else:
                print(f"❌ {filename} missing")
                all_exist = False
        
        if all_exist:
            print("✅ All required files present")
        else:
            print("❌ Some files missing") 