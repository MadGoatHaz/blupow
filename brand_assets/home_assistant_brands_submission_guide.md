# Home Assistant Brands Submission Guide for BluPow

## 📁 Files Ready for Submission

The following files in `brand_assets/home_assistant_brands/` are ready for submission to the [Home Assistant brands repository](https://github.com/home-assistant/brands):

```
custom_integrations/blupow/
├── icon.png        (256x256 pixels - Square icon)
├── icon@2x.png     (512x512 pixels - hDPI version)  
└── manifest.json   (Domain and integration info)
```

## 🎯 Submission Process

### Step 1: Fork the Repository
```bash
# Fork the Home Assistant brands repository
gh repo fork home-assistant/brands
cd brands
```

### Step 2: Create the Directory Structure
```bash
# Create the custom integrations directory for blupow
mkdir -p custom_integrations/blupow
```

### Step 3: Copy the Files
Copy these files from your `brand_assets/home_assistant_brands/custom_integrations/blupow/` directory:

- `icon.png` → `custom_integrations/blupow/icon.png`
- `icon@2x.png` → `custom_integrations/blupow/icon@2x.png`
- `manifest.json` → `custom_integrations/blupow/manifest.json`

### Step 4: Commit and Push
```bash
git add custom_integrations/blupow/
git commit -m "Add BluPow integration brand assets

- Domain: blupow
- Custom integration for Renogy solar devices via Bluetooth
- Professional BluPow logo in required sizes (256px, 512px)
- Repository: https://github.com/MadGoatHaz/blupow

Brand assets include:
- Square icon in 256x256 and 512x512 (hDPI) formats
- Proper manifest.json with domain information
- PNG format with transparency and optimization"

git push origin master
```

### Step 5: Create Pull Request
```bash
gh pr create \
  --title "Add BluPow integration brand assets" \
  --body "This PR adds brand assets for the BluPow custom integration.

**Integration Details:**
- **Domain:** blupow  
- **Name:** BluPow - Renogy Device Integration
- **Type:** Custom integration
- **Repository:** https://github.com/MadGoatHaz/blupow
- **Purpose:** Home Assistant integration for Renogy solar devices via Bluetooth

**Brand Assets:**
- ✅ Square icon (256x256 pixels)
- ✅ hDPI icon (512x512 pixels)  
- ✅ PNG format with transparency
- ✅ Properly optimized for web use
- ✅ Professional BluPow branding

**Compliance:**
- ✅ Follows Home Assistant brands image specifications
- ✅ Custom integration (not core)
- ✅ Proper directory structure: custom_integrations/blupow/
- ✅ Includes required manifest.json

The integration is production-ready and will be submitted to HACS default store."
```

## ✅ Image Specifications Compliance

Our brand assets meet all [Home Assistant brands requirements](https://github.com/home-assistant/brands):

### Icon Requirements ✅
- ✅ **Format:** PNG with transparency
- ✅ **Aspect Ratio:** 1:1 (square)
- ✅ **Size:** 256x256 pixels (normal), 512x512 pixels (hDPI)
- ✅ **Optimization:** Properly compressed for web use
- ✅ **Trimming:** Minimal empty space around logo
- ✅ **Background:** Optimized for white background with transparency

### Directory Structure ✅
- ✅ **Location:** custom_integrations/blupow/ (custom integration)
- ✅ **Domain Match:** Directory name matches integration domain
- ✅ **Required Files:** icon.png, icon@2x.png, manifest.json

### Content Requirements ✅
- ✅ **Professional Branding:** Official BluPow logo
- ✅ **No HA Branding:** Does not use Home Assistant branded images
- ✅ **Domain Compliance:** Matches integration manifest.json domain

## 🚀 Expected Outcome

After PR approval and merge:
- BluPow brand assets will be available at:
  - `https://brands.home-assistant.io/blupow/icon.png`
  - `https://brands.home-assistant.io/blupow/icon@2x.png`
- Home Assistant will automatically use these assets for the BluPow integration
- HACS validation will pass the brands requirement
- Integration will have professional branding in Home Assistant UI

## 📋 Next Steps After Brands Submission

1. **Wait for PR Review** - Home Assistant team will review the submission
2. **Address Feedback** - Make any requested changes
3. **PR Merge** - Assets become available on brands.home-assistant.io
4. **HACS Submission** - Submit to HACS default store with brands requirement met
5. **User Availability** - Integration appears in HACS store for easy installation

## 🎯 Timeline

- **Brands PR:** 1-2 weeks for review and merge
- **HACS Submission:** Can submit immediately after brands merge
- **HACS Review:** 2-4 weeks for default store inclusion
- **User Access:** Custom repository available immediately, default store after review 