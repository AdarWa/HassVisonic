# Visonic PowerLink Home Assistant Integration

This is a custom Home Assistant integration for Visonic alarm systems using the **Visonic PowerLink** REST API. It provides access to alarm panel information and connected sensors, while optionally supporting fast and offline sensor state updates via **RS232-to-TCP converters** like the USR-TCP232-T2.

---

## Features

- Full integration with **Visonic PowerLink** REST API.
- Fetch sensor data including:
  - Name, type, bypassed state, tamper alerts, and warnings.
- Support for **arming/disarming with multiple codes**.
- Optional support for **RS232-to-TCP converters** (e.g. USR-TCP232-T2):
  - Allows **faster updates** of the alarm state.
  - Works **offline** if PowerLink is unavailable.
  - Supports **one "rapid sensor"**, ideal for doors/windows.
- Easy setup via Home Assistant **GUI Config Flow**.
- Installable through [HACS](https://hacs.xyz) as a **custom repository**.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Optional: RS232-to-TCP Support](#optional-rs232-to-tcp-support)
- [Services](#services)
- [Events](#events)
- [Contributions](#contributions)
- [License](#license)

---

## Installation

1. Install [HACS](https://hacs.xyz/) in your Home Assistant setup.
2. Add this repository as a **custom integration**:
   - Go to HACS → Integrations → Menu (three dots) → Custom repositories.
   - URL: `https://github.com/AdarWa/HassVisonic`
   - Category: Integration.
3. Install the `Visonic Integration` integration from the list.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services**, click **Add Integration**, and search for `Visonic`.

---

## Configuration

Setup is fully GUI-based. When prompted, provide the following:

| Field | Description |
|-------|-------------|
| `hostname` | Hostname of the alarm provider |
| `email` | Email used to log into PowerLink |
| `password` | PowerLink password |
| `user_code` | Code used to arm/disarm the system |
| `panel_serial` | The panel's serial number |
| `valid_codes` | Comma-separated list of valid codes allowed for arming (can include `user_code`) |

> **Note**: If you want to use a USR-TCP232-T2 (or similar) device for faster updates, you can do so without removing the PowerLink. However, it is entirely optional.

---

## Optional: RS232-to-TCP Support

You can connect an RS232-to-TCP converter like **USR-TCP232-T2** to the panel for:

- **Faster alarm state updates**
- **Offline status updates** when PowerLink is unreachable
- **One "rapid sensor"**, ideal for fast response times

> ⚠️ Only **one rapid sensor** can be used in this mode.

---

## Services

This integration exposes the following **services** in Home Assistant:

| Service | Description |
|--------|-------------|
| `visonic_hass.update` | Manually fetch the latest alarm and sensor state |
| `visonic_hass.trigger_siren` | Activate the alarm siren |
| `visonic_hass.mute_siren` | Mute the alarm siren |
| `visonic_hass.continue_action` | **Must be called after arming/disarming** to continue the action |

### ⚠️ Important: `continue_action` Required

You **must call `visonic_hass.continue_action`** using an automation or script **after** receiving any of the following events:

- `visonic.arm_home`
- `visonic.arm_away`
- `visonic.arm_vacation`
- `visonic.disarm`

This is required to complete the action on the alarm panel. You can use an automation to perform any pre-arm actions and then follow it with `continue_action`.

#### Example Automation:
```yaml
alias: Example Pre Arm Actions
description: ""
triggers:
  - trigger: event
    event_type: visonic.disarm
  - trigger: event
    event_type: visonic.arm_home
  - trigger: event
    event_type: visonic.arm_away
  - trigger: event
    event_type: visonic.arm_vacation
conditions: []
actions:
  - action: visonic_hass.continue_action
    metadata: {}
    data: {}
mode: single
```

---

## Events

The integration emits several events:

| Event | Description |
|-------|-------------|
| `visonic.invalid_code` | Triggered when a user enters an invalid code |
| `visonic.disarm` | Emitted when the system is queued to be disarmed |
| `visonic.arm_home` | Emitted when the system is queued to be armed in "home" mode |
| `visonic.arm_away` | Emitted when the system is queued to be armed in "away" mode |
| `visonic.arm_vacation` | Emitted when the system is queued to be armed in "vacation" mode |

Use these events to build automations, notify users, or log activity.

### Alarm Ready State

The integration provides an `alarm.ready` state attribute, which indicates whether the alarm system is ready to be armed. When `alarm.ready` is `True`, all sensors are in a secure state and the system can be armed. If `alarm.ready` is `False`, one or more sensors may be open, bypassed, or in a fault state, preventing arming until resolved.

---

## Contributions

Feel free to open issues or pull requests to improve this integration. Suggestions and enhancements are welcome!

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
