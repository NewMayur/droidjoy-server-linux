import logging
from evdev import UInput, AbsInfo, ecodes as e

logger = logging.getLogger(__name__)

# Map DroidJoy button IDs to evdev EV_KEY codes
BUTTON_MAP = {
    1: e.BTN_A,
    2: e.BTN_B,
    3: e.BTN_X,
    4: e.BTN_Y,
    5: e.BTN_TL,          # Left Bumper (User's L button, ID 5)
    6: e.BTN_TR,          # Right Bumper (User's R button, ID 6)
    7: e.BTN_SELECT,      # Back / Menu - User's left oval button (ID 7)
    8: e.BTN_START,       # Start - User's right oval button (ID 8)
    9: None,              
    10: None,             
    11: None,             # Left Trigger (User's V+, ID 11) - Handled in code
    12: None,             # Right Trigger (User's V-, ID 12) - Handled in code
}

# Map DroidJoy POV ordinals to (HAT0X, HAT0Y) directions
POV_MAP = {
    0: (0, -1),   # UP
    1: (1, 0),    # RIGHT
    2: (0, 1),    # DOWN
    3: (-1, 0),   # LEFT
    4: (1, -1),   # UP_RIGHT
    5: (1, 1),    # DOWN_RIGHT
    6: (-1, 1),   # DOWN_LEFT
    7: (-1, -1),  # UP_LEFT
}

class VirtualGamepad:
    def __init__(self):
        # Define the capabilities of our virtual Xbox 360 controller
        cap = {
            e.EV_KEY: [
                e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y,
                e.BTN_TL, e.BTN_TR, e.BTN_SELECT, e.BTN_START,
                e.BTN_MODE, e.BTN_THUMBL, e.BTN_THUMBR
            ],
            e.EV_ABS: [
                (e.ABS_X, AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)),
                (e.ABS_Y, AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)),
                (e.ABS_RX, AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)),
                (e.ABS_RY, AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)),
                (e.ABS_Z, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RZ, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0X, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0Y, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
            ]
        }
        
        # Identity for an Xbox 360 controller
        self.ui = UInput(
            events=cap,
            name="Microsoft X-Box 360 pad",
            vendor=0x045e,
            product=0x028e,
            version=0x0114,
            bustype=e.BUS_USB
        )
        logger.info("Virtual Gamepad created: %s", self.ui.device)

    def close(self):
        if self.ui:
            self.ui.close()
            self.ui = None
            logger.info("Virtual Gamepad destroyed")

    def press_button(self, button_id: int):
        logger.info("Button pressed on phone: ID %d", button_id)
        # Triggers are analog
        if button_id == 11:
            self.ui.write(e.EV_ABS, e.ABS_Z, 255)
        elif button_id == 12:
            self.ui.write(e.EV_ABS, e.ABS_RZ, 255)
        else:
            evdev_code = BUTTON_MAP.get(button_id)
            if evdev_code is not None:
                self.ui.write(e.EV_KEY, evdev_code, 1)

    def release_button(self, button_id: int):
        if button_id == 11:
            self.ui.write(e.EV_ABS, e.ABS_Z, 0)
        elif button_id == 12:
            self.ui.write(e.EV_ABS, e.ABS_RZ, 0)
        else:
            evdev_code = BUTTON_MAP.get(button_id)
            if evdev_code is not None:
                self.ui.write(e.EV_KEY, evdev_code, 0)

    def set_pov(self, direction_ordinal: int):
        vec = POV_MAP.get(direction_ordinal)
        if vec:
            self.ui.write(e.EV_ABS, e.ABS_HAT0X, vec[0])
            self.ui.write(e.EV_ABS, e.ABS_HAT0Y, vec[1])

    def release_pov(self):
        self.ui.write(e.EV_ABS, e.ABS_HAT0X, 0)
        self.ui.write(e.EV_ABS, e.ABS_HAT0Y, 0)

    def set_stick(self, stick: str, x: int, y: int):
        def clamp16(val):
            return max(-32768, min(32767, val))
            
        # DroidJoy app sends sticks normalized to [0, 32768] with center at 16384
        # We shift by -16384 and multiply by 2 to get the full [-32768, 32767] evdev range
        mapped_x = clamp16((x - 16384) * 2)
        mapped_y = clamp16((y - 16384) * 2)
        
        if stick == 'left':
            self.ui.write(e.EV_ABS, e.ABS_X, mapped_x)
            self.ui.write(e.EV_ABS, e.ABS_Y, mapped_y)
        elif stick == 'right':
            self.ui.write(e.EV_ABS, e.ABS_RX, mapped_x)
            self.ui.write(e.EV_ABS, e.ABS_RY, mapped_y)

    def release_stick(self, stick: str):
        if stick == 'left':
            self.ui.write(e.EV_ABS, e.ABS_X, 0)
            self.ui.write(e.EV_ABS, e.ABS_Y, 0)
        elif stick == 'right':
            self.ui.write(e.EV_ABS, e.ABS_RX, 0)
            self.ui.write(e.EV_ABS, e.ABS_RY, 0)

    def sync(self):
        self.ui.syn()
