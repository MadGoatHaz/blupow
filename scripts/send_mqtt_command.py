#!/usr/bin/env python3
"""
A simple MQTT client to publish a single command message.
"""
import argparse
import json
import time
from paho.mqtt import client as mqtt_client

def main():
    """Main function to setup and run the MQTT client."""
    parser = argparse.ArgumentParser(description="BluPow MQTT Command Sender")
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='blupow/command', help='MQTT topic to publish to')
    parser.add_argument('--username', help='MQTT username')
    parser.add_argument('--password', help='MQTT password')
    parser.add_argument('--command', required=True, help='Command to send (e.g., add_device)')
    parser.add_argument('--address', required=True, help='Device MAC address')
    parser.add_argument('--type', help='Device type (e.g., inverter)')
    
    args = parser.parse_args()

    client_id = f'blupow-sender-{int(time.time())}'
    
    # Use MQTTv3.1.1 for maximum compatibility
    client = mqtt_client.Client(client_id=client_id)

    if args.username:
        client.username_pw_set(args.username, args.password)
        
    print(f"🔌 Connecting to broker at {args.broker}:{args.port}...")
    try:
        client.connect(args.broker, args.port)
    except Exception as e:
        print(f"❌ Error connecting to broker: {e}")
        return

    payload = {
        "command": args.command,
        "address": args.address,
    }
    if args.type:
        payload["type"] = args.type

    json_payload = json.dumps(payload)

    client.loop_start()
    print(f"⬆️  Publishing message to topic '{args.topic}':")
    print(f"   {json_payload}")
    result = client.publish(args.topic, json_payload)
    status = result.rc
    if status == 0:
        print("✅ Message sent successfully")
    else:
        print(f"❌ Failed to send message, return code {status}")
    
    # Give the client a moment to send the message before disconnecting
    time.sleep(1) 

    client.loop_stop()
    client.disconnect()

if __name__ == '__main__':
    main() 