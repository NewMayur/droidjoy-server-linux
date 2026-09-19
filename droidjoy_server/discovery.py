import socket
import logging
import threading

logger = logging.getLogger(__name__)

class DiscoveryResponder(threading.Thread):
    """
    Listens for UDP broadcast packets from the DroidJoy app and responds to them.
    The app sends '27' to port 4269 (broadcastPort) and expects a reply on port 4268 (connectionPort).
    """
    def __init__(self, stop_event: threading.Event):
        super().__init__()
        self.stop_event = stop_event
        self.daemon = True
        
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow reusing the address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', 4269))
        except Exception as e:
            logger.error("Failed to bind discovery socket on port 4269: %s", e)
            return

        sock.settimeout(1.0)
        logger.info("Discovery responder listening on UDP 0.0.0.0:4269")

        while not self.stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                if data == b'27':
                    logger.debug("Received discovery broadcast from %s", addr)
                    # Reply with arbitrary string to the sender's IP on port 4268
                    sock.sendto(b'DROIDJOY_SERVER', (addr[0], 4268))
            except socket.timeout:
                pass
            except Exception as e:
                logger.error("Error in discovery responder: %s", e)

        sock.close()
        logger.info("Discovery responder stopped.")
