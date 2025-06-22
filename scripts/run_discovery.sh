#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/custom_components/blupow
python3 scripts/blupow_device_discovery.py
