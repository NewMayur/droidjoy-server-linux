# DroidJoy Linux Server

A custom Linux server for the DroidJoy Android app, allowing you to use your phone as a PC gamepad on Ubuntu/Linux.

## Features

- **Virtual Xbox 360 Controller**: Exposes native Linux `/dev/uinput` device mapped cleanly to standard Xbox 360 pad layouts.
- **Full Multiplayer Support**: Supports up to 4 concurrent players with dynamic client IP-based routing.
- **Low Latency**: TCP connection handling for discrete button events and fast UDP socket streaming for analog joysticks.
- **Automatic Discovery**: Responds to DroidJoy app broadcast discovery packets on UDP port 4269.

## Prerequisites

- Ubuntu/Linux
- Python 3.8+
- The `uinput` kernel module loaded

## One-time Setup

To allow the server to create virtual gamepads without running as root, configure `udev` rules:

```bash
sudo ./setup_udev.sh
```

*(You may need to log out and back in, or reboot for this to take effect)*

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Server

```bash
python3 -m droidjoy_server
```

Run with `--debug` for verbose button and axis event logs:

```bash
python3 -m droidjoy_server --debug
```

You can now open the DroidJoy app on your Android device and tap "Search Server". The Linux PC should appear in the list!

## How it Works

- Listens for UDP broadcasts on port `4269` and responds to discovery packets.
- Listens on TCP port `4268` for connection and discrete button events.
- Listens on UDP port `4268` for fast analog joystick events.
- Emulates an **Xbox 360 Controller** via Linux `/dev/uinput` using `python-evdev`.
