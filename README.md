# ha-dreame-vacuum

A simple Home Assistant custom component for the **Dreame L10s Ultra Gen 2** robot vacuum, using the Dreame cloud API directly.

> ⚠️ **Model-specific:** This integration was built and tested exclusively on the **Dreame L10s Ultra Gen 2** (`dreame.vacuum.r2469a`). It may work on other Dreame cloud-account models, but this has not been tested and is not guaranteed.

---

## What This Is (and What It Isn't)

This is an intentionally **simple, honest integration**. It does one thing well: exposes your vacuum's status, sensors, and shortcuts to Home Assistant in a clean way that works great with [vacuum-card](https://github.com/denysdovhan/vacuum-card).

### ✅ What it does

- Connects to your Dreame cloud account (no local token needed)
- Exposes battery, status, consumable life, clean history as sensors
- Exposes shortcuts you've configured in the Dreame app as pressable buttons
- Provides a full `vacuum.*` entity compatible with vacuum-card
- Handles authentication and token refresh automatically

### ❌ What it does NOT do

- **No map support** — no room layout, zone display, or live map streaming
- **No room-by-room triggering** — you cannot target specific rooms directly from HA
- **No advanced cleaning modes** — no zone cleaning, spot cleaning, or segment selection via HA
- **Shortcuts are the action mechanism** — if you want custom cleaning routines (specific rooms, specific settings), configure them as shortcuts in the Dreame app first, then trigger those shortcuts from HA

> 💡 **The shortcuts approach is intentional.** Configure your cleaning routines (rooms, suction level, mop settings) directly in the Dreame app where you have the full UI, then expose them as one-tap shortcuts in HA. This keeps the integration simple and reliable.

### Controlling Individual Rooms

This integration does **not** support targeting individual rooms directly — there is no room map, no segment IDs, and no room-selection API exposed.

**The recommended approach is shortcuts:**

1. Open the **Dreame app** on your phone
2. Create a shortcut for each room you want to control (e.g. "Kitchen", "Living Room", "Bedrooms")
3. Configure each shortcut with the exact rooms, suction level, and mop settings you want
4. Those shortcuts will automatically appear as **button entities** in HA when the integration loads
5. Trigger them from automations, dashboards, or voice assistants like any other HA button

This way you get full per-room control with all the power of the Dreame app's room editor, and HA just triggers the run.

---

## Tested With

- ✅ **Dreame L10s Ultra Gen 2** (`dreame.vacuum.r2469a`) — Dreamehome account, Singapore region
- ❓ Other Dreame models with Dreamehome accounts — untested, may work
- ❌ Xiaomi/Mi Home account vacuums — not supported
- ❌ Mova/Trouver account vacuums — not tested

---

## Works Great With vacuum-card

