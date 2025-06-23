import asyncio
import json
import time
import pytest
import subprocess
import os
import aiomqtt
import socket

COMPOSE_FILE = 'docker-compose.integration.yml'

@pytest.fixture(scope="module")
def gateway_stack():
    """
    Starts and stops the docker-compose stack for integration tests,
    ensuring the MQTT broker is ready before tests run.
    """
    compose_file_path = os.path.join(os.path.dirname(__file__), COMPOSE_FILE)
    try:
        subprocess.run(
            ["docker", "compose", "-f", compose_file_path, "up", "-d", "--build"],
            check=True,
            capture_output=True,
            text=True
        )

        # --- Readiness Check ---
        broker_ready = False
        attempts = 0
        max_attempts = 10
        
        while not broker_ready and attempts < max_attempts:
            try:
                # Attempt to connect to the broker
                conn = socket.create_connection(("localhost", 1884), timeout=2)
                conn.close()
                broker_ready = True
                print("MQTT Broker is ready.")
            except (socket.timeout, ConnectionRefusedError):
                print("Waiting for MQTT broker...")
                time.sleep(2)
                attempts += 1
        
        if not broker_ready:
            raise RuntimeError("MQTT broker did not become ready in time.")
            
        yield

    finally:
        # Stop and remove the containers
        subprocess.run(
            ["docker", "compose", "-f", compose_file_path, "down"],
            check=True,
            capture_output=True,
            text=True
        )

@pytest.mark.integration
async def test_gateway_publishes_discovery_on_startup(gateway_stack):
    """
    Connects to the MQTT broker and verifies that the gateway publishes a
    gateway status message on startup.
    """
    status_topic = "blupow/gateway/status"
    status_message_received = asyncio.Event()
    received_payload = None

    async def listen():
        nonlocal received_payload
        async with aiomqtt.Client("localhost", 1884) as client:
            await client.subscribe(status_topic)
            async for message in client.messages:
                if message.topic.matches(status_topic):
                    received_payload = json.loads(message.payload.decode())
                    status_message_received.set()
                    break # We got what we needed

    try:
        await asyncio.wait_for(listen(), timeout=10) # Shorter timeout, should be fast
    except asyncio.TimeoutError:
        pytest.fail("Test timed out waiting for gateway status message.")

    assert received_payload is not None
    assert received_payload.get("state") == "online"
    assert "version" in received_payload 