import struct
import cv2
import mss
import numpy as np
import threading
import time
import asyncio
import logging
from typing import Optional, Set
import ctypes
try:
    from volatouch.config import config
except ImportError:
    from config import config

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class ScreenStreamer:
    """
    Ultra-low latency screen capture engine with zero-copy pipeline,
    direct BGRA encoding, and zero-latency asyncio event dispatch.
    """
    def __init__(self):
        self._quality = 50       # 50 is the optimal sweet spot for 60 FPS mobile Wi-Fi streaming
        self._scale = 0.65       # 0.65 yields razor-sharp display at ultra-high frame rates
        self._target_fps = 60
        self._monitor_idx = config.monitor_index
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Asyncio event loop & client queues for zero-delay wakeup
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._clients: Set[asyncio.Queue] = set()
        self._clients_lock = threading.Lock()
        
        # Screen resolution info
        self.screen_width = 1920
        self.screen_height = 1080
        self.screen_left = 0
        self.screen_top = 0

        # FPS metrics
        self.current_fps = 0.0
        self._fps_counter = 0
        self._last_fps_time = time.time()

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        """Register a new WebSocket client queue (maxsize=1 for zero backpressure)."""
        q = asyncio.Queue(maxsize=1)
        with self._clients_lock:
            self._clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._clients_lock:
            self._clients.discard(q)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True, name="CaptureWorker")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def update_settings(self, quality: Optional[int] = None, scale: Optional[float] = None):
        if quality is not None:
            self._quality = max(10, min(95, int(quality)))
        if scale is not None:
            self._scale = max(0.2, min(1.0, float(scale)))

    def get_settings(self) -> dict:
        return {
            "quality": self._quality,
            "scale": self._scale,
            "fps": round(self.current_fps, 1),
            "width": self.screen_width,
            "height": self.screen_height
        }

    def _dispatch_frame(self, packet_bytes: bytes):
        """Thread-safe non-blocking push to all active client queues."""
        if not self._loop or self._loop.is_closed():
            return
        
        with self._clients_lock:
            if not self._clients:
                return
            active_list = list(self._clients)

        def _push():
            for q in active_list:
                # If client hasn't consumed previous frame, drop it immediately
                if not q.empty():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                try:
                    q.put_nowait(packet_bytes)
                except asyncio.QueueFull:
                    pass

        self._loop.call_soon_threadsafe(_push)

    def _capture_worker(self):
        frame_interval = 1.0 / self._target_fps

        with mss.mss() as sct:
            monitors = sct.monitors
            monitor = monitors[self._monitor_idx] if len(monitors) > self._monitor_idx else monitors[0]
            self.screen_width = monitor["width"]
            self.screen_height = monitor["height"]
            self.screen_left = monitor.get("left", 0)
            self.screen_top = monitor.get("top", 0)

            while self._running:
                loop_start = time.perf_counter()

                try:
                    # 1. Grab raw BGRA buffer
                    raw_shot = sct.grab(monitor)

                    # 2. Reshape into BGRA numpy buffer without any unnecessary color conversions
                    bgra = np.frombuffer(raw_shot.raw, dtype=np.uint8).reshape((raw_shot.height, raw_shot.width, 4))

                    # 3. Dynamic scaling with INTER_NEAREST (<1ms)
                    current_scale = self._scale
                    if current_scale < 0.99:
                        new_w = max(16, int(raw_shot.width * current_scale))
                        new_h = max(16, int(raw_shot.height * current_scale))
                        bgra = cv2.resize(bgra, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

                    # 4. Hardware cursor overlay
                    try:
                        pt = POINT()
                        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
                            cx = pt.x - monitor["left"]
                            cy = pt.y - monitor["top"]
                            if 0 <= cx < raw_shot.width and 0 <= cy < raw_shot.height:
                                scx = int(cx * current_scale)
                                scy = int(cy * current_scale)
                                arrow = np.array([
                                    [scx, scy],
                                    [scx, scy + 19],
                                    [scx + 5, scy + 14],
                                    [scx + 9, scy + 22],
                                    [scx + 12, scy + 20],
                                    [scx + 8, scy + 13],
                                    [scx + 15, scy + 13]
                                ], dtype=np.int32)
                                # Draw black border and white arrow on BGRA
                                cv2.fillPoly(bgra, [arrow], (255, 255, 255, 255))
                                cv2.polylines(bgra, [arrow], isClosed=True, color=(0, 0, 0, 255), thickness=2)
                    except Exception:
                        pass

                    # 5. Direct BGRA JPEG compression with IMWRITE_JPEG_OPTIMIZE=0
                    encode_params = [
                        int(cv2.IMWRITE_JPEG_QUALITY), int(self._quality),
                        int(cv2.IMWRITE_JPEG_OPTIMIZE), 0
                    ]
                    success, encoded = cv2.imencode('.jpg', bgra, encode_params)

                    if success:
                        timestamp_header = struct.pack('>d', time.time() * 1000)
                        packet_bytes = timestamp_header + encoded.tobytes()

                        # Dispatch immediately to all waiting WebSocket clients with ZERO delay
                        self._dispatch_frame(packet_bytes)

                        # Calculate FPS
                        self._fps_counter += 1
                        now = time.time()
                        if now - self._last_fps_time >= 1.0:
                            self.current_fps = self._fps_counter / (now - self._last_fps_time)
                            self._fps_counter = 0
                            self._last_fps_time = now

                except Exception:
                    time.sleep(0.01)

                elapsed = time.perf_counter() - loop_start
                sleep_needed = frame_interval - elapsed
                if sleep_needed > 0:
                    time.sleep(sleep_needed)
