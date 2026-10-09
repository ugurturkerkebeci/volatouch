<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/banner.jpg" alt="Volatouch Banner" width="100%" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/logo.jpg" alt="Volatouch Logo" width="120" style="border-radius: 24px;" />
</p>

<h1 align="center">VOLATOUCH</h1>

<p align="center">
  <strong>Zero-Dependency Ultra-Low Latency Bidirectional Remote Control for PC & Android over Wi-Fi</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/v/volatouch.svg?color=6366f1&style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/pyversions/volatouch.svg?color=06b6d4&style=for-the-badge" alt="Python Versions" /></a>
  <a href="https://github.com/ugurturkerkebeci/volatouch/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/Dependencies-0_Packages-22c55e.svg?style=for-the-badge" alt="0 Dependencies" />
  <img src="https://img.shields.io/badge/Footprint-<100_KB-8b5cf6.svg?style=for-the-badge" alt="Ultra-Lightweight" />
  <img src="https://img.shields.io/badge/Platform-Windows_%7C_Android_(Termux)-0284c7.svg?style=for-the-badge" alt="Platform: Windows | Android" />
</p>

<p align="center">
  <a href="#quick-start">⚡ Quick Start</a> •
  <a href="#bidirectional">🔄 Bidirectional Modes</a> •
  <a href="#zero-dependency">🌟 Zero Dependencies</a> •
  <a href="#features">✨ Features</a> •
  <a href="#gestures">📱 Controls Cheatsheet</a> •
  <a href="#cli-usage">💻 CLI Usage</a> •
  <a href="#security">🛡️ Security</a> •
  <a href="#from-source">🛠️ From Source</a>
</p>

---

<a id="quick-start"></a>
## ⚡ Quick Start

Volatouch is a pure Python application with **ZERO third-party pip dependencies**.

### Scenario A: Control your PC from your Phone 📱 ➔ 💻
1. On your Windows PC, install and run:
   ```bash
   pip install volatouch
   volatouch
   ```
2. Open the printed URL (e.g. `http://192.168.1.5:8000`) in Chrome or Safari on your phone.
3. Your phone instantly becomes a wireless multi-touch trackpad, air mouse, and keyboard for your PC.

### Scenario B: Control your Android Phone from your PC 💻 ➔ 📱
1. On your Android phone (inside **Termux** or terminal):
   ```bash
   pkg install python
   pip install volatouch
   volatouch
   ```
2. Open the printed phone URL (e.g. `http://192.168.1.20:8000`) in any browser on your desktop computer.
3. Click, swipe, and scroll on your phone screen with your PC mouse, type directly into apps using your physical PC keyboard, and use the floating Android Navigation Bar (`Back`, `Home`, `Recents`, `Power`, `Volume`).

---

<a id="bidirectional"></a>
## 🔄 Smart Bidirectional Engine

Volatouch automatically detects the host environment and adapts its streaming and input pipelines:

| Mode | Host Device | Client Device | Capabilities |
| :--- | :--- | :--- | :--- |
| **PC Host** | Windows PC | Smartphone Browser | 60 FPS Win32 GDI+ desktop stream, Direct & Trackpad touch gestures, full virtual QWERTY keyboard, drag lock, mouse wheel. |
| **Android Host** | Android (Termux) | PC Desktop Browser | Native `/system/bin/screencap` stream, mouse click/drag touch emulation, mouse wheel swipe scrolling, physical PC keyboard sync, Android hardware navigation bar (`Back`, `Home`, `Recents`, `Power`, `Volume`). |

*You can also manually enforce a specific mode via CLI: `volatouch --mode pc` or `volatouch --mode phone`.*

---

<a id="zero-dependency"></a>
## 🌟 100% Zero-Dependency Architecture

Unlike heavy remote desktop applications requiring OpenCV, NumPy, FastAPI, Uvicorn, or pynput, Volatouch uses **only Python's standard library**:

- **0 External Packages on PyPI:** Pure Python standard library (`asyncio`, `subprocess`, `struct`, `ctypes`, `socket`, `time`, `os`).
- **Native Hardware Capture:**
  - **Windows:** Hardware-level screen capture (<2ms) and native JPEG compression via Win32 `ctypes` (`GDI32` and `GDIPlus`).
  - **Android:** Direct framebuffer capture via `/system/bin/screencap -p` with zero external image processing tools.
- **Built-in Asyncio HTTP & WebSocket Server:** RFC-6455 compliant WebSocket server and static file server running on standard library `asyncio`.
- **Hardware Input Emulation:**
  - **Windows:** Native `SendInput` / `user32` calls for pixel-accurate mouse and Unicode keyboard events.
  - **Android:** Native `/system/bin/input` injection for taps, swipes, text typing, and key events.
