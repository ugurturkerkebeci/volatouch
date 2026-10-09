"""
Volatouch Android Screen Streamer
Zero-Dependency Android framebuffer capture engine using /system/bin/screencap.
Zero-Root Support: Local ADB, Wireless Debugging, Shizuku (rish), and Root (su).
"""

import os
import sys
import time
import struct
import shutil
import asyncio
import threading
import subprocess
from typing import Optional, Set, List

try:
    from volatouch.config import config
except ImportError:
    from config import config

class AndroidScreenStreamer:
    """Captures Android screen frames and broadcasts them to WebSocket subscribers."""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()
        self._subscribers_lock = threading.Lock()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.quality = config.default_quality
        self.scale = config.default_scale
        self.fps = min(30, config.target_fps)  # Max 30 FPS for mobile screencap

        self.screencap_bin = self._find_binary("screencap")
        self.cmd_prefix: List[str] = self._detect_cmd_prefix()
        self.last_error: Optional[str] = None
        self._warned_error = False

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

    def _detect_cmd_prefix(self) -> List[str]:
        # 1. Test direct execution
        try:
            r = subprocess.run([self.screencap_bin, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            if r.returncode == 0 and len(r.stdout) > 24:
                return []
        except Exception:
            pass

        # 2. Test ADB (Zero-Root via Local ADB or Wireless Debugging)
        adb_bin = shutil.which("adb")
        if adb_bin:
            try:
                r = subprocess.run([adb_bin, "exec-out", self.screencap_bin, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                if r.returncode == 0 and len(r.stdout) > 24:
                    print("[+] Android: Local ADB connection active (Zero-Root).", flush=True)
                    return ["adb", "exec-out"]
            except Exception:
                pass
            try:
                r = subprocess.run([adb_bin, "shell", self.screencap_bin, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                if r.returncode == 0 and len(r.stdout) > 24:
                    print("[+] Android: Local ADB shell active (Zero-Root).", flush=True)
                    return ["adb", "shell"]
            except Exception:
                pass

        # 3. Test Shizuku (Zero-Root via rish)
        rish_bin = shutil.which("rish")
        if rish_bin:
            try:
                r = subprocess.run([rish_bin, "-c", f"{self.screencap_bin} -p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                if r.returncode == 0 and len(r.stdout) > 24:
                    print("[+] Android: Shizuku ('rish') active (Zero-Root).", flush=True)
                    return ["rish", "-c"]
            except Exception:
                pass

        # 4. Test Root (su)
        for su_candidate in ["su", "/system/xbin/su", "/system/bin/su"]:
            if shutil.which(su_candidate) or os.path.exists(su_candidate):
                try:
                    r = subprocess.run([su_candidate, "-c", f"{self.screencap_bin} -p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                    if r.returncode == 0 and len(r.stdout) > 24:
                        print(f"[+] Android: Root ('{su_candidate}') privileges active.", flush=True)
                        return [su_candidate, "-c"]
                except Exception:
                    pass

        return []

    def _detect_screen_size(self):
        wm_bin = self._find_binary("wm")
        if self.cmd_prefix == ["adb", "exec-out"] or self.cmd_prefix == ["adb", "shell"]:
            cmd = ["adb", "shell", "wm", "size"]
        elif self.cmd_prefix:
            cmd = self.cmd_prefix + [f"{wm_bin} size"]
        else:
            cmd = [wm_bin, "size"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and "Physical size:" in res.stdout:
                part = res.stdout.split("Physical size:")[-1].strip().split("\n")[0].strip()
                if "x" in part:
                    w_str, h_str = part.split("x", 1)
                    self.screen_width = int(w_str.strip())
                    self.screen_height = int(h_str.strip())
                    return
        except Exception:
            pass

        dumpsys_bin = self._find_binary("dumpsys")
        if self.cmd_prefix == ["adb", "exec-out"] or self.cmd_prefix == ["adb", "shell"]:
            cmd = ["adb", "shell", "dumpsys", "window", "displays"]
        elif self.cmd_prefix:
            cmd = self.cmd_prefix + [f"{dumpsys_bin} window displays"]
        else:
            cmd = [dumpsys_bin, "window", "displays"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
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
        with self._subscribers_lock:
            self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._subscribers_lock:
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
            "height": self.screen_height,
            "last_error": self.last_error
        }

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True, name="AndroidCaptureWorker")
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

    def _capture_frame(self) -> Optional[bytes]:
        try:
            if self.cmd_prefix == ["adb", "exec-out"]:
                cmd = ["adb", "exec-out", self.screencap_bin, "-p"]
            elif self.cmd_prefix == ["adb", "shell"]:
                cmd = ["adb", "shell", self.screencap_bin, "-p"]
            elif self.cmd_prefix:
                cmd = self.cmd_prefix + [f"{self.screencap_bin} -p"]
            else:
                cmd = [self.screencap_bin, "-p"]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            if proc.returncode == 0 and len(proc.stdout) > 24:
                self.last_error = None
                data = proc.stdout
                # If PNG magic bytes \x89PNG\r\n\x1a\n
                if data.startswith(b"\x89PNG"):
                    w, h = struct.unpack(">II", data[16:24])
                    if w > 0 and h > 0:
                        self.screen_width = w
                        self.screen_height = h
                return data
            else:
                err_msg = proc.stderr.decode("utf-8", errors="ignore").strip()
                if not err_msg:
                    err_msg = f"Exit code {proc.returncode}"
                self.last_error = err_msg

                if not self._warned_error:
                    self._warned_error = True
                    print(f"\n[!] Android Screen Capture Notice: {err_msg}", flush=True)
                    print("[*] To stream Android screen WITHOUT ROOT:", flush=True)
                    print("    1) Wireless Debugging (Termux):", flush=True)
                    print("       Run 'pkg install android-tools' -> 'adb connect localhost:<port>'", flush=True)
                    print("    2) Shizuku (Zero-Root): Run 'rish -c volatouch'", flush=True)
                    print("    3) PC ADB: Run 'adb shell volatouch' from your computer via USB/Wi-Fi\n", flush=True)
        except Exception as e:
            self.last_error = str(e)
        return None

    def _capture_worker(self):
        target_delay = 1.0 / max(1, self.fps)

        while self.running:
            start_t = time.perf_counter()

            with self._subscribers_lock:
                has_subscribers = bool(self.subscribers)

            if not has_subscribers:
                time.sleep(0.05)
                continue

            img_bytes = self._capture_frame()
            if img_bytes and self._loop and not self._loop.is_closed() and self.running:
                now_ms = time.time() * 1000.0
                packet = struct.pack(">d", now_ms) + img_bytes

                with self._subscribers_lock:
                    active_subs = list(self.subscribers)

                if active_subs:
                    def _push(subs=active_subs, pkt=packet):
                        for q in subs:
                            if not q.empty():
                                try:
                                    q.get_nowait()
                                except (asyncio.QueueEmpty, Exception):
                                    pass
                            try:
                                q.put_nowait(pkt)
                            except (asyncio.QueueFull, Exception):
                                pass

                    try:
                        self._loop.call_soon_threadsafe(_push)
                    except Exception:
                        pass

            elapsed = time.perf_counter() - start_t
            sleep_t = target_delay - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)
            else:
                time.sleep(0.005)
