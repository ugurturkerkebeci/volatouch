"""
Volatouch Android Screen Streamer
Zero-Dependency Android framebuffer capture engine using /system/bin/screencap.
"""

import os
import sys
import time
import struct
import shutil
import asyncio
import threading
import subprocess
from typing import Optional, Set

try:
    from volatouch.config import config
except ImportError:
    from config import config

class AndroidScreenStreamer:
    """Captures Android screen frames and broadcasts them to WebSocket subscribers."""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.quality = config.default_quality
        self.scale = config.default_scale
        self.fps = min(30, config.target_fps)  # Max 30 FPS for mobile screencap

        self.screencap_bin = self._find_binary("screencap")
        self.screen_width = 1080
        self.screen_height = 2400
        self.screen_left = 0
        self.screen_top = 0

        self._detect_screen_size()

    def _find_binary(self, name: str) -> str:
        for p in [f"/system/bin/{name}", f"/system/xbin/{name}"]:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
        w = shutil.which(name)
        if w:
            return w
        return f"/system/bin/{name}"

    def _detect_screen_size(self):
        # 1. Try `wm size`
        wm_bin = self._find_binary("wm")
        try:
            res = subprocess.run([wm_bin, "size"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and "Physical size:" in res.stdout:
                part = res.stdout.split("Physical size:")[-1].strip().split("\n")[0].strip()
                if "x" in part:
                    w_str, h_str = part.split("x", 1)
                    self.screen_width = int(w_str.strip())
                    self.screen_height = int(h_str.strip())
                    return
        except Exception:
            pass

        # 2. Try dumpsys window displays
        try:
            dumpsys_bin = self._find_binary("dumpsys")
            res = subprocess.run([dumpsys_bin, "window", "displays"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "cur=" in line and "app=" in line:
                        parts = line.split("cur=")
                        if len(parts) > 1:
                            wh = parts[1].split()[0]
                            if "x" in wh:
                                w_str, h_str = wh.split("x", 1)
                                self.screen_width = int(w_str)
                                self.screen_height = int(h_str)
                                return
        except Exception:
            pass

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=2)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.subscribers.discard(q)

    def update_settings(self, quality: Optional[int] = None, scale: Optional[float] = None):
        if quality is not None:
            self.quality = max(10, min(95, quality))
        if scale is not None:
            self.scale = max(0.2, min(1.0, scale))

    def get_settings(self) -> dict:
        return {
            "quality": self.quality,
            "scale": self.scale,
            "fps": self.fps,
            "width": self.screen_width,
            "height": self.screen_height
        }

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _capture_frame(self) -> Optional[bytes]:
        try:
            cmd = [self.screencap_bin, "-p"]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
            if proc.returncode == 0 and len(proc.stdout) > 24:
                data = proc.stdout
                # If PNG magic bytes \x89PNG\r\n\x1a\n
                if data.startswith(b"\x89PNG"):
                    # Bytes 16 to 24 in PNG are Width and Height in Big-Endian unsigned int
                    w, h = struct.unpack(">II", data[16:24])
                    if w > 0 and h > 0:
                        self.screen_width = w
                        self.screen_height = h
                return data
        except Exception:
            pass
        return None

    def _capture_worker(self):
        target_delay = 1.0 / max(1, self.fps)

        while self.running:
            start_t = time.perf_counter()

            if not self.subscribers:
                time.sleep(0.05)
                continue

            img_bytes = self._capture_frame()
            if img_bytes and self._loop and self.running:
                now_ms = time.time() * 1000.0
                packet = struct.pack(">d", now_ms) + img_bytes

                for q in list(self.subscribers):
                    if q.full():
                        try:
                            q.get_nowait()
                        except Exception:
                            pass
                    try:
                        self._loop.call_soon_threadsafe(q.put_nowait, packet)
                    except Exception:
                        pass

            elapsed = time.perf_counter() - start_t
            sleep_t = target_delay - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)
            else:
                time.sleep(0.005)
