import logging
from typing import Set, List, Optional
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

logger = logging.getLogger("volatouch.input")

class InputController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self._pressed_keys: Set[Key] = set()
        self._pressed_mouse_buttons: Set[Button] = set()
        
        # Fractional delta accumulators for smooth micro-movements
        self._acc_dx: float = 0.0
        self._acc_dy: float = 0.0

        # Key mapping dictionary
        self._special_keys = {
            "enter": Key.enter,
            "return": Key.enter,
            "backspace": Key.backspace,
            "tab": Key.tab,
            "space": Key.space,
            "esc": Key.esc,
            "escape": Key.esc,
            "delete": Key.delete,
            "shift": Key.shift,
            "shift_r": Key.shift_r,
            "ctrl": Key.ctrl_l,
            "control": Key.ctrl_l,
            "alt": Key.alt_l,
            "cmd": Key.cmd,
            "super": Key.cmd,
            "win": Key.cmd,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "home": Key.home,
            "end": Key.end,
            "pageup": Key.page_up,
            "pagedown": Key.page_down,
            "capslock": Key.caps_lock,
            "f1": Key.f1,
            "f2": Key.f2,
            "f3": Key.f3,
            "f4": Key.f4,
            "f5": Key.f5,
            "f6": Key.f6,
            "f7": Key.f7,
            "f8": Key.f8,
            "f9": Key.f9,
            "f10": Key.f10,
            "f11": Key.f11,
            "f12": Key.f12,
        }

    def _resolve_button(self, name: str) -> Button:
        btn = name.lower()
        if btn == "right":
            return Button.right
        elif btn == "middle":
            return Button.middle
        return Button.left

    def _resolve_key(self, key_str: str):
        normalized = key_str.lower()
        if normalized in self._special_keys:
            return self._special_keys[normalized]
        if len(key_str) == 1:
            return key_str
        return None

    def move_mouse(self, dx: float, dy: float):
        """Relative mouse move with sub-pixel accumulator."""
        self._acc_dx += dx
        self._acc_dy += dy
        
        move_x = int(self._acc_dx)
        move_y = int(self._acc_dy)
        
        if move_x != 0 or move_y != 0:
            self.mouse.move(move_x, move_y)
            self._acc_dx -= move_x
            self._acc_dy -= move_y
    def move_mouse_abs(self, norm_x: float, norm_y: float, screen_width: int, screen_height: int, left: int = 0, top: int = 0):
        """
        Direct Target Positioning: Moves mouse pointer immediately to the normalized
        touch coordinate (0.0 - 1.0) on the host monitor.
        """
        clamped_x = max(0.0, min(1.0, float(norm_x)))
        clamped_y = max(0.0, min(1.0, float(norm_y)))
        target_x = int(round(left + clamped_x * screen_width))
        target_y = int(round(top + clamped_y * screen_height))
        try:
            self.mouse.position = (target_x, target_y)
            self._acc_dx = 0.0
            self._acc_dy = 0.0
        except Exception as e:
            logger.error(f"Error setting absolute mouse position ({target_x}, {target_y}): {e}")

    def click_mouse(self, button_name: str = "left", count: int = 1):
        """Perform a single or double click."""
        btn = self._resolve_button(button_name)
        self.mouse.click(btn, count)

    def mouse_down(self, button_name: str = "left"):
        """Press and hold mouse button (e.g. for drag & drop)."""
        btn = self._resolve_button(button_name)
        self.mouse.press(btn)
        self._pressed_mouse_buttons.add(btn)

    def mouse_up(self, button_name: str = "left"):
        """Release held mouse button."""
        btn = self._resolve_button(button_name)
        self.mouse.release(btn)
        self._pressed_mouse_buttons.discard(btn)

    def scroll_mouse(self, dx: float, dy: float):
        """Scroll vertical or horizontal."""
        # Windows / pynput mouse.scroll(dx, dy)
        self.mouse.scroll(int(round(dx)), int(round(dy)))

    def key_down(self, key_str: str):
        """Press down a key."""
        resolved = self._resolve_key(key_str)
        if resolved is not None:
            try:
                self.keyboard.press(resolved)
                self._pressed_keys.add(resolved)
            except Exception as e:
                logger.warning(f"Failed to press key {key_str}: {e}")

    def key_up(self, key_str: str):
        """Release a pressed key."""
        resolved = self._resolve_key(key_str)
        if resolved is not None:
            try:
                self.keyboard.release(resolved)
                self._pressed_keys.discard(resolved)
            except Exception as e:
                logger.warning(f"Failed to release key {key_str}: {e}")

    def key_tap(self, key_str: str, modifiers: Optional[List[str]] = None):
        """
        Tap a key with optional modifier combinations (e.g. Ctrl + C).
        Safely presses modifiers, taps target key, and releases modifiers.
        """
        resolved_mods = []
        if modifiers:
            for mod in modifiers:
                m = self._resolve_key(mod)
                if m is not None:
                    resolved_mods.append(m)

        resolved_key = self._resolve_key(key_str)
        if resolved_key is None:
            return

        try:
            for mod in resolved_mods:
                self.keyboard.press(mod)

            self.keyboard.press(resolved_key)
            self.keyboard.release(resolved_key)

            for mod in reversed(resolved_mods):
                self.keyboard.release(mod)
        except Exception as e:
            logger.error(f"Error during key tap ({modifiers} + {key_str}): {e}")

    def type_text(self, text: str):
        """Type arbitrary string."""
        try:
            self.keyboard.type(text)
        except Exception as e:
            logger.error(f"Error typing text: {e}")

    def release_all(self):
        """Emergency release of all currently held buttons and keys to avoid stuck states."""
        for btn in list(self._pressed_mouse_buttons):
            try:
                self.mouse.release(btn)
            except Exception:
                pass
        self._pressed_mouse_buttons.clear()

        for k in list(self._pressed_keys):
            try:
                self.keyboard.release(k)
            except Exception:
                pass
        self._pressed_keys.clear()
        self._acc_dx = 0.0
        self._acc_dy = 0.0
