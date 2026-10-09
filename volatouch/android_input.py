"""
Volatouch Android Input Controller
Zero-Dependency input injection engine using /system/bin/input.
Zero-Root Support: Local ADB, Wireless Debugging, Shizuku (rish), and Root (su).
"""

import os
import time
import shutil
import subprocess
from typing import List, Optional, Tuple

class AndroidInputController:
    """Translates input events into native Android /system/bin/input commands."""

    def __init__(self):
        self.input_bin = "input"
        self.adb_bin: Optional[str] = None
        self.cmd_prefix: List[str] = self._detect_cmd_prefix()
        self.last_x: int = 540
        self.last_y: int = 1200
        self.is_down: bool = False
        self.down_pos: Tuple[int, int] = (540, 1200)
        self.down_time: float = 0.0

    def _detect_cmd_prefix(self) -> List[str]:
        # 1. On Android local terminal (Termux / native)
        local_input = self._find_binary("input")
        if os.path.exists(local_input) and os.access(local_input, os.X_OK):
            self.input_bin = local_input
            return []

        # 2. Shizuku (Zero-Root)
        rish_bin = shutil.which("rish")
        if rish_bin:
            return [rish_bin, "-c"]

        # 3. Root
        for su_candidate in ["su", "/system/xbin/su", "/system/bin/su"]:
            if shutil.which(su_candidate) or os.path.exists(su_candidate):
                return [su_candidate, "-c"]

        # 4. ADB (PC or Local Wireless Debugging via ADBManager)
        try:
            from volatouch.adb_manager import ADBManager
            adb = ADBManager.ensure_adb()
            if adb:
                self.adb_bin = adb
                return [adb, "shell"]
        except Exception:
            pass

        return []

    def _find_binary(self, name: str) -> str:
        for p in [f"/system/bin/{name}", f"/system/xbin/{name}"]:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
        w = shutil.which(name)
        if w:
            return w
        return name

    def _exec_input(self, *args):
        try:
            adb = self.adb_bin or "adb"
            if self.cmd_prefix and "shell" in self.cmd_prefix:
                cmd = [adb, "shell", "input"] + [str(a) for a in args]
            elif self.cmd_prefix:
                cmd_str = f"{self.input_bin} " + " ".join(str(a) for a in args)
                cmd = self.cmd_prefix + [cmd_str]
            else:
                cmd = [self.input_bin] + [str(a) for a in args]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            if res.returncode != 0 and b"INJECT_EVENTS" in res.stderr:
                if not getattr(self, "_warned_security", False):
                    self._warned_security = True
                    print("\n" + "!" * 65, flush=True)
                    print("[!] XIAOMI / REDMI / MIUI SECURITY REQUIREMENT:", flush=True)
                    print("[*] To allow mouse clicks, touch, and typing from PC:", flush=True)
                    print("[*] Go to: Phone Settings -> Developer Options", flush=True)
                    print("[*] Enable: 'USB debugging (Security settings)'", flush=True)
                    print("[*] (Ayarlar ➔ Gelistirici Secenekleri ➔ 'USB Hata Ayiklama (Guvenlik Ayarlari)'ni acin)", flush=True)
                    print("!" * 65 + "\n", flush=True)
        except Exception:
            pass

    def move_mouse_abs(self, norm_x: float, norm_y: float, screen_w: int, screen_h: int, screen_left: int = 0, screen_top: int = 0):
        target_x = max(0, min(screen_w - 1, int(norm_x * screen_w)))
        target_y = max(0, min(screen_h - 1, int(norm_y * screen_h)))
        self.last_x = target_x
        self.last_y = target_y

    def move_mouse(self, dx: float, dy: float):
        self.last_x = max(0, int(self.last_x + dx))
        self.last_y = max(0, int(self.last_y + dy))

    def click_mouse(self, button: str = "left", count: int = 1):
        if button == "right":
            # Right-click serves as Android Back action
            self.android_nav("back")
            return

        for _ in range(count):
            self._exec_input("tap", self.last_x, self.last_y)

    def mouse_down(self, button: str = "left"):
        if button == "right":
            self.android_nav("back")
            return
        self.is_down = True
        self.down_pos = (self.last_x, self.last_y)
        self.down_time = time.time()

    def mouse_up(self, button: str = "left"):
        if not self.is_down:
            return
        self.is_down = False
        duration_ms = max(50, min(1000, int((time.time() - self.down_time) * 1000)))
        start_x, start_y = self.down_pos
        end_x, end_y = self.last_x, self.last_y

        dist_sq = (end_x - start_x) ** 2 + (end_y - start_y) ** 2
        if dist_sq < 100:
            self._exec_input("tap", end_x, end_y)
        else:
            self._exec_input("swipe", start_x, start_y, end_x, end_y, duration_ms)

    def scroll_mouse(self, dx: float, dy: float):
        swipe_dist = int(dy * 200)
        start_y = max(300, min(1800, self.last_y))
        end_y = max(100, min(2200, start_y + swipe_dist))
        self._exec_input("swipe", self.last_x, start_y, self.last_x, end_y, 150)

    def key_tap(self, key: str, modifiers: Optional[List[str]] = None):
        k = key.lower()
        key_map = {
            "enter": 66,
            "return": 66,
            "backspace": 67,
            "tab": 61,
            "space": 62,
            "esc": 111,
            "escape": 111,
            "delete": 112,
            "home": 3,
            "back": 4,
            "up": 19,
            "down": 20,
            "left": 21,
            "right": 22,
            "volume_up": 24,
            "volume_down": 25,
            "power": 26,
            "menu": 82,
            "app_switch": 187,
            "recents": 187,
        }
        if k in key_map:
            self._exec_input("keyevent", key_map[k])
        elif len(key) == 1:
            self.type_text(key)

    def key_down(self, key: str):
        pass

    def key_up(self, key: str):
        pass

    def type_text(self, text: str):
        if not text:
            return
        formatted = text.replace(" ", "%s")
        escaped = ""
        for ch in formatted:
            if ch in '"\'$\\`&|;()<>*?':
                escaped += "\\" + ch
            else:
                escaped += ch
        self._exec_input("text", escaped)

    def android_nav(self, action: str):
        nav_map = {
            "back": 4,
            "home": 3,
            "recents": 187,
            "app_switch": 187,
            "power": 26,
            "volume_up": 24,
            "volume_down": 25,
            "menu": 82,
        }
        code = nav_map.get(action.lower())
        if code:
            self._exec_input("keyevent", code)

    def release_all(self):
        self.is_down = False
