"""
Volatouch Native Input Controller (Zero-Dependency Windows Hardware Emulation via ctypes)
"""

import ctypes
from ctypes import wintypes
import time
from typing import Set, List, Optional

if hasattr(ctypes, "windll"):
    user32 = ctypes.windll.user32
else:
    user32 = None

# Mouse flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0009
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# Virtual-Key Codes Mapping
VK_MAPPING = {
    "enter": 0x0D,
    "return": 0x0D,
    "backspace": 0x08,
    "tab": 0x09,
    "space": 0x20,
    "esc": 0x1B,
    "escape": 0x1B,
    "delete": 0x2E,
    "shift": 0x10,
    "shift_l": 0xA0,
    "shift_r": 0xA1,
    "ctrl": 0x11,
    "ctrl_l": 0xA2,
    "ctrl_r": 0xA3,
    "alt": 0x12,
    "alt_l": 0xA4,
    "alt_r": 0xA5,
    "win": 0x5B,
    "cmd": 0x5B,
    "super": 0x5B,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "home": 0x24,
    "end": 0x23,
    "page_up": 0x21,
    "page_down": 0x22,
    "caps_lock": 0x14,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}

# SendInput C structures for Unicode text typing
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT),
        ('hi', HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', INPUT_UNION)
    ]

user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


class InputController:
    """Zero-dependency Windows Input Controller using ctypes Win32 APIs."""

    def __init__(self):
        self._pressed_keys: Set[int] = set()
        self._pressed_buttons: Set[str] = set()
        self._acc_dx: float = 0.0
        self._acc_dy: float = 0.0

    def move_mouse(self, dx: float, dy: float):
        """Relative cursor motion with sub-pixel accumulator."""
        self._acc_dx += dx
        self._acc_dy += dy

        int_x = int(self._acc_dx)
        int_y = int(self._acc_dy)

        if int_x != 0 or int_y != 0:
            self._acc_dx -= int_x
            self._acc_dy -= int_y
            user32.mouse_event(MOUSEEVENTF_MOVE, int_x, int_y, 0, 0)

    def move_mouse_abs(self, norm_x: float, norm_y: float, screen_w: int, screen_h: int, screen_left: int = 0, screen_top: int = 0):
        """Direct absolute cursor positioning using normalized (0.0 to 1.0) coordinates."""
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        target_x = int(screen_left + norm_x * screen_w)
        target_y = int(screen_top + norm_y * screen_h)
        user32.SetCursorPos(target_x, target_y)

    def click_mouse(self, button: str = "left", count: int = 1):
        """Mouse click emulation."""
        b = button.lower()
        if b == "right":
            down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
        elif b == "middle":
            down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
        else:
            down_flag, up_flag = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP

        for _ in range(count):
            user32.mouse_event(down_flag, 0, 0, 0, 0)
            time.sleep(0.005)
            user32.mouse_event(up_flag, 0, 0, 0, 0)
            if count > 1:
                time.sleep(0.04)

    def mouse_down(self, button: str = "left"):
        """Press and hold mouse button."""
        b = button.lower()
        if b == "right":
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        elif b == "middle":
            user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        else:
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self._pressed_buttons.add(b)

    def mouse_up(self, button: str = "left"):
        """Release mouse button."""
        b = button.lower()
        if b == "right":
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        elif b == "middle":
            user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
        else:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self._pressed_buttons.discard(b)

    def scroll_mouse(self, dx: float, dy: float):
        """Vertical/horizontal mouse wheel scroll."""
        if dy != 0:
            # Win32 WHEEL_DELTA is 120
            wheel_amount = int(dy * 120)
            user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, wheel_amount, 0)

    def _resolve_vk(self, key_str: str) -> Optional[int]:
        """Convert key name or character to Windows Virtual-Key code."""
        k = key_str.lower()
        if k in VK_MAPPING:
            return VK_MAPPING[k]
        if len(key_str) == 1:
            ch = key_str.upper()
            vk = ord(ch)
            if (0x30 <= vk <= 0x39) or (0x41 <= vk <= 0x5A):  # 0-9 or A-Z
                return vk
        return None

    def key_down(self, key_str: str):
        """Press and hold key."""
        vk = self._resolve_vk(key_str)
        if vk is not None:
            user32.keybd_event(vk, 0, 0, 0)
            self._pressed_keys.add(vk)

    def key_up(self, key_str: str):
        """Release key."""
        vk = self._resolve_vk(key_str)
        if vk is not None:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            self._pressed_keys.discard(vk)

    def key_tap(self, key_str: str, modifiers: Optional[List[str]] = None):
        """Tap key with optional active modifier keys."""
        pressed_mods: List[int] = []
        if modifiers:
            for mod in modifiers:
                mvk = self._resolve_vk(mod)
                if mvk is not None and mvk not in self._pressed_keys:
                    user32.keybd_event(mvk, 0, 0, 0)
                    pressed_mods.append(mvk)
                    self._pressed_keys.add(mvk)

        vk = self._resolve_vk(key_str)
        if vk is not None:
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        elif len(key_str) == 1:
            self.type_text(key_str)

        # Release modifiers held for this tap
        for mvk in pressed_mods:
            user32.keybd_event(mvk, 0, KEYEVENTF_KEYUP, 0)
            self._pressed_keys.discard(mvk)

    def type_text(self, text: str):
        """Type Unicode text safely via SendInput without keyboard layout issues."""
        for ch in text:
            code = ord(ch)
            inp_down = INPUT(type=1)
            inp_down.u.ki.wVk = 0
            inp_down.u.ki.wScan = code
            inp_down.u.ki.dwFlags = KEYEVENTF_UNICODE

            inp_up = INPUT(type=1)
            inp_up.u.ki.wVk = 0
            inp_up.u.ki.wScan = code
            inp_up.u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP

            inputs = (INPUT * 2)(inp_down, inp_up)
            user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
            time.sleep(0.002)

    def release_all(self):
        """Failsafe: release all pressed mouse buttons and keys."""
        for vk in list(self._pressed_keys):
            try:
                user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            except Exception:
                pass
        self._pressed_keys.clear()

        for b in list(self._pressed_buttons):
            try:
                if b == "right":
                    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                elif b == "middle":
                    user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                else:
                    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            except Exception:
                pass
        self._pressed_buttons.clear()
