# UI Configuration Update Guide

## Entity Replacements Applied
*Generated: 2025-06-20 21:05:40*

### Missing → Available Entity Mappings

- `sensor.airthing_barn_temperature` → `sensor.airthings_wave_129002_temperature`\n- `sensor.airthing_barn_carbon_dioxide` → `sensor.airthings_wave_129002_carbon_dioxide`\n- `sensor.airthing_house_humidity` → `sensor.airthings_wave_112365_humidity`\n- `sensor.moresense_ms05_ms_c_co2` → `sensor.ms_c_co2`\n- `sensor.moresense_ms05_ms_g_co2` → `sensor.ms_g_co2`\n

### Manual UI Updates Required

If you have custom Lovelace dashboards or cards that reference the missing entities,
you'll need to manually update them with the new entity IDs.

### Steps to Update UI:

1. **Go to Settings → Dashboards**
2. **Edit each dashboard**
3. **Find cards with missing entities** (showing "Entity not available")
4. **Replace entity IDs** using the mappings above
5. **Save changes**

### Template Sensor Updates

For any template sensors referencing missing entities, update them in:
- `configuration.yaml`
- `templates.yaml` 
- Custom template files

### Automation Verification

All automations have been automatically updated with the new entity mappings.
Restart Home Assistant to apply changes.
