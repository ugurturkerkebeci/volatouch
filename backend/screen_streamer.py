"""
Volatouch Native Screen Streamer (Zero-Dependency Windows GDI & GDI+ Capture Engine)
"""

import ctypes
from ctypes import wintypes
import struct
import threading
import time
import asyncio
from typing import Optional, Set

try:
    from volatouch.config import config
except ImportError:
    from config import config

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
gdiplus = ctypes.windll.gdiplus
ole32 = ctypes.windll.ole32
kernel32 = ctypes.windll.kernel32

# 64-bit safe signatures
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

# GDI+ Structures
class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ('GdiplusVersion', ctypes.c_uint32),
        ('DebugEventCallback', ctypes.c_void_p),
        ('SuppressBackgroundThread', ctypes.c_bool),
        ('SuppressExternalCodecs', ctypes.c_bool)
    ]

class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_uint32),
        ('Data2', ctypes.c_uint16),
        ('Data3', ctypes.c_uint16),
        ('Data4', ctypes.c_uint8 * 8)
    ]

# JPEG Encoder CLSID: {557CF401-1A04-11D3-9A73-0000F81EF32E}
CLSID_JPEG = GUID(
    0x557CF401, 0x1A04, 0x11D3,
    (ctypes.c_uint8 * 8)(0x9A, 0x73, 0x00, 0x00, 0xF8, 0x1E, 0xF3, 0x2E)
)

# EncoderQuality GUID: {1D5BE4B5-FA4A-452D-9CDD-5DB35105E7EB}
GUID_EncoderQuality = GUID(
    0x1D5BE4B5, 0xFA4A, 0x452D,
    (ctypes.c_uint8 * 8)(0x9C, 0xDD, 0x5D, 0xB3, 0x51, 0x05, 0xE7, 0xEB)
)

class EncoderParameter(ctypes.Structure):
    _fields_ = [
        ('Guid', GUID),
        ('NumberOfValues', ctypes.c_ulong),
        ('Type', ctypes.c_ulong),
        ('Value', ctypes.c_void_p)
    ]

class EncoderParameters(ctypes.Structure):
    _fields_ = [
        ('Count', ctypes.c_uint),
        ('Parameter', EncoderParameter * 1)
    ]

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


