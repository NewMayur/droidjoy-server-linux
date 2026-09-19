import argparse
import logging
import sys
from .server import serve

def main():
    parser = argparse.ArgumentParser(description="DroidJoy Linux Server")
    parser.add_argument("--tcp-port", type=int, default=4268, help="TCP connection and UDP data port (default: 4268)")
    parser.add_argument("--discovery-port", type=int, default=4269, help="UDP discovery broadcast port (default: 4269)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout
    )
    
    try:
        serve(connection_port=args.tcp_port, discovery_port=args.discovery_port)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
