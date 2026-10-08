import argparse
import sys
import uvicorn
from volatouch.config import config, LOCAL_IP

def main():
    parser = argparse.ArgumentParser(
        prog="volatouch",
        description="Volatouch: Zero-Latency Mobile Air Control & Remote Trackpad for PC over local Wi-Fi."
    )
    parser.add_argument("--host", default=config.host, help=f"Host interface to bind (default: {config.host})")
    parser.add_argument("--port", type=int, default=config.port, help=f"Port to listen on (default: {config.port})")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    args = parser.parse_args()

    uvicorn.run("volatouch.main:app", host=args.host, port=args.port, log_level="warning", access_log=False)

if __name__ == "__main__":
    main()