class ScreenStreamer:
    """
    Zero-dependency, hardware-level Windows screen capture engine.
    Uses Win32 GDI BitBlt/StretchBlt for capture (<2ms) and Windows GDI+
    native JPEG encoder (<2ms) with zero external python dependencies.
    """

    def __init__(self):
        self._quality = config.default_quality
        self._scale = config.default_scale
        self._target_fps = config.target_fps
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._clients: Set[asyncio.Queue] = set()
        self._clients_lock = threading.Lock()

        # Metrics
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        self.screen_left = 0
        self.screen_top = 0

        self.current_fps = 0.0
        self._fps_counter = 0
        self._last_fps_time = time.time()

        # Initialize GDI+
        self._gdiplus_token = ctypes.c_ulong()
        startup_in = GdiplusStartupInput(1, None, False, False)
        gdiplus.GdiplusStartup(ctypes.byref(self._gdiplus_token), ctypes.byref(startup_in), None)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
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
        if not self._loop or self._loop.is_closed():
            return
        with self._clients_lock:
            if not self._clients:
                return
            active_list = list(self._clients)

        def _push():
            for q in active_list:
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

        # Update screen bounds
        orig_w = user32.GetSystemMetrics(0)
        orig_h = user32.GetSystemMetrics(1)
        self.screen_width = orig_w
        self.screen_height = orig_h

        hScreenDC = user32.GetDC(0)

        # Drawing cursor arrow points
        hWhitePen = gdi32.CreatePen(0, 1, 0x00FFFFFF)
        hBlackPen = gdi32.CreatePen(0, 2, 0x00000000)
        hWhiteBrush = gdi32.CreateSolidBrush(0x00FFFFFF)

        current_cached_scale = -1.0
        hMemDC = None
        hBitmap = None
        hOldBitmap = None
        target_w = orig_w
        target_h = orig_h

        try:
            while self._running:
                loop_start = time.perf_counter()

                # Recreate compatible DC/Bitmap if scale changes
                active_scale = self._scale
                if active_scale != current_cached_scale:
                    if hMemDC:
                        gdi32.SelectObject(hMemDC, hOldBitmap)
                        gdi32.DeleteObject(hBitmap)
                        gdi32.DeleteDC(hMemDC)

                    target_w = max(16, int(orig_w * active_scale))
                    target_h = max(16, int(orig_h * active_scale))

                    hMemDC = gdi32.CreateCompatibleDC(hScreenDC)
                    hBitmap = gdi32.CreateCompatibleBitmap(hScreenDC, target_w, target_h)
                    hOldBitmap = gdi32.SelectObject(hMemDC, hBitmap)
                    gdi32.SetStretchBltMode(hMemDC, 3)  # COLORONCOLOR (instant nearest-neighbor)
                    current_cached_scale = active_scale

                try:
                    # 1. Grab screen with hardware StretchBlt
                    gdi32.StretchBlt(hMemDC, 0, 0, target_w, target_h, hScreenDC, 0, 0, orig_w, orig_h, 0x00CC0020)

                    # 2. Draw hardware cursor overlay
                    pt = POINT()
                    if user32.GetCursorPos(ctypes.byref(pt)):
                        cx = int(pt.x * active_scale)
                        cy = int(pt.y * active_scale)
                        if 0 <= cx < target_w and 0 <= cy < target_h:
                            arrow_pts = (POINT * 7)(
                                POINT(cx, cy),
                                POINT(cx, cy + 19),
                                POINT(cx + 5, cy + 14),
                                POINT(cx + 9, cy + 22),
                                POINT(cx + 12, cy + 20),
                                POINT(cx + 8, cy + 13),
                                POINT(cx + 15, cy + 13)
                            )
                            old_pen = gdi32.SelectObject(hMemDC, hBlackPen)
                            old_brush = gdi32.SelectObject(hMemDC, hWhiteBrush)
                            gdi32.Polygon(hMemDC, arrow_pts, 7)
                            gdi32.SelectObject(hMemDC, old_pen)
                            gdi32.SelectObject(hMemDC, old_brush)

                    # 3. Native GDI+ JPEG compression
                    pBitmap = ctypes.c_void_p()
                    gdiplus.GdipCreateBitmapFromHBITMAP(hBitmap, 0, ctypes.byref(pBitmap))

                    pStream = ctypes.c_void_p()
                    ole32.CreateStreamOnHGlobal(None, True, ctypes.byref(pStream))

                    q_val = ctypes.c_ulong(self._quality)
                    enc_params = EncoderParameters(1, (EncoderParameter * 1)(
                        EncoderParameter(GUID_EncoderQuality, 1, 4, ctypes.cast(ctypes.byref(q_val), ctypes.c_void_p))
                    ))
                    gdiplus.GdipSaveImageToStream(pBitmap, pStream, ctypes.byref(CLSID_JPEG), ctypes.byref(enc_params))

                    hGlobal = ctypes.c_void_p()
                    ole32.GetHGlobalFromStream(pStream, ctypes.byref(hGlobal))
                    size = kernel32.GlobalSize(hGlobal)
                    ptr = kernel32.GlobalLock(hGlobal)
                    encoded_bytes = ctypes.string_at(ptr, size)
                    kernel32.GlobalUnlock(hGlobal)

                    gdiplus.GdipDisposeImage(pBitmap)

                    # 4. Dispatch frame with 8-byte double timestamp
                    timestamp_header = struct.pack('>d', time.time() * 1000)
                    packet_bytes = timestamp_header + encoded_bytes
                    self._dispatch_frame(packet_bytes)

                    # 5. Measure FPS
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

        finally:
            if hMemDC:
                gdi32.SelectObject(hMemDC, hOldBitmap)
                gdi32.DeleteObject(hBitmap)
                gdi32.DeleteDC(hMemDC)
            gdi32.DeleteObject(hWhitePen)
            gdi32.DeleteObject(hBlackPen)
            gdi32.DeleteObject(hWhiteBrush)
            user32.ReleaseDC(0, hScreenDC)
