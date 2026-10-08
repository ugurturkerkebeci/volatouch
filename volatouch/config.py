import socket
from dataclasses import dataclass

def get_local_ip() -> str:
    """Attempts to find the LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Does not actually create a connection, just gets outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@dataclass
class StreamConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    default_quality: int = 55       # JPEG quality (10-100)
    default_scale: float = 0.70     # Resolution scale (0.3 - 1.0)
    target_fps: int = 60            # Maximum capture rate
    monitor_index: int = 1          # Primary monitor in mss

config = StreamConfig()
LOCAL_IP = get_local_ip()
