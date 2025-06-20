# BluPow Container & Bluetooth Configuration Guide

This is the definitive guide for resolving Bluetooth connectivity issues when running the BluPow integration inside a Docker container. These issues almost always stem from the container's security policies (like AppArmor) preventing Home Assistant from accessing the host's Bluetooth hardware.

## 🔍 Step 1: Diagnose the Problem

First, confirm that you are facing a container security issue. Check your Home Assistant and system logs for these specific error messages:

```bash
# Check Home Assistant logs for D-Bus errors
docker logs homeassistant | grep -i "dbus"

# Check system logs for AppArmor denials
sudo dmesg | grep -i "apparmor" | grep -i "denied"
```

**If you see messages like these, you have a container security issue:**
- `[org.freedesktop.DBus.Error.AccessDenied] An AppArmor policy prevents this sender from sending this message`
- `apparmor="DENIED" operation="dbus_method_call"`

## 🛠️ Step 2: Choose Your Solution

Here are three common solutions, from easiest (but least secure) to most secure. For most users, **Option 2 is the recommended balance.**

---

### Option 1: Privileged Mode (The Easy Way)

This option gives the container full access to all host devices. It's the simplest way to solve the problem but reduces the security benefits of containerization.

**For `docker-compose.yml`:**
```yaml
services:
  homeassistant:
    # ... other config ...
    image: ghcr.io/home-assistant/home-assistant:stable
    privileged: true
    network_mode: host
    volumes:
      - /path/to/your/config:/config
      - /run/dbus:/run/dbus:ro
```

---

### Option 2: Specific Device Access (Recommended)

This is the preferred method. It grants the container access only to the necessary Bluetooth hardware and gives it the required network capabilities, without granting full privileged access.

**For `docker-compose.yml`:**
```yaml
services:
  homeassistant:
    # ... other config ...
    image: ghcr.io/home-assistant/home-assistant:stable
    # Note: No 'privileged: true'
    network_mode: host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    devices:
      # You may need to verify the exact path of your BT adapter
      - /dev/hci0:/dev/hci0
    volumes:
      - /path/to/your/config:/config
      - /run/dbus:/run/dbus:ro
```

---

### Option 3: Custom AppArmor Profile (Most Secure)

This is the most advanced option. It involves creating a custom security profile that grants the container the exact permissions it needs for Bluetooth and nothing more.

**1. Create the custom profile file:**
```bash
sudo nano /etc/apparmor.d/docker-homeassistant-bluetooth
```

**2. Paste in the following profile. This profile is tailored to allow D-Bus and Bluetooth operations:**
```c
#include <tunables/global>

profile docker-homeassistant-bluetooth flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/python>

  # Allow network access for Home Assistant
  network inet tcp,
  network inet udp,
  network inet icmp,
  network netlink raw,

  # Allow Bluetooth and D-Bus communication
  network netlink,
  dbus (send, receive) bus=system,
  dbus (send, receive) bus=session,

  # Allow access to necessary system files for Bluetooth
  file,
  /run/dbus/system_bus_socket rw,
  /run/udev/control rw,
  /sys/class/bluetooth/** r,
  /sys/devices/virtual/bluetooth/** r,
  /dev/rfkill rw,

  # Grant required capabilities
  capability net_admin,
  capability net_raw,
  capability dac_override,

  # Allow Python execution
  /usr/bin/python3 ix,
  /usr/local/bin/python3 ix,

  # Allow access to config and temp directories
  /config/** rwk,
  /tmp/** rwk,
}
```

**3. Load the new profile into AppArmor:**
```bash
sudo apparmor_parser -r -W /etc/apparmor.d/docker-homeassistant-bluetooth
```

**4. Update your `docker-compose.yml` to use the profile:**
```yaml
services:
  homeassistant:
    # ... other config ...
    image: ghcr.io/home-assistant/home-assistant:stable
    network_mode: host
    security_opt:
      - apparmor=docker-homeassistant-bluetooth # Use the new profile
    volumes:
      - /path/to/your/config:/config
      - /run/dbus:/run/dbus:ro
```

## ✅ Step 3: Restart and Verify

After applying your chosen solution, restart your Home Assistant container.
```bash
docker-compose up -d --force-recreate homeassistant
```
Once restarted, run the connection verification script again. It should now be able to connect successfully.
```bash
python3 scripts/verify_connection.py
```

This consolidated guide provides a robust and detailed approach to solving container-based Bluetooth issues, preserving the critical low-level knowledge required for effective troubleshooting.

## 🎯 Problem: AppArmor/Container Security Blocking Bluetooth

Your Home Assistant Docker container cannot access Bluetooth due to security restrictions. This guide provides multiple solutions to enable Bluetooth access while maintaining reasonable security.

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