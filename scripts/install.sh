#!/usr/bin/env bash
set -e

echo "--- BluPow Gateway Smart Installer ---"
echo ""

# --- Phase 1: Smart MQTT Broker Detection ---
echo "🔎 Checking for an existing BluPow MQTT broker..."

MQTT_CONTAINER_ID=$(docker ps -q -f name=blupow-mosquitto)
INSTALL_CHOICE=""
if [ -z "$MQTT_CONTAINER_ID" ]; then
    echo "ℹ️ No existing BluPow broker found. A new one will be created."
    INSTALL_CHOICE="1" # Quick Install
else
    echo "✔️ Found existing BluPow broker. The gateway will connect to it."
    INSTALL_CHOICE="2" # Custom Install (re-use existing)
fi

sleep 2 # Give user a moment to see the message

MQTT_CONNECT_HOST=""
GATEWAY_NETWORK_MODE="host" # Default to host

# --- Phase 2: Configure MQTT Broker (Automated) ---
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
    # --- Custom Install: Use the existing broker ---
    echo "🔗 Configuring gateway to use existing 'blupow-mosquitto' broker..."
    MQTT_CONNECT_HOST="blupow-mosquitto"
    # Ensure the gateway connects to the same network as the broker
    BROKER_NETWORK=$(docker inspect --format '{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}' "$MQTT_CONTAINER_ID")
    if [ -z "$BROKER_NETWORK" ]; then
        echo "⚠️ Warning: Could not determine network for existing broker. Defaulting to 'host' mode."
        GATEWAY_NETWORK_MODE="host"
    else
        echo "✔️ Found broker on network '$BROKER_NETWORK'."
        GATEWAY_NETWORK_MODE="$BROKER_NETWORK"
    fi
fi

echo "✔️ Gateway will connect to MQTT at '${MQTT_CONNECT_HOST}'."
echo ""

# --- Phase 3: Build and Launch BluPow Gateway ---
echo "🚀 Building the BluPow Gateway image... (This may take a few minutes)"
if ! docker build --no-cache -t blp-gateway:latest -f ./blupow_gateway/Dockerfile ./blupow_gateway; then
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
CONFIG_DIR="$HOME/blupow_config"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/devices.json" ]; then
    echo "   - Creating default devices.json at $CONFIG_DIR/devices.json"
    echo '{\n  "devices": []\n}' > "$CONFIG_DIR/devices.json"
fi
sudo chown -R "$USER":"$USER" "$CONFIG_DIR"

docker run -d \
    --name blupow-gateway \
    --network="$GATEWAY_NETWORK_MODE" \
    --restart=unless-stopped \
    --privileged \
    -e MQTT_BROKER_HOST="$MQTT_CONNECT_HOST" \
    -e MQTT_PORT="1883" \
    -e POLLING_INTERVAL_SECONDS="30" \
    -v "$CONFIG_DIR":/app/config \
    -v /var/run/dbus:/var/run/dbus \
    -v /run/dbus:/run/dbus:ro \
    blp-gateway:latest

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