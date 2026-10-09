"""
Volatouch ADB Manager
Provides zero-dependency ADB discovery, automatic portable setup (Google platform-tools),
and device management for controlling Android devices from PC.
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
import time
from typing import Optional, List, Tuple

GOOGLE_PLATFORM_TOOLS_URLS = {
    "win32": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
    "darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
}

class ADBManager:
    """Manages local or portable ADB binaries and device connections."""

    _cached_adb_path: Optional[str] = None

    @classmethod
    def get_volatouch_bin_dir(cls) -> str:
        home = os.path.expanduser("~")
        bin_dir = os.path.join(home, ".volatouch", "bin")
        os.makedirs(bin_dir, exist_ok=True)
        return bin_dir

    @classmethod
    def find_adb(cls) -> Optional[str]:
        if cls._cached_adb_path and os.path.exists(cls._cached_adb_path):
            return cls._cached_adb_path

        # 1. System PATH
        system_adb = shutil.which("adb") or shutil.which("adb.exe")
        if system_adb:
            cls._cached_adb_path = system_adb
            return system_adb

        # 2. Local Volatouch portable directory
        bin_dir = cls.get_volatouch_bin_dir()
        candidate = os.path.join(bin_dir, "adb.exe" if sys.platform == "win32" else "adb")
        if os.path.exists(candidate) and (sys.platform == "win32" or os.access(candidate, os.X_OK)):
            cls._cached_adb_path = candidate
            return candidate

        # 3. Known standard installation paths
        standard_paths = []
        if sys.platform == "win32":
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            if local_appdata:
                standard_paths.append(os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe"))
            standard_paths.append(r"C:\platform-tools\adb.exe")
            standard_paths.append(r"C:\Program Files\Android\platform-tools\adb.exe")
        elif sys.platform == "darwin":
            standard_paths.append(os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"))
        else:
            standard_paths.append(os.path.expanduser("~/Android/Sdk/platform-tools/adb"))
            standard_paths.append("/usr/bin/adb")
            standard_paths.append("/usr/local/bin/adb")

        for path in standard_paths:
            if os.path.exists(path):
                cls._cached_adb_path = path
                return path

        return None

    @classmethod
    def ensure_adb(cls) -> Optional[str]:
        """Finds existing ADB or automatically downloads portable Google platform-tools."""
        existing = cls.find_adb()
        if existing:
            return existing

        url = GOOGLE_PLATFORM_TOOLS_URLS.get(sys.platform)
        if not url:
            print("[!] Unsupported platform for automatic ADB download.", flush=True)
            return None

        bin_dir = cls.get_volatouch_bin_dir()
        zip_path = os.path.join(bin_dir, "platform-tools.zip")

        print("\n[*] ADB not found on system. Auto-downloading portable Google platform-tools (~8MB)...", flush=True)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Volatouch/1.3.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as out_file:
                shutil.copyfileobj(resp, out_file)

            print("[*] Extracting portable ADB tools...", flush=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if not filename:
                        continue
                    # Extract directly to bin_dir
                    source = zip_ref.open(member)
                    target_path = os.path.join(bin_dir, filename)
                    with open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)

            # Cleanup zip
            try:
                os.remove(zip_path)
            except Exception:
                pass

            target_binary = os.path.join(bin_dir, "adb.exe" if sys.platform == "win32" else "adb")
            if sys.platform != "win32" and os.path.exists(target_binary):
                os.chmod(target_binary, 0o755)

            if os.path.exists(target_binary):
                cls._cached_adb_path = target_binary
                print("[+] Portable ADB successfully installed and ready!", flush=True)
                return target_binary

        except Exception as e:
            print(f"[!] Failed to auto-download ADB: {e}", flush=True)
            print("[*] Please install Android platform-tools or run 'adb' manually.", flush=True)

        return None

    @classmethod
    def list_devices(cls, adb_bin: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """Returns list of (serial, status, description). Status can be 'device', 'unauthorized', 'offline'."""
        binary = adb_bin or cls.find_adb()
        if not binary:
            return []

        try:
            res = subprocess.run([binary, "devices", "-l"], capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return []

            devices = []
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("List of devices attached") or line.startswith("*"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]
                    extra = " ".join(parts[2:]) if len(parts) > 2 else ""
                    devices.append((serial, status, extra))
            return devices
        except Exception:
            return []

    @classmethod
    def wait_for_device(cls, adb_bin: Optional[str] = None, timeout: float = 10.0) -> Optional[str]:
        """Waits for an authorized device to connect. Returns the device serial if found."""
        binary = adb_bin or cls.ensure_adb()
        if not binary:
            return None

        start_time = time.time()
        warned_unauthorized = False
        warned_no_device = False

        while time.time() - start_time < timeout:
            devices = cls.list_devices(binary)
            if not devices:
                if not warned_no_device:
                    print("[!] No Android device found. Connect phone via USB with 'USB Debugging' enabled...", flush=True)
                    warned_no_device = True
                time.sleep(1.0)
                continue

            # Look for ready 'device'
            for serial, status, extra in devices:
                if status == "device":
                    desc = f" ({extra})" if extra else ""
                    print(f"[+] Android device ready: {serial}{desc}", flush=True)
                    return serial
                elif status == "unauthorized":
                    if not warned_unauthorized:
                        print("[!] Phone detected but UNAUTHORIZED! Check phone screen and tap [Allow / Always allow].", flush=True)
                        warned_unauthorized = True

            time.sleep(1.0)

        return None
