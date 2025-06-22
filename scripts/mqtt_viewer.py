#!/usr/bin/env python3
"""
A simple MQTT client to subscribe to a topic and print messages.
Useful for debugging and monitoring MQTT traffic.
"""
import argparse
import time
from paho.mqtt import client as mqtt_client

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(userdata['topic'])
        print(f"👂 Subscribed to topic: {userdata['topic']}")
    else:
        print(f"❌ Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

def on_subscribe(client, userdata, mid, granted_qos):
    """Callback for when the client subscribes to a topic."""
    print(f"✅ Subscribed with MID {mid} and QoS {granted_qos}")

def main():
    """Main function to setup and run the MQTT client."""
    parser = argparse.ArgumentParser(description="BluPow MQTT Data Viewer")
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='blupow/#', help='MQTT topic to subscribe to')
    parser.add_argument('--username', help='MQTT username')
    parser.add_argument('--password', help='MQTT password')
    args = parser.parse_args()

    client_id = f'blupow-viewer-{int(time.time())}'
    
    userdata = {'topic': args.topic}
    
    # Use MQTTv3.1.1 for maximum compatibility
    client = mqtt_client.Client(client_id=client_id, userdata=userdata)

    if args.username:
        client.username_pw_set(args.username, args.password)
        
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    print(f"🔌 Connecting to broker at {args.broker}:{args.port}...")
    try:
        client.connect(args.broker, args.port)
    except Exception as e:
        print(f"❌ Error connecting to broker: {e}")
        print("   Please check if the broker address is correct and that it is running.")
        return

    client.loop_forever()

if __name__ == '__main__':
    main() 