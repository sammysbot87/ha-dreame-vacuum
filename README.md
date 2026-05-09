# ha-dreame-vacuum

A Home Assistant custom component for **Dreame robot vacuums** using the Dreame cloud API directly — no local token required.

Works with Dreamehome account logins (the native Dreame app).

## Features

- 🔋 **Sensors:** Battery, charging status, device status, last clean duration & area, lifetime totals, all consumable life percentages, error state, shortcut list
- 🔌 **Binary sensors:** Charging, cleaning active, mop installed, mop in station
- ⚡ **Buttons:** Pause, Stop, Return to Dock, and **one button per shortcut** (auto-discovered from your account)
- 🔐 **Authentication:** Full OAuth login via Dreamehome credentials — tokens auto-refresh, no secrets hardcoded
- 🔄 **Token persistence:** Access + refresh tokens saved to config entry, refreshed automatically every 2h

## Tested with

- Dreame L10s Ultra Gen 2 (`dreame.vacuum.r2469a`)

Should work with any Dreame cloud account vacuum (Dreamehome app). Mova/Trouver accounts not tested.

## Installation

### HACS (recommended)

1. Add this repo as a custom repository in HACS (Integration category)
2. Install **Dreame Vacuum Cloud**
3. Restart Home Assistant

### Manual

1. Copy `custom_components/dreame_cloud/` to your HA `custom_components/` folder
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Dreame Vacuum Cloud**
3. Enter your **Dreamehome username and password**
4. Select your region (default: `sg` for Australia/Singapore)
5. Your device will be auto-discovered

## Entities

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
| Shortcut: \<name\> | One button per configured shortcut |

## Notes

- **No local token needed** — Dreame cloud accounts (Dreamehome app) communicate via cloud MQTT. This integration uses the same cloud API the app uses.
- **Poll interval:** 30 seconds by default
- **Refresh token validity:** ~90 days. After expiry the integration will re-login using your stored password automatically.

## License

MIT
