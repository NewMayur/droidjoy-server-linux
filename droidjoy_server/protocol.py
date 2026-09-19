import struct
import logging
from .gamepad import VirtualGamepad

logger = logging.getLogger(__name__)

def parse_packet(data: bytes):
    """
    Parse a 13-byte DroidJoy packet.
    Format: [1 byte ASCII command] [4 bytes BE int32] [4 bytes BE int32] [4 bytes BE int32]
    Returns: (command: str, param1: int, param2: int, param3: int)
    """
    if len(data) < 13:
        return None
    try:
        cmd = chr(data[0])
        p1 = struct.unpack('>i', data[1:5])[0]
        p2 = struct.unpack('>i', data[5:9])[0]
        p3 = struct.unpack('>i', data[9:13])[0]
        return (cmd, p1, p2, p3)
    except Exception as e:
        logger.error("Error parsing packet: %s", e)
        return None

def dispatch(gamepad: VirtualGamepad, cmd: str, p1: int, p2: int, p3: int):
    """
    Dispatch a parsed packet command to the VirtualGamepad instance.
    """
    try:
        if cmd == 'b':    # button down
            gamepad.press_button(p1)
        elif cmd == 'f':  # button up
            gamepad.release_button(p1)
        elif cmd == 'l':  # left stick move
            gamepad.set_stick('left', p1, p2)
        elif cmd == 'r':  # right stick move
            gamepad.set_stick('right', p1, p2)
        elif cmd == 'g':  # left stick release
            gamepad.release_stick('left')
        elif cmd == 'h':  # right stick release
            gamepad.release_stick('right')
        elif cmd == 'p':  # DPad direction
            gamepad.set_pov(p1)
        elif cmd == 'o':  # DPad release
            gamepad.release_pov()
        else:
            logger.debug("Unknown command: %s", cmd)
            
        # Sync after every event as they come in batches or individually
        gamepad.sync()
    except Exception as e:
        logger.error("Error dispatching command %s: %s", cmd, e)
