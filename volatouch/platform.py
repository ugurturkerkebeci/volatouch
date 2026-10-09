"""
Volatouch Platform Detection Engine
Zero-Dependency platform and environment identification.
"""

import os
import sys
import shutil

def is_android() -> bool:
    """
    Detect if running inside an Android environment (Termux, PRoot, Android terminal).
    """
    if "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ:
        return True
    if "TERMUX_VERSION" in os.environ:
        return True
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    # Check for Android system binaries
    if os.path.exists("/system/bin/screencap") or os.path.exists("/system/bin/input"):
        return True
    return False

def is_windows() -> bool:
    """Detect if running on Windows."""
    return sys.platform == "win32"

def detect_platform(mode_override: str = "auto") -> str:
    """
    Returns 'android' or 'windows' (fallback to 'windows').
    mode_override can be 'auto', 'pc', 'windows', 'phone', or 'android'.
    """
    mode = (mode_override or "auto").lower()
    if mode in ("phone", "android"):
        return "android"
    if mode in ("pc", "windows"):
        return "windows"

    if is_android():
        return "android"
    if is_windows():
        return "windows"

    # Default fallback
    return "windows"
