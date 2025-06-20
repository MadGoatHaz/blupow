# BluPow Container Configuration Guide

## 🎯 Problem: AppArmor/Container Security Blocking Bluetooth

Your Home Assistant Docker container cannot access Bluetooth due to security restrictions. This guide provides multiple solutions to enable Bluetooth access while maintaining reasonable security.

## 🔍 Diagnosis: Confirm the Issue

First, verify this is your issue by checking for these error messages:

```bash
# Check Home Assistant logs
docker logs homeassistant | grep -i "apparmor\|access.*denied\|bluetooth"

# Check system logs for AppArmor denials
sudo dmesg | grep -i apparmor | grep -i denied
```

**Look for:**
- `[org.freedesktop.DBus.Error.AccessDenied] An AppArmor policy prevents this sender from sending this message`
- `apparmor="DENIED" operation="dbus_method_call"`
- `authentication failed: REJECTED: ['EXTERNAL']`

## 🛠️ Solution Options (Choose One)

### Option 1: Privileged Mode (Easiest, Less Secure)

**For Docker Run:**
```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Your/Timezone \
  -v /path/to/config:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

**For Docker Compose:**
```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    privileged: true
    restart: unless-stopped
    environment:
      - TZ=Your/Timezone
    volumes:
      - /path/to/config:/config
      - /run/dbus:/run/dbus:ro
    network_mode: host
```

### Option 2: Specific Device Access (More Secure)

**For Docker Run:**
```bash
docker run -d \
  --name homeassistant \
  --restart=unless-stopped \
  -e TZ=Your/Timezone \
  -v /path/to/config:/config \
  -v /run/dbus:/run/dbus:ro \
  --device /dev/bus/usb \
  --device /dev/ttyUSB0 \
  --device /dev/ttyACM0 \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

**For Docker Compose:**
```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    restart: unless-stopped
    environment:
      - TZ=Your/Timezone
    volumes:
      - /path/to/config:/config
      - /run/dbus:/run/dbus:ro
    devices:
      - /dev/bus/usb:/dev/bus/usb
      - /dev/ttyUSB0:/dev/ttyUSB0
      - /dev/ttyACM0:/dev/ttyACM0
    cap_add:
      - NET_ADMIN
      - NET_RAW
    network_mode: host
```

### Option 3: Custom AppArmor Profile (Most Secure)

**Step 1: Create Custom Profile**
```bash
sudo nano /etc/apparmor.d/docker-homeassistant-bluetooth
```

**Profile Content:**
```c
#include <tunables/global>

profile docker-homeassistant-bluetooth flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/python>

  # Network access
  network inet tcp,
  network inet udp,
  network inet icmp,
  network netlink raw,

  # Bluetooth and D-Bus access
  network netlink,
  dbus (send, receive) bus=system,
  dbus (send, receive) bus=session,

  # File system access
  file,
  /run/dbus/system_bus_socket rw,
  /run/udev/control rw,
  /sys/class/bluetooth/** r,
  /sys/devices/virtual/bluetooth/** r,
  /dev/rfkill rw,

  # Capabilities
  capability net_admin,
  capability net_raw,
  capability dac_override,
  capability setuid,
  capability setgid,

  # Python and Home Assistant
  /usr/bin/python3 ix,
  /usr/local/bin/python3 ix,
  /config/** rw,
  /tmp/** rw,

  # Deny dangerous operations
  deny @{PROC}/sys/kernel/core_pattern w,
  deny mount,
  deny umount,
}
```

**Step 2: Load the Profile**
```bash
sudo apparmor_parser -r -W /etc/apparmor.d/docker-homeassistant-bluetooth
```

**Step 3: Use the Profile**
```bash
docker run -d \
  --name homeassistant \
  --security-opt apparmor=docker-homeassistant-bluetooth \
  --restart=unless-stopped \
  -e TZ=Your/Timezone \
  -v /path/to/config:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

### Option 4: MacVLAN Network (Advanced)

**Step 1: Create MacVLAN Network**
```bash
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  macvlan_network
```

**Step 2: Docker Compose with MacVLAN**
```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    restart: unless-stopped
    environment:
      - TZ=Your/Timezone
    volumes:
      - /path/to/config:/config
      - /run/dbus:/run/dbus:ro
    networks:
      macvlan_network:
        ipv4_address: 192.168.1.100

networks:
  macvlan_network:
    external: true
```

## 🧪 Testing Your Configuration

After applying any solution, test with our diagnostic suite:

```bash
# Deploy BluPow with testing tools
./deploy.sh

# Run comprehensive Bluetooth testing
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/blupow_testing_suite.py
```

**Select option 6** for "Current Device Diagnostics" to test your specific Renogy device.

## 🔧 Troubleshooting

### Issue: Still Getting Access Denied
**Solution:** Try removing `/etc/subuid` and `/etc/subgid` files:
```bash
sudo rm /etc/subuid /etc/subgid
sudo systemctl restart docker
```

### Issue: Container Won't Start
**Solution:** Check AppArmor profile syntax:
```bash
sudo apparmor_parser -Q /etc/apparmor.d/docker-homeassistant-bluetooth
```

### Issue: Bluetooth Works But Integration Fails
**Solution:** Verify D-Bus service is running:
```bash
sudo systemctl status dbus
sudo systemctl status bluetooth
```

## 🚀 Implementation for BluPow Vision

Once Bluetooth is working, you can proceed with the automated setup vision:

### Phase 1: Validate Container Configuration
```bash
# Test Bluetooth access
docker exec -it homeassistant hcitool dev

# Test D-Bus connectivity  
docker exec -it homeassistant dbus-send --system --print-reply --dest=org.bluez / org.freedesktop.DBus.Introspectable.Introspect
```

### Phase 2: Deploy BluPow with Auto-Discovery
```bash
# Deploy with container configuration
./deploy.sh

# Run automated device discovery
docker exec -it homeassistant env PYTHONPATH=/config python3 /config/custom_components/blupow/device_discovery_system.py
```

### Phase 3: Enable HACS Integration Path
Once container Bluetooth is working:
1. **Test device discovery** with 15-second optimized scans
2. **Validate sensor creation** and Energy Dashboard integration
3. **Prepare HACS submission** with automated setup wizard

## 📋 Security Considerations

### Risk Levels:
1. **Privileged Mode**: High risk, but easiest setup
2. **Device Access**: Medium risk, good balance
3. **Custom AppArmor**: Low risk, most secure
4. **MacVLAN**: Low risk, network isolation

### Recommendations:
- **Home Users**: Use Option 2 (Device Access)
- **Advanced Users**: Use Option 3 (Custom AppArmor)
- **Production**: Use Option 3 or 4 with additional hardening

## 🎯 Success Criteria

After configuration, you should see:
- ✅ No AppArmor denial messages in logs
- ✅ Bluetooth integration loads successfully
- ✅ BluPow discovers your Renogy device
- ✅ Sensors populate in Home Assistant
- ✅ Energy Dashboard shows power data

## 🔄 Rollback Plan

If something goes wrong:

```bash
# Stop container
docker stop homeassistant

# Remove custom configurations
sudo rm /etc/apparmor.d/docker-homeassistant-bluetooth
sudo apparmor_parser -R /etc/apparmor.d/docker-homeassistant-bluetooth

# Restart with basic configuration
docker run -d --name homeassistant --privileged --network=host -v /path/to/config:/config ghcr.io/home-assistant/home-assistant:stable
```

---

**Next Steps:** Choose your preferred option and follow the implementation steps. Once Bluetooth is working, return to the main BluPow setup to enable automated device discovery and Energy Dashboard integration. 