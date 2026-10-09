<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/banner.jpg" alt="Volatouch Banner" width="100%" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/logo.jpg" alt="Volatouch Logo" width="120" style="border-radius: 24px;" />
</p>

<h1 align="center">VOLATOUCH</h1>

<p align="center">
  <strong>Zero-Dependency Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/v/volatouch.svg?color=6366f1&style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/pyversions/volatouch.svg?color=06b6d4&style=for-the-badge" alt="Python Versions" /></a>
  <a href="https://github.com/ugurturkerkebeci/volatouch/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/Dependencies-0_Packages-22c55e.svg?style=for-the-badge" alt="0 Dependencies" />
  <img src="https://img.shields.io/badge/Footprint-<100_KB-8b5cf6.svg?style=for-the-badge" alt="Ultra-Lightweight" />
  <img src="https://img.shields.io/badge/Platform-Windows-0284c7.svg?style=for-the-badge&logo=windows" alt="Platform: Windows" />
</p>

<p align="center">
  <a href="#quick-start">⚡ Quick Start</a> •
  <a href="#zero-dependency">🌟 Zero Dependencies</a> •
  <a href="#features">✨ Features</a> •
  <a href="#gestures">📱 Gestures</a> •
  <a href="#cli-usage">💻 CLI Usage</a> •
  <a href="#security">🛡️ Security</a> •
  <a href="#from-source">🛠️ From Source</a>
</p>

---

<a id="quick-start"></a>
## ⚡ Quick Start

Install and launch Volatouch with **ZERO third-party dependencies**:

```bash
# 1. Install via pip (instant download, <100 KB total size)
pip install volatouch

# 2. Launch the air control server
volatouch
```

Open the printed URL (e.g. `http://192.168.1.5:8000`) in **Safari** or **Chrome** on any smartphone connected to the same Wi-Fi.  
**No mobile app installation, no accounts, no bloat!**

---

<a id="zero-dependency"></a>
## 🌟 100% Zero-Dependency Architecture

Unlike traditional remote desktop tools that require hundreds of megabytes of third-party libraries (OpenCV, NumPy, FastAPI, Uvicorn, etc.), Volatouch is engineered from the ground up to be **completely self-contained**:

- **0 External Packages on PyPI:** Requires literally **0 dependencies** to install and run.
- **Native Windows GDI & GDI+ Capture:** Hardware-level screen capture (<2ms) and native JPEG compression via Win32 `ctypes` without requiring OpenCV or Pillow.
- **Built-in Asyncio HTTP & WebSocket Server:** RFC-6455 compliant WebSocket & static file server running on standard-library `asyncio` without FastAPI or Uvicorn.
- **Native Hardware Input Emulation:** Mouse motion, clicks, wheel scrolls, and Unicode typing powered directly by Win32 `SendInput` / `user32` APIs without pynput.
- **Pre-Bundled Web UI:** Complete React + Tailwind touch interface embedded directly in the package (~220 KB), with zero Node.js / npm requirement at runtime.

---

<a id="features"></a>
## ✨ Features

- **🚀 60 FPS Hardware Streaming:** Sub-millisecond latency screen mirror with 8-byte double timestamp headers and single-slot atomic queues.
- **🎯 Dual Input Modes:**
  - **Direct Target Mode:** Tap anywhere on your phone screen to instantly teleport the cursor to that desktop point.
  - **Relative Trackpad Mode:** Smooth multi-touch trackpad navigation with acceleration curves.
- **🏝️ Draggable Floating Action Island:**
  - Dedicated **L-Click** and **R-Click** buttons.
  - **HOLD / LOCKED Button:** Persistent left-click lock with tactile vibration feedback for dragging windows and files.
  - **UP & DOWN Scroll Buttons:** Dedicated micro-step mouse wheel scrollers.
  - **Collapsible Mini-Pill:** Compact mode keeps controls out of the way.
  - **Boundary Clamping:** Widgets automatically re-align to stay safely within the viewport across orientation changes.
- **⌨️ Built-In Virtual Keyboard:**
  - Full **QWERTY layout** with dynamic Caps / Shift switching.
  - **Sticky Modifiers:** `Ctrl`, `Shift`, `Alt`, and `Win (Super)` lock on tap for desktop combos (e.g., `Ctrl` + `C`).
  - Function keys (**F1–F12**) and navigation keys.
- **📱 Landscape Edge-to-Edge Fill:** Switch between **Fit** and **Fill** modes to eliminate black bars on widescreen mobile displays.
- **🌐 Bilingual UI:** Instant toggle between English and Turkish saved in `localStorage`.

---

<a id="gestures"></a>
## 📱 Gesture & Touch Cheatsheet

| Gesture / Action | Relative Mode | Direct Mode |
| :--- | :--- | :--- |
| **1-Finger Drag** | Relative Mouse Cursor Movement | Direct Cursor Navigation |
| **1-Finger Tap** | Left Click (Mouse 1) | Left Click at Touch Location |
| **2-Finger Tap** | Right Click (Mouse 2) | Right Click at Touch Location |
| **2-Finger Scroll** | Smooth Vertical Wheel Scroll | Smooth Vertical Wheel Scroll |
| **Long Press (>350ms)** | Drag & Drop (Left Mouse Down) | Drag & Drop at Location |
| **Island `[ HOLD ]`** | Toggles Left Button Lock | Toggles Left Button Lock |
| **Island `[ UP/DOWN ]`**| Mouse Scroll Wheel Increment | Mouse Scroll Wheel Increment |

---

<a id="cli-usage"></a>
## 💻 CLI Usage

Launch Volatouch with custom network and display parameters:

```text
usage: volatouch [-h] [--host HOST] [--port PORT] [--quality QUALITY]
                 [--scale SCALE] [--version]

Volatouch: Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi (Zero Dependencies).

options:
  -h, --help            Show this help message and exit
  --host HOST           Host network interface to bind (default: 0.0.0.0)
  -p PORT, --port PORT  Port to listen on (default: 8000)
  -q QUALITY, --quality QUALITY
                        Initial JPEG stream quality (10-100, default: 55)
  -s SCALE, --scale SCALE
                        Initial resolution scale (0.2-1.0, default: 0.70)
  -v, --version         Show program's version number and exit
```

### Examples:

```bash
# Run on custom port
volatouch -p 8080

# Run with higher image quality
volatouch -q 75 -s 0.85
```

---

<a id="security"></a>
## 🛡️ Security & Sandbox

1. **Subnet Verification (RFC-1918):** Only devices on the exact same `/24` local Wi-Fi subnet can access endpoints or establish WebSocket handshakes. External requests receive an immediate `403 Forbidden`.
2. **Strict Origin & CSP Protection:** Enforces modern `Content-Security-Policy`, `X-Frame-Options: DENY`, and strict frame-ancestors restrictions.
3. **Whitelisted Hardware Commands:** Only explicit, sanitized commands (`mouse_move`, `mouse_click`, `key_tap`, etc.) are processed. Arbitrary shell execution is impossible.
4. **Failsafe Key Release:** When a connection drops, all pressed keys and mouse buttons are instantly released via `input_ctrl.release_all()` to prevent stuck keys on your PC.

---

<a id="from-source"></a>
## 🛠️ Running From Source

```bash
# 1. Clone repository
git clone https://github.com/ugurturkerkebeci/volatouch.git
cd volatouch

# 2. Run immediately (0 dependencies needed!)
python run.py
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for full details.

---

<p align="center">
  Crafted with ❤️ by <a href="https://github.com/ugurturkerkebeci">Uğur Türker Kebeci</a>
</p>