This integration pairs perfectly with [vacuum-card](https://github.com/denysdovhan/vacuum-card) for Lovelace. Install vacuum-card via HACS, then drop the YAML below straight into your dashboard — no template entities needed.

---

## Installation

### HACS (recommended)

1. Add `https://github.com/sammysbot87/ha-dreame-vacuum` as a custom repository in HACS (Integration category)
2. Install **Dreame Vacuum Cloud**
3. Restart Home Assistant

### Manual

1. Copy `custom_components/dreame_cloud/` to your HA `custom_components/` folder
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Dreame Vacuum Cloud**
3. Enter your **Dreamehome username and password**
4. Select your region (default: `sg` for Australia/Singapore)
5. Your device will be auto-discovered and configured

---

## Entities

### Vacuum

| Entity | Description |
|--------|-------------|
| `vacuum.l10s_ultra_gen_2` | Main vacuum entity — use this with vacuum-card |

**Supported services:** `start`, `pause`, `stop`, `return_to_base`, `locate`, `set_fan_speed`, `send_command`

**Vacuum attributes** (all available via `attribute:` in vacuum-card stats):

| Attribute | Description |
|-----------|-------------|
| `status` | Friendly status string |
| `battery_level` | Battery % |
| `battery_icon` | MDI battery icon |
| `fan_speed` | Current suction level |
| `last_clean_time` | Last session duration (minutes) |
| `last_clean_area` | Last session area (m²) |
| `total_clean_time` | Lifetime clean time (minutes) |
| `total_clean_time_hours` | Lifetime clean time (hours) |
| `total_clean_area` | Lifetime cleaned area (m²) |
| `main_brush_life` | Main brush % remaining |
| `side_brush_life` | Side brush % remaining |
| `filter_life` | Filter % remaining |
| `mop_pad_life` | Mop pad % remaining |
| `sensor_cleanliness` | Sensor cleanliness % |
| `task_status` | Current task type |
| `charging_status` | Charging state |
| `water_volume` | Water volume (mop) |
| `mop_in_station` | Mop currently in wash station |
| `mop_pad_installed` | Mop pad fitted on robot |
| `self_wash_base_status` | Wash base state (idle/washing/drying) |
| `error` | Current error description (null if none) |

### Sensors

| Entity | Description |
|--------|-------------|
| Battery | Battery % |
| Status | Device state (sleeping, cleaning, charging, etc.) |
| Charging Status | not_charging / charging / returning |
| Task Status | Current task type |
| Last Clean Duration | Minutes |
| Last Clean Area | m² |
| Total Clean Time | Lifetime minutes |
| Total Cleaned Area | Lifetime m² |
| Suction Level | quiet / standard / strong / turbo |
| Water Volume | off / low / medium / high |
| Error | Current error description |
| Main Brush Life | % remaining |
| Side Brush Life | % remaining |
| Filter Life | % remaining |
| Sensor Cleanliness | % remaining |
| Mop Pad Life | % remaining |
| Available Shortcuts | List of shortcut names and IDs |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| Charging | On when charging |
| Cleaning | On when any cleaning activity is active |
| Mop Pad Installed | On when mop pad is fitted |
| Mop in Station | On when mop is in the wash station |

### Buttons

| Entity | Description |
|--------|-------------|
| Pause | Pause current task |
| Stop | Stop current task |
| Return to Dock | Send robot home |
| Shortcut: \<name\> | One button per shortcut configured in the Dreame app |

---

## vacuum-card YAML

```yaml
type: custom:vacuum-card
entity: vacuum.l10s_ultra_gen_2
battery_entity: sensor.l10s_ultra_gen_2_battery
show_name: true
show_status: true
show_toolbar: true  # start / pause / stop / dock / locate buttons per state

stats:
  default:  # shown when docked or idle
    - attribute: main_brush_life
      unit: "%"
      subtitle: Main Brush
    - attribute: side_brush_life
      unit: "%"
      subtitle: Side Brush
    - attribute: filter_life
      unit: "%"
      subtitle: Filter
    - attribute: mop_pad_life
      unit: "%"
      subtitle: Mop Pad
  cleaning:  # shown while cleaning
    - attribute: last_clean_time
      unit: min
      subtitle: Duration
    - attribute: last_clean_area
      unit: m²
      subtitle: Area
  docked:  # shown while charging
    - attribute: total_clean_area
      unit: m²
      subtitle: Total Area
    - attribute: total_clean_time_hours
      unit: h
      subtitle: Total Time
    - attribute: main_brush_life
      unit: "%"
      subtitle: Main Brush
    - attribute: filter_life
      unit: "%"
      subtitle: Filter

shortcuts:
  - name: Weekend Vacuum
    service: button.press
    target:
      entity_id: button.l10s_ultra_gen_2_shortcut_weekend_vacuum
    icon: mdi:sofa
  - name: Bathrooms
    service: button.press
    target:
      entity_id: button.l10s_ultra_gen_2_shortcut_bathrooms_vac_and_mop
    icon: mdi:shower
```

> All stats use `attribute:` pointing directly to the vacuum entity — no separate sensor entities needed for the card display.

---

## Automations

Trigger a shortcut from an automation using the auto-created button entities:

```yaml
action:
  - service: button.press
    target:
      entity_id: button.l10s_ultra_gen_2_shortcut_bathrooms_vac_and_mop
```

Or via `send_command` if you prefer to reference shortcuts by ID:

```yaml
service: vacuum.send_command
target:
  entity_id: vacuum.l10s_ultra_gen_2
data:
  command: shortcut
  params:
    id: 33  # Bathrooms vac and mop
```

---

## Notes

- **No local token needed** — Dreame cloud accounts communicate via cloud MQTT. This integration uses the same cloud API as the Dreame app.
- **Poll interval:** 30 seconds
- **Token refresh:** Automatic. Access tokens expire every 2 hours and are refreshed silently. Refresh tokens last ~90 days, after which the integration re-authenticates using your stored password.

---

## License

MIT
