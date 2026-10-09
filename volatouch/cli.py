import argparse
import sys
from volatouch.config import config, LOCAL_IP
from volatouch.server import run_server
from volatouch import __version__

def main():
    parser = argparse.ArgumentParser(
        prog="volatouch",
        description="Volatouch: Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi (Zero Dependencies)."
    )
    parser.add_argument("--host", default=config.host, help=f"Host network interface to bind (default: {config.host})")
    parser.add_argument("--port", "-p", type=int, default=config.port, help=f"Port to listen on (default: {config.port})")
    parser.add_argument("--quality", "-q", type=int, default=config.default_quality, help=f"Initial JPEG stream quality (10-100, default: {config.default_quality})")
    parser.add_argument("--scale", "-s", type=float, default=config.default_scale, help=f"Initial resolution scale (0.2-1.0, default: {config.default_scale})")
    parser.add_argument("--mode", "-m", choices=["auto", "pc", "phone"], default="auto", help="Execution mode: 'auto' (detect platform), 'pc' (control PC from phone), or 'phone' (control Android phone from PC)")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    config.host = args.host
    config.port = args.port
    config.default_quality = max(10, min(95, args.quality))
    config.default_scale = max(0.2, min(1.0, args.scale))

    run_server(host=args.host, port=args.port, mode=args.mode)

if __name__ == "__main__":
    main()
