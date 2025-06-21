# Home Assistant Brands Submission for BluPow

## Files to Submit to home-assistant/brands

### 1. Brand Directory Structure
Create the following directory structure in the `home-assistant/brands` repository:

```
brands/
└── core_integrations/
    └── blupow/
        ├── icon.png        (256x256 - from brand_assets/icon-256.png)
        ├── icon@2x.png     (512x512 - from brand_assets/icon-512.png)
        └── manifest.json   (from brand_assets/brands_submission.json)
```

### 2. Submission Process
1. Fork the `home-assistant/brands` repository
2. Create the `brands/core_integrations/blupow/` directory
3. Copy the files as specified above
4. Submit a pull request with title: "Add BluPow integration brand"

### 3. Files Ready for Submission
- `brand_assets/icon-256.png` → `brands/core_integrations/blupow/icon.png`
- `brand_assets/icon-512.png` → `brands/core_integrations/blupow/icon@2x.png`
- `brand_assets/brands_submission.json` → `brands/core_integrations/blupow/manifest.json`

### 4. PR Description Template
```
Add BluPow integration brand

This PR adds the brand assets for the BluPow integration, which provides 
Home Assistant integration for Renogy solar devices via Bluetooth.

- Domain: blupow
- Integration: Custom integration for Renogy solar equipment
- Repository: https://github.com/MadGoatHaz/blupow
- Icons: Professional BluPow logo in required sizes

The integration is production-ready and will be submitted to HACS default store.
``` 