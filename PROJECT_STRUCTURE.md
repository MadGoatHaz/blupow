# BluPow Project Structure

## 📁 Directory Organization

```
blupow/
├── 📂 brand/                    # Branding assets
│   └── blupow/
│       ├── logo.png
│       └── manifest.json
├── 📂 docs/                     # Documentation
│   ├── 📂 guides/               # User guides
│   │   ├── CONTAINER_SETUP_GUIDE.md
│   │   ├── ENERGY_DASHBOARD_PLAN.md
│   │   └── FUTURE_VISION.md
│   ├── 📂 troubleshooting/      # Troubleshooting guides
│   │   └── TROUBLESHOOTING.md
│   ├── 📂 development/          # Developer documentation
│   │   ├── CONTEXT_GUIDE.md
│   │   ├── SESSION_SUMMARY.md
│   │   └── TESTING_GUIDE.md
│   ├── CURRENT_STATUS.md
│   └── DOCUMENTATION.md
├── 📂 info/                     # Reference information
│   └── AppArmor Info.txt        # AppArmor security reference
├── 📂 logs/                     # Log files (created at runtime)
├── 📂 results/                  # Test and analysis results
│   ├── progress_log.json
│   ├── progress_results.json
│   └── proxy_move_results.md
├── 📂 scripts/                  # Utility scripts
│   ├── deploy.sh                # Deployment script
│   └── setup_container_bluetooth.sh  # Container setup script
├── 📂 tests/                    # Testing framework
│   ├── 📂 diagnostics/          # Diagnostic tools
│   │   ├── blupow_testing_suite.py
│   │   ├── device_discovery_system.py
│   │   ├── device_wake_system.py
│   │   └── monitor_progress.py
│   ├── 📂 integration/          # Integration tests
│   │   ├── connection_test.py
│   │   ├── proxy_test.py
│   │   ├── quick_test.py
│   │   └── simple_test.py
│   └── 📂 unit/                 # Unit tests (future)
├── 📂 translations/             # Internationalization
│   └── en.json
├── 📂 .vscode/                  # VS Code configuration
│   └── settings.json
├── 📄 Core Integration Files    # Home Assistant integration
│   ├── __init__.py              # Integration entry point
│   ├── blupow_client.py         # Main client implementation
│   ├── config_flow.py           # Configuration flow
│   ├── const.py                 # Constants and configuration
│   ├── coordinator.py           # Data coordinator
│   ├── diagnostics.py           # Diagnostic data
│   ├── manifest.json            # Integration manifest
│   ├── sensor.py                # Sensor platform
│   └── strings.json             # UI strings
├── 📄 Project Files
│   ├── .gitignore               # Git ignore rules
│   ├── BluPow.png              # Project logo
│   ├── LICENSE                  # License file
│   └── README.md               # Main project documentation
└── 📄 Legacy Files
    └── Home Assistant Integration.txt  # Original integration notes
```

## 📋 File Categories

### Core Integration Files
These are the main Home Assistant integration files that should remain in the root directory:

- **`__init__.py`** - Integration entry point and setup
- **`blupow_client.py`** - Main Bluetooth client implementation
- **`config_flow.py`** - Configuration flow for Home Assistant UI
- **`const.py`** - Constants, device definitions, and configuration
- **`coordinator.py`** - Data update coordinator
- **`diagnostics.py`** - Diagnostic data collection
- **`manifest.json`** - Integration manifest for Home Assistant
- **`sensor.py`** - Sensor platform implementation
- **`strings.json`** - UI strings and translations

### Documentation (`docs/`)
Organized by purpose and audience:

#### Guides (`docs/guides/`)
- **`CONTAINER_SETUP_GUIDE.md`** - Docker container configuration
- **`ENERGY_DASHBOARD_PLAN.md`** - Energy dashboard integration plan
- **`FUTURE_VISION.md`** - Long-term roadmap and automation vision

#### Troubleshooting (`docs/troubleshooting/`)
- **`TROUBLESHOOTING.md`** - Complete troubleshooting guide

#### Development (`docs/development/`)
- **`CONTEXT_GUIDE.md`** - Developer context and background
- **`SESSION_SUMMARY.md`** - Development session summaries
- **`TESTING_GUIDE.md`** - Testing procedures and methodologies

### Testing Framework (`tests/`)

#### Diagnostics (`tests/diagnostics/`)
- **`blupow_testing_suite.py`** - Comprehensive testing suite
- **`device_discovery_system.py`** - Device discovery testing
- **`device_wake_system.py`** - Device wake-up testing
- **`monitor_progress.py`** - Progress monitoring tools

#### Integration Tests (`tests/integration/`)
- **`connection_test.py`** - Connection testing
- **`proxy_test.py`** - Bluetooth proxy testing
- **`quick_test.py`** - Quick diagnostic tests
- **`simple_test.py`** - Simple functionality tests

### Scripts (`scripts/`)
- **`deploy.sh`** - Automated deployment to Home Assistant
- **`setup_container_bluetooth.sh`** - Container Bluetooth setup

### Reference Information (`info/`)
- **`AppArmor Info.txt`** - Comprehensive AppArmor security reference

### Results (`results/`)
- Test results, logs, and analysis outputs

## 🚀 Usage Patterns

### For Users
1. **Setup**: Use `scripts/setup_container_bluetooth.sh`
2. **Deploy**: Use `scripts/deploy.sh`
3. **Troubleshooting**: Check `docs/troubleshooting/TROUBLESHOOTING.md`
4. **Testing**: Run `tests/diagnostics/blupow_testing_suite.py`

### For Developers
1. **Context**: Read `docs/development/CONTEXT_GUIDE.md`
2. **Testing**: Use files in `tests/` directory
3. **Documentation**: Update files in `docs/` directory
4. **Reference**: Check `info/` directory for technical details

### For Home Assistant
1. **Core files** remain in root for proper integration loading
2. **Manifest** and **strings** define integration metadata
3. **Platforms** (sensor.py) provide entity functionality

## 🔄 Maintenance

### Adding New Features
- Tests go in appropriate `tests/` subdirectory
- Documentation goes in appropriate `docs/` subdirectory
- Reference materials go in `info/`

### File Naming Conventions
- **Snake_case** for Python files
- **UPPER_CASE** for documentation files
- **Descriptive names** that indicate purpose
- **Directory organization** by function, not file type

### Git Management
- Core integration files tracked in root
- Organized structure makes diffs cleaner
- Easier to find and maintain specific functionality

---

This structure provides clear separation of concerns while maintaining Home Assistant integration requirements. 