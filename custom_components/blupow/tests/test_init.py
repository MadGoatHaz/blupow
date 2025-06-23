import pytest
import json
from pytest_homeassistant_custom_component.common import (
    async_fire_mqtt_message,
    async_setup_component
)

@pytest.mark.asyncio
async def test_setup_and_discovery(hass, mqtt_mock):
    """Test that the integration sets up and discovers a device via MQTT."""
    # Setup our component
    await async_setup_component(hass, "blupow", {})

    # Publish a fake discovery message from our "gateway"
    discovery_topic = "homeassistant/sensor/blupow_aabbcc_battery/config"
    discovery_payload = {
        "name": "Test Battery",
        "unique_id": "blupow_aabbcc_battery",
        "state_topic": "blupow/aabbcc/state",
        "value_template": "{{ value_json.battery }}",
        "device": {
            "identifiers": ["blupow_aabbcc"],
            "name": "BluPow aabbcc",
            "manufacturer": "BluPow"
        }
    }
    async_fire_mqtt_message(hass, discovery_topic, json.dumps(discovery_payload))
    await hass.async_block_till_done()

    # Check that the entity was created
    state = hass.states.get("sensor.test_battery")
    assert state is not None
    assert state.name == "Test Battery"

    # Publish a state update
    state_topic = "blupow/aabbcc/state"
    state_payload = '{"battery": 95}'
    async_fire_mqtt_message(hass, state_topic, state_payload)
    await hass.async_block_till_done()

    # Check that the entity state was updated
    state = hass.states.get("sensor.test_battery")
    assert state.state == "95" 