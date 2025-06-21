# BluPow Project Structure

This document provides a clear overview of the BluPow integration's file and directory structure.

## 📁 Root Directory

The root directory contains the core integration files, primary documentation, and configuration.

- `__init__.py`: Handles the initial setup of the integration in Home Assistant.
- `config_flow.py`: Manages the user configuration flow (e.g., adding the device).
- `const.py`: Contains all project-wide constants, including sensor definitions.
- `coordinator.py`: The data update coordinator, which schedules and manages data fetching.
- `sensor.py`: Defines the Home Assistant sensor entities.
- `manifest.json`: The integration's manifest file, defining its properties.
- `README.md`: The main entry point for understanding the project.
- `PROJECT_STRUCTURE.md`: This file.
- `LICENSE`: The project's license.

## 📁 `docs/` - Documentation

This directory contains all project documentation, organized for clarity.

- `PROJECT_HISTORY.md`: **(Start here for context)** A detailed history of the project's evolution, explaining the critical "inverter vs. charge controller" discovery.
- `guides/`: Contains all user-facing guides.
  - `VERIFICATION_GUIDE.md`: Step-by-step instructions for verifying the connection to the inverter.
  - `CONTAINER_SETUP_GUIDE.md`: The definitive guide for configuring Docker, including advanced AppArmor and Bluetooth troubleshooting.
  - `ENERGY_DASHBOARD_PLAN.md`: A plan for integrating the sensors with the Home Assistant Energy Dashboard.
  - `FUTURE_VISION.md`: High-level goals and future ideas for the project.
- `troubleshooting/`: Specific troubleshooting documents.
  - `TROUBLESHOOTING.md`: General troubleshooting steps for common issues.
  - `BLUETOOTH_CONNECTION_GUIDE.md`: A guide focused on Bluetooth-specific problems.
- `development/`: Notes and research for developers.
  - `AUTHENTICATION_RESEARCH.md`: Historical research on the device's protocol.
  - `NEXT_STEPS.md`: A historical document outlining the recovery plan.
  - `TESTING_GUIDE.md`: A guide for testing the integration.

## 📁 `scripts/` - Utility & Diagnostic Scripts

This directory contains helpful scripts for testing, verification, and diagnostics.

- `verify_connection.py`: **(Primary user tool)** A simple script to perform a live connection test and verify data retrieval. Supports both interactive and CLI modes for AI automation.
- `diagnostics.py`: **(Advanced diagnostics)** A powerful, menu-driven diagnostic tool for in-depth troubleshooting of connectivity, sensors, and project structure. Fully supports CLI automation.
- `project_health_check.py`: **(Comprehensive analysis)** A master health check script that provides complete project analysis, including code consistency, documentation completeness, and system readiness.

### CLI Examples for AI Contributors

```bash
# Quick connection verification with JSON output
python3 scripts/verify_connection.py --json --quiet

# Run specific diagnostic tests
python3 scripts/diagnostics.py --test connection --json
python3 scripts/diagnostics.py --test sensors --quiet

# Comprehensive project health check
python3 scripts/project_health_check.py --json
python3 scripts/project_health_check.py --brief --skip-hardware
```

## 📁 `brand/` & `translations/`