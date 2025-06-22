#!/usr/bin/env bash
set -e

echo "--- BluPow Standalone Gateway Installer ---"
echo ""

# --- Phase 1: Choose Installation Type ---
echo -e "🔧 How would you like to set up your MQTT broker?
   \e[1m[1] Quick Install:\e[0m Let BluPow set up a new, dedicated Mosquitto MQTT broker. (Recommended)
   \e[1m[2] Custom Install:\e[0m Connect to your own existing MQTT broker."

read -p "Enter your choice [1/2]: " INSTALL_CHOICE

while [[ "$INSTALL_CHOICE" != "1" && "$INSTALL_CHOICE" != "2" ]]; do
    echo "❌ Invalid input. Please enter 1 or 2."
    read -p "Enter your choice [1/2]: " INSTALL_CHOICE
done

MQTT_CONNECT_HOST=""
GATEWAY_NETWORK_MODE="host" # Default to host

# --- Phase 2: Configure MQTT Broker ---
if [ "$INSTALL_CHOICE" == "1" ]; then
    # --- Quick Install: Setup a new BluPow-managed broker ---
    echo "🚀 Performing Quick Install..."
    BROKER_DIR="$HOME/blupow_broker"
    echo "   - Creating dedicated directory for broker data at $BROKER_DIR"
    # Ensure directory exists and we own it before writing to it
    mkdir -p "$BROKER_DIR"
    sudo chown -R "$USER":"$USER" "$BROKER_DIR"
    mkdir -p "$BROKER_DIR/config"
    mkdir -p "$BROKER_DIR/data"
    mkdir -p "$BROKER_DIR/log"

    echo "   - Generating Mosquitto configuration..."
    cat << EOF > "$BROKER_DIR/config/mosquitto.conf"
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
allow_anonymous true
listener 1883
EOF

    echo "   - Setting correct permissions for broker data..."
    sudo chown -R 1883:1883 "$BROKER_DIR"

    echo "   - Creating dedicated docker network 'blupow-net'..."
    docker network create blupow-net >/dev/null 2>&1 || true

    echo "   - Stopping and removing any old blupow-mosquitto container..."
    if [ "$(docker ps -a -q -f name=blupow-mosquitto)" ]; then
        docker stop blupow-mosquitto >/dev/null 2>&1 || true
        docker rm blupow-mosquitto >/dev/null 2>&1 || true
    fi

    echo "   - Pulling latest Mosquitto image..."
    docker pull eclipse-mosquitto:latest

    echo "   - Launching new 'blupow-mosquitto' container..."
    docker run -d \
        --name blupow-mosquitto \
        --network=blupow-net \
        --restart=unless-stopped \
        -v "$BROKER_DIR/config":/mosquitto/config \
        -v "$BROKER_DIR/data":/mosquitto/data \
        -v "$BROKER_DIR/log":/mosquitto/log \
        eclipse-mosquitto:latest

    MQTT_CONNECT_HOST="blupow-mosquitto"
    GATEWAY_NETWORK_MODE="blupow-net"
    echo "✔️ Successfully launched BluPow-managed MQTT broker."

else
    # --- Custom Install: Use an existing broker ---
    echo "🔎 Performing Custom Install..."
    echo "   - This script will attempt to find your Home Assistant instance to join its network."
    # Find Home Assistant Container & Network
    HA_CONTAINER_ID=$(docker ps -q --filter "name=^/homeassistant$")
    if [ -z "$HA_CONTAINER_ID" ]; then
        echo "⚠️ Warning: Could not find a running container named 'homeassistant'."
        echo "   - The gateway will be deployed on the 'bridge' network by default."
        HA_NETWORK="bridge"
    else
        HA_NETWORK=$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$HA_CONTAINER_ID")
        echo "✔️ Found Home Assistant on network '$HA_NETWORK'."
    fi

    while [ -z "$MQTT_CONNECT_HOST" ]; do
        echo "❌ Broker address cannot be empty."
        read -p "   - Please enter the hostname or IP address of your existing MQTT broker: " MQTT_CONNECT_HOST
    done
fi

echo "✔️ Gateway will connect to MQTT at '${MQTT_CONNECT_HOST}'."
echo ""

# --- Phase 3: Build and Launch BluPow Gateway ---
echo "🚀 Building the BluPow Gateway image... (This may take a few minutes)"
if ! docker build --no-cache -t blupow-gateway:latest -f ./blupow_addon/Dockerfile .; then
    echo "❌ Error: Failed to build the Docker image."
    exit 1
fi
echo "✔️ Gateway image built successfully."

# Stop and remove any old gateway container
if [ "$(docker ps -a -q -f name=blupow-gateway)" ]; then
    echo "🗑️ Removing old blupow-gateway container..."
    docker stop blupow-gateway >/dev/null 2>&1 || true
    docker rm blupow-gateway >/dev/null 2>&1 || true
fi

echo "🚀 Launching the BluPow Gateway container..."

# Create a config directory if it doesn't exist to ensure correct permissions
mkdir -p ./blupow_addon/config

docker run -d \
    --name blupow-gateway \
    --network="$GATEWAY_NETWORK_MODE" \
    --restart=unless-stopped \
    --privileged \
    -e MQTT_BROKER="$MQTT_CONNECT_HOST" \
    -e MQTT_PORT="1883" \
    -e POLLING_INTERVAL_SECONDS="30" \
    -v ./blupow_addon/config:/app/config \
    -v /var/run/dbus:/var/run/dbus \
    -v /run/dbus:/run/dbus:ro \
    blupow-gateway:latest

echo ""
echo "🎉 Success! The BluPow Gateway is now running."
echo "   - It is configured to use the '${MQTT_CONNECT_HOST}' MQTT broker."
echo "   - You can view gateway logs with: docker logs -f blupow-gateway"
if [ "$INSTALL_CHOICE" == "1" ]; then
    echo "   - You can view broker logs with: docker logs -f blupow-mosquitto"
fi
echo ""
echo "--- FINAL STEP ---"
echo "Please go to your Home Assistant UI -> Settings -> Devices & Services."
echo "Click '+ Add Integration' and search for 'BluPow'."
echo "------------------" 