- **Pre-Bundled Web Client:** Complete React + Tailwind interface pre-compiled and bundled inside the package (~230 KB), requiring zero Node.js runtime.

---

<a id="features"></a>
## ✨ Key Features

- **🚀 High-Speed Hardware Streaming:** Low-latency video pipeline with 8-byte double timestamp headers for precise latency measurement.
- **🎯 Dual Touch Navigation Modes:**
  - **Direct Target Mode:** Tap anywhere to immediately position the cursor or touch event at that screen location.
  - **Relative Trackpad Mode:** Multi-touch trackpad navigation with smooth acceleration curves.
- **🏝️ Draggable Floating Action Island:**
  - Dedicated **L-Click** and **R-Click** action triggers.
  - **HOLD / LOCKED Button:** Persistent mouse-down lock with vibration feedback for seamless drag-and-drop operations.
  - **UP & DOWN Scroll Buttons:** Quick micro-step mouse wheel scrolling.
  - **Boundary Clamping:** Widgets automatically stay within viewports during rotation or fullscreen toggle.
- **🤖 Dedicated Android Navigation Bar:**
  - Floating pill when controlling Android: ◀ Back, ⌂ Home, ▢ Recents, ⚡ Power, 🔊 Volume Up, 🔉 Volume Down.
  - Right-clicking on the phone canvas automatically triggers the Android **Back** action.
- **⌨️ Dual Keyboard Options:**
  - Full **QWERTY On-Screen Keyboard** with Caps/Shift switching and sticky modifiers (`Ctrl`, `Alt`, `Shift`, `Win`).
  - **Physical Desktop Keyboard Sync:** Type directly on your physical computer keyboard to inject text into your Android phone.
- **📱 Responsive Display Modes:** Instant toggle between **Fit** (aspect ratio preservation) and **Fill** (zero black bars edge-to-edge).
- **🌐 Bilingual Support:** Instant toggle between English and Turkish.

---

<a id="gestures"></a>
## 📱 Controls & Gestures Cheatsheet

| Input Action | When Controlling PC (from Phone) | When Controlling Phone (from PC) |
| :--- | :--- | :--- |
| **Left Click / 1-Finger Tap** | Left mouse click | Touch tap at screen coordinates |
| **Right Click / 2-Finger Tap** | Right mouse click | Android **Back** navigation action |
| **Mouse Drag / 1-Finger Drag** | Move cursor or drag | Swipe / drag across screen |
| **Mouse Wheel / 2-Finger Scroll**| Scroll desktop page | Swipe scroll up / down |
| **Physical Keyboard Typing** | Type on virtual keyboard | Type directly into active phone input |
| **Navigation Pill** | N/A | Quick Back, Home, Recents, Power, Vol |

---

<a id="cli-usage"></a>
## 💻 CLI Usage

```text
usage: volatouch [-h] [--host HOST] [--port PORT] [--quality QUALITY]
                 [--scale SCALE] [--mode {auto,pc,phone}] [--version]

Volatouch: Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi (Zero Dependencies).

optional arguments:
  -h, --help            Show this help message and exit
  --host HOST           Host network interface to bind (default: 0.0.0.0)
  -p PORT, --port PORT  Port to listen on (default: 8000)
  -q QUALITY, --quality QUALITY
                        Initial stream quality (10-100, default: 55)
  -s SCALE, --scale SCALE
                        Initial resolution scale (0.2-1.0, default: 0.70)
  -m MODE, --mode {auto,pc,phone}
                        Execution mode: 'auto' (detect platform), 'pc' (control PC from phone), or 'phone' (control Android from PC)
  -v, --version         Show program's version number and exit
```

### Examples:

```bash
# Automatic environment detection (default)
volatouch

# Force phone host mode (when testing or running in Android terminal)
volatouch --mode phone

# Custom network port and high quality
volatouch -p 8080 -q 75 -s 0.85
```

---

<a id="security"></a>
## 🛡️ Security & Sandbox

1. **Subnet Verification (RFC-1918):** Only devices connected to the same private `/24` Wi-Fi subnet can access endpoints or establish WebSocket handshakes. External networks receive an immediate `403 Forbidden`.
2. **Strict Origin & CSP Protection:** Enforces modern `Content-Security-Policy`, `X-Frame-Options: DENY`, and strict frame-ancestor protections.
3. **Whitelisted Hardware Commands:** Only explicit, sanitized commands (`mouse_move`, `mouse_click`, `key_tap`, `android_nav`, etc.) are processed. Arbitrary command execution is impossible.
4. **Failsafe Release:** Whenever a connection drops, all pressed keys and buttons are instantly cleared to prevent stuck keys.

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
