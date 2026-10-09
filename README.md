<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/banner.jpg" alt="Volatouch Banner" width="100%" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/ugurturkerkebeci/volatouch/main/assets/logo.jpg" alt="Volatouch Logo" width="120" style="border-radius: 24px;" />
</p>

<h1 align="center">VOLATOUCH V1.0.0</h1>

<p align="center">
  <strong>Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/v/volatouch.svg?color=6366f1&style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/volatouch/"><img src="https://img.shields.io/pypi/pyversions/volatouch.svg?color=06b6d4&style=for-the-badge" alt="Python Versions" /></a>
  <a href="https://github.com/ugurturkerkebeci/volatouch/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge" alt="License: MIT" /></a>
  <a href="https://github.com/ugurturkerkebeci/volatouch/stargazers"><img src="https://img.shields.io/github/stars/ugurturkerkebeci/volatouch?style=for-the-badge&color=eab308" alt="GitHub Stars" /></a>
  <a href="https://github.com/ugurturkerkebeci/volatouch/issues"><img src="https://img.shields.io/github/issues/ugurturkerkebeci/volatouch?style=for-the-badge&color=ec4899" alt="GitHub Issues" /></a>
  <img src="https://img.shields.io/badge/Footprint-Ultra--Lightweight-22c55e.svg?style=for-the-badge" alt="Ultra-Lightweight" />
  <img src="https://img.shields.io/badge/Platform-Windows-0284c7.svg?style=for-the-badge&logo=windows" alt="Platform: Windows" />
</p>

<p align="center">
  <a href="#quick-start">⚡ Quick Start</a> •
  <a href="#why-volatouch">🌟 Why Volatouch?</a> •
  <a href="#features">✨ Features</a> •
  <a href="#gestures">📱 Gestures</a> •
  <a href="#cli-usage">💻 CLI Usage</a> •
  <a href="#security">🛡️ Security</a> •
  <a href="#from-source">🛠️ From Source</a>
</p>

---

<a id="quick-start"></a>
## ⚡ Quick Start

Install and launch Volatouch in seconds from your command line:

```bash
# 1. Install via pip (ultra-lightweight package, <100 KB)
pip install volatouch

# 2. Start the air control server
volatouch
```

Once running, open the URL displayed in the terminal (e.g. `http://192.168.1.5:8000`) in **Safari** or **Chrome** on any phone connected to the same Wi-Fi.  
**No mobile app installation, no registration, no configuration required!**

---

<a id="why-volatouch"></a>
## 🌟 Why Volatouch?

- **🪶 100% Standalone & Zero-Bloat:**
  - **No 100 MB OpenCV Dependency:** Uses a lightweight PIL engine by default (~3 MB) with optional automatic OpenCV acceleration if available.
  - **Self-Contained Web Client:** The complete, modern React + Tailwind touch interface is pre-bundled directly within the package (~220 KB). You don't need Node.js, npm, or any frontend build step at runtime.
  - Total package wheel size is **under 100 KB**!

- **⚡ Hardware-Level 60 FPS & Near-Zero Latency:**
  - Screen frames captured at the hardware display level via `mss`.
  - Transmitted over WebSockets as raw **Binary ArrayBuffers** (no Base64 overhead).
  - Single-slot atomic queues (`asyncio.Queue(maxsize=1)`) prevent buffer bloat and frame queuing.
  - Rendered client-side on an HTML5 `<canvas>` using `createImageBitmap` and `requestAnimationFrame`.

- **🎯 Dual Navigation Modes:**
  - **Direct Target Mode:** Tap anywhere on your phone to instantly teleport the cursor to that point on your PC display.
  - **Relative Trackpad Mode:** Smooth trackpad navigation with acceleration and configurable sensitivity.

---

<a id="features"></a>
## ✨ Features

- **🏝️ Draggable Floating Action Island:**
  - Dedicated **L-Click** and **R-Click** buttons.
  - **HOLD / LOCKED Button:** One-touch left-click lock with tactile vibration feedback for moving windows and drag-and-drop.
  - **UP & DOWN Scroll Buttons:** Dedicated micro-step mouse wheel scrollers.
  - **Collapsible Mini-Pill:** Minimize the controls into a small floating dot to maximize visible screen real estate.
  - **Boundary Clamping:** Widgets automatically re-align to stay safely within the viewport on orientation change or fullscreen.

- **⌨️ Comprehensive Built-In Virtual Keyboard:**
  - Full **QWERTY layout** with dynamic Caps / Shift character switching.
  - **Sticky Modifier Keys:** `Ctrl`, `Shift`, `Alt`, and `Win (Super)` lock on tap (highlighted in indigo) for desktop shortcuts (e.g., `Ctrl` + `C`).
  - Function keys (**F1–F12**), navigation keys (`Esc`, `Tab`, `Home`, `End`), and a **Voice / Text drawer**.

- **📱 Landscape Edge-to-Edge Fill:**
  - Toggle between **Fit** (aspect ratio preservation) and **Fill** (edge-to-edge stretch) to eliminate black side bars on widescreen mobile devices.

- **🌐 English & Turkish Language Support:**
  - Default English interface with an instant Turkish language switcher saved in `localStorage`.

---

<a id="gestures"></a>
## 📱 Gesture & Touch Cheatsheet

| Gesture / Action | Relative Mode | Direct Mode |
| :--- | :--- | :--- |
| **1-Finger Drag** | Smooth Relative Mouse Movement | Direct Absolute Cursor Navigation |
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

Volatouch: Ultra-Low Latency Mobile Air Control & Wireless Trackpad for PC over Wi-Fi.

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

1. **Subnet Verification (RFC-1918):** Only devices within the same `/24` private local Wi-Fi subnet can access endpoints or establish WebSocket handshakes. External requests receive an immediate `403 Forbidden`.
2. **Strict Origin & CSP Protection:** Enforces modern `Content-Security-Policy`, `X-Frame-Options: DENY`, and strict frame-ancestors restrictions.
3. **Whitelisted Hardware Commands:** Only explicit, sanitized commands (`mouse_move`, `mouse_click`, `key_tap`, etc.) are processed. Arbitrary command execution is impossible.
4. **Failsafe Key Release:** When a WebSocket connection drops, all pressed keys and mouse buttons are instantly released via `input_ctrl.release_all()` to prevent stuck keys.

---

<a id="from-source"></a>
## 🛠️ Running From Source

If you want to clone and develop Volatouch locally:

```bash
# 1. Clone repository
git clone https://github.com/ugurturkerkebeci/volatouch.git
cd volatouch

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run directly (uses bundled web client)
python run.py
```

Optional: To modify and re-compile the frontend web interface:
```bash
cd frontend
npm install
npm run build
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for full details.

---

<p align="center">
  Crafted with ❤️ by <a href="https://github.com/ugurturkerkebeci">Uğur Türker Kebeci</a>
</p>
