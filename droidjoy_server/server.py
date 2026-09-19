import socket
import logging
import threading
from .gamepad import VirtualGamepad
from .discovery import DiscoveryResponder
from .protocol import parse_packet, dispatch

logger = logging.getLogger(__name__)

MAX_PLAYERS = 4

def handle_tcp_client(conn, client_ip: str, gamepads: dict, gamepads_lock: threading.Lock):
    """
    Handle the TCP connection from a DroidJoy client.
    Reads continuous stream, buffers, and processes 13-byte packets.
    """
    with gamepads_lock:
        if client_ip in gamepads:
            gamepads[client_ip].close()
        gamepads[client_ip] = VirtualGamepad()
        gamepad = gamepads[client_ip]
        
    logger.info("Player connected from %s (Total players: %d)", client_ip, len(gamepads))
    
    buffer = b''
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Connection closed by client
            
            buffer += data
            # Process as many 13-byte packets as we have
            while len(buffer) >= 13:
                packet = buffer[:13]
                buffer = buffer[13:]
                
                parsed = parse_packet(packet)
                if parsed:
                    cmd, p1, p2, p3 = parsed
                    dispatch(gamepad, cmd, p1, p2, p3)
    except Exception as e:
        logger.error("TCP client error (%s): %s", client_ip, e)
    finally:
        conn.close()
        with gamepads_lock:
            if client_ip in gamepads:
                gamepads[client_ip].close()
                del gamepads[client_ip]
        logger.info("Player disconnected from %s", client_ip)


def run_udp_receiver(gamepads: dict, stop_event: threading.Event, port: int):
    """
    Listens for UDP packets on the connectionPort.
    UDP packets contain joystick axes which are sent continuously for speed.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(1.0)
    
    logger.info("UDP data receiver listening on port %d", port)
    
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            client_ip = addr[0]
            
            # dict.get is atomic in python, safe to use without lock for reading
            gamepad = gamepads.get(client_ip)
            if gamepad and len(data) >= 13:
                parsed = parse_packet(data[:13])
                if parsed:
                    cmd, p1, p2, p3 = parsed
                    dispatch(gamepad, cmd, p1, p2, p3)
        except socket.timeout:
            continue
        except Exception as e:
            logger.error("UDP receiver error: %s", e)
            
    sock.close()


def serve(connection_port=4268, discovery_port=4269):
    """
    Main entrypoint for the server. Starts discovery, UDP, and TCP loops.
    """
    stop_event = threading.Event()
    gamepads = {}
    gamepads_lock = threading.Lock()
    
    # Start Discovery Thread
    discovery_thread = DiscoveryResponder(stop_event)
    discovery_thread.start()
    
    # Start UDP Receiver Thread
    udp_thread = threading.Thread(
        target=run_udp_receiver, 
        args=(gamepads, stop_event, connection_port),
        daemon=True
    )
    udp_thread.start()
    
    # Main TCP Accept Loop
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(('0.0.0.0', connection_port))
    tcp_sock.listen(MAX_PLAYERS)
    tcp_sock.settimeout(1.0)
    
    logger.info("TCP server listening on port %d", connection_port)
    logger.info("Waiting for DroidJoy apps to connect (Up to %d players)...", MAX_PLAYERS)
    
    threads = []
    
    try:
        while not stop_event.is_set():
            try:
                conn, addr = tcp_sock.accept()
            except socket.timeout:
                continue
                
            client_ip = addr[0]
            
            with gamepads_lock:
                if len(gamepads) >= MAX_PLAYERS and client_ip not in gamepads:
                    logger.warning("Max players reached. Rejecting connection from %s", client_ip)
                    conn.close()
                    continue
            
            # Disable Nagle's algorithm for lower latency
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Spawn a new thread for this client
            client_thread = threading.Thread(
                target=handle_tcp_client,
                args=(conn, client_ip, gamepads, gamepads_lock),
                daemon=True
            )
            client_thread.start()
            threads.append(client_thread)
            
            # Clean up dead threads
            threads = [t for t in threads if t.is_alive()]
                
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    finally:
        stop_event.set()
        tcp_sock.close()
        discovery_thread.join(timeout=2)
        udp_thread.join(timeout=2)
