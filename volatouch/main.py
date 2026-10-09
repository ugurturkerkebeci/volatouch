"""
Volatouch Main Server Entry Point
"""

from volatouch.server import run_server
from volatouch.config import config

def main():
    run_server(host=config.host, port=config.port)

if __name__ == "__main__":
    main()
