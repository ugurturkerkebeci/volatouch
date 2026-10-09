"""
Volatouch Standalone Asyncio HTTP & WebSocket (RFC 6455) Server
Zero external dependencies (Pure standard library).
"""

import asyncio
import os
import json
import socket
import ipaddress
import hashlib
import base64
import struct
import mimetypes
from typing import Dict, Optional, Tuple, Set

from volatouch.config import config, LOCAL_IP
from volatouch.platform import detect_platform

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Allowed input commands whitelist
ALLOWED_COMMANDS = {
    "mouse_move",
    "mouse_move_abs",
    "mouse_click",
    "mouse_down",
    "mouse_up",
    "mouse_scroll",
    "key_tap",
    "key_down",
    "key_up",
    "text_input",
    "reset_inputs",
    "android_nav"
}

def compute_ws_accept(sec_key: str) -> str:
    raw = (sec_key.strip() + WS_GUID).encode("latin-1")
    return base64.b64encode(hashlib.sha1(raw).digest()).decode("latin-1")

def encode_ws_frame(payload: bytes, opcode: int = 0x2) -> bytes:
    """Encode server-to-client unmasked WebSocket frame (RFC 6455)."""
    header = bytearray([0x80 | (opcode & 0x0F)])
    length = len(payload)
    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header.extend(struct.pack(">H", length))
    else:
        header.append(127)
        header.extend(struct.pack(">Q", length))
    return bytes(header) + payload

def is_same_network(client_ip_str: Optional[str], host_ip_str: str) -> bool:
    try:
        if not client_ip_str:
            return False
        client_ip = ipaddress.ip_address(client_ip_str)
        if client_ip.is_loopback:
            return True
        if not client_ip.is_private:
            return False
        host_ip = ipaddress.ip_address(host_ip_str)
        if client_ip.version == 4 and host_ip.version == 4:
            client_net = ipaddress.IPv4Network(f"{client_ip_str}/24", strict=False)
            host_net = ipaddress.IPv4Network(f"{host_ip_str}/24", strict=False)
            return client_net == host_net
        return True
    except Exception:
        return False


class VolatouchServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, mode: str = "auto"):
        self.host = host
        self.port = port
        self.platform = detect_platform(mode)

        if self.platform == "android":
            from volatouch.android_streamer import AndroidScreenStreamer
            from volatouch.android_input import AndroidInputController
            self.streamer = AndroidScreenStreamer()
            self.input_ctrl = AndroidInputController()
        else:
            from volatouch.screen_streamer import ScreenStreamer
            from volatouch.input_controller import InputController
            self.streamer = ScreenStreamer()
            self.input_ctrl = InputController()

        self.active_devices: Dict[str, int] = {}
        self.devices_lock: Optional[asyncio.Lock] = None
        self._server: Optional[asyncio.Server] = None

        # Resolve static web directory
        pkg_web = os.path.abspath(os.path.join(os.path.dirname(__file__), "web"))
        dev_web = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
        if os.path.exists(os.path.join(pkg_web, "index.html")):
            self.web_root = pkg_web
        elif os.path.exists(os.path.join(dev_web, "index.html")):
            self.web_root = dev_web
        else:
            self.web_root = pkg_web

    def _get_lock(self) -> asyncio.Lock:
        if self.devices_lock is None:
            self.devices_lock = asyncio.Lock()
        return self.devices_lock

    async def register_connect(self, client_ip: str):
        lock = self._get_lock()
        async with lock:
            prev = self.active_devices.get(client_ip, 0)
            self.active_devices[client_ip] = prev + 1
            if prev == 0:
                print(f"[+] Device connected: {client_ip} | Active devices: {len(self.active_devices)}", flush=True)

    async def register_disconnect(self, client_ip: str):
        lock = self._get_lock()
        async with lock:
            if client_ip in self.active_devices:
                self.active_devices[client_ip] -= 1
                if self.active_devices[client_ip] <= 0:
                    del self.active_devices[client_ip]
                    print(f"[-] Device disconnected: {client_ip} | Active devices: {len(self.active_devices)}", flush=True)

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if peer else "127.0.0.1"

        try:
            # 1. Subnet Verification (RFC-1918)
            if not is_same_network(client_ip, LOCAL_IP):
                err_body = b'{"error":"Forbidden","message":"Access Denied: Must be on the same local subnet."}'
                await self._send_http_response(writer, 403, "application/json", err_body)
                return

            # Read HTTP request header
            try:
                header_bytes = await reader.readuntil(b"\r\n\r\n")
            except Exception:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                return

            header_text = header_bytes.decode("latin-1", errors="ignore")
            lines = header_text.split("\r\n")
            if not lines or not lines[0]:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                return

            request_line = lines[0].split()
            if len(request_line) < 2:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                return

            method, path = request_line[0].upper(), request_line[1]

            headers: Dict[str, str] = {}
            for line in lines[1:]:
                if ": " in line:
                    k, v = line.split(": ", 1)
                    headers[k.lower()] = v.strip()

            # Check WebSocket upgrade
            is_ws = (
                "upgrade" in headers.get("connection", "").lower()
                and headers.get("upgrade", "").lower() == "websocket"
            )

            if is_ws:
                ws_key = headers.get("sec-websocket-key", "")
                if not ws_key:
                    writer.close()
                    await writer.wait_closed()
                    return

                accept_token = compute_ws_accept(ws_key)
                handshake = (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept_token}\r\n\r\n"
                )
                writer.write(handshake.encode("latin-1"))
                await writer.drain()

                if path.startswith("/ws/stream"):
                    await self._handle_ws_stream(reader, writer, client_ip)
                elif path.startswith("/ws/input"):
                    await self._handle_ws_input(reader, writer, client_ip)
                else:
                    writer.close()
                    await writer.wait_closed()
            else:
                await self._handle_http(method, path, headers, reader, writer)

        except Exception:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_http(self, method: str, path: str, headers: Dict[str, str], reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        clean_path = path.split("?")[0].lstrip("/")

        # API: /api/info
        if clean_path == "api/info" and method == "GET":
            info = {
                "status": "online",
                "lan_ip": LOCAL_IP,
                "port": self.port,
                "host_type": self.platform,
                "screen": {
                    "width": self.streamer.screen_width,
                    "height": self.streamer.screen_height
                },
                "stream": self.streamer.get_settings()
            }
            body = json.dumps(info).encode("utf-8")
            await self._send_http_response(writer, 200, "application/json", body)
            return

        # API: /api/settings
        if clean_path == "api/settings" and method == "POST":
            content_len = int(headers.get("content-length", 0))
            body_bytes = await reader.readexactly(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(body_bytes.decode("utf-8"))
                self.streamer.update_settings(quality=data.get("quality"), scale=data.get("scale"))
            except Exception:
                pass
            res_body = json.dumps({"status": "ok", "current": self.streamer.get_settings()}).encode("utf-8")
            await self._send_http_response(writer, 200, "application/json", res_body)
            return

        # Static file resolution
        if not clean_path or clean_path == "index.html":
            file_path = os.path.join(self.web_root, "index.html")
        else:
            file_path = os.path.join(self.web_root, clean_path.replace("/", os.sep))

        if not os.path.isfile(file_path):
            file_path = os.path.join(self.web_root, "index.html")

        if os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                if file_path.endswith(".js"):
                    content_type = "application/javascript"
                elif file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".html"):
                    content_type = "text/html; charset=utf-8"
                else:
                    content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                content = f.read()
            await self._send_http_response(writer, 200, content_type, content)
        else:
            err = b"<h1>404 - Web Assets Not Found</h1>"
            await self._send_http_response(writer, 404, "text/html", err)

    async def _send_http_response(self, writer: asyncio.StreamWriter, status: int, content_type: str, body: bytes):
        status_text = "200 OK" if status == 200 else ("404 Not Found" if status == 404 else f"{status} Status")
        headers = [
            f"HTTP/1.1 {status_text}",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(body)}",
            "Connection: close",
            "X-Content-Type-Options: nosniff",
            "X-Frame-Options: DENY",
            "X-XSS-Protection: 1; mode=block",
            "Referrer-Policy: strict-origin-when-cross-origin",
            "Permissions-Policy: accelerometer=(), camera=(), geolocation=(), microphone=()",
            "Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'none';"
        ]
        resp_data = ("\r\n".join(headers) + "\r\n\r\n").encode("latin-1") + body
        try:
            writer.write(resp_data)
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _read_ws_frame(self, reader: asyncio.StreamReader) -> Optional[Tuple[int, bytes]]:
        try:
            head = await reader.readexactly(2)
        except Exception:
            return None

        opcode = head[0] & 0x0F
        is_masked = (head[1] & 0x80) != 0
        length = head[1] & 0x7F

        if length == 126:
            ext = await reader.readexactly(2)
            length = struct.unpack(">H", ext)[0]
        elif length == 127:
            ext = await reader.readexactly(8)
            length = struct.unpack(">Q", ext)[0]

        if is_masked:
            mask = await reader.readexactly(4)
            payload_raw = await reader.readexactly(length)
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload_raw))
        else:
            payload = await reader.readexactly(length)

        return (opcode, payload)

    async def _handle_ws_stream(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_ip: str):
        await self.register_connect(client_ip)
        queue = self.streamer.subscribe()
        write_lock = asyncio.Lock()

        async def incoming_loop():
            try:
                while True:
                    frame = await self._read_ws_frame(reader)
                    if not frame:
                        break
                    opcode, payload = frame
                    if opcode == 0x8:  # Close
                        break
                    elif opcode == 0x9:  # Ping
                        pong_frame = encode_ws_frame(payload, opcode=0xA)
                        async with write_lock:
                            writer.write(pong_frame)
                            await writer.drain()
                    elif opcode == 0x1:  # Text
                        try:
                            data = json.loads(payload.decode("utf-8"))
                            t = data.get("type")
                            if t == "set_quality":
                                self.streamer.update_settings(quality=int(data.get("quality", 50)))
                            elif t == "set_scale":
                                self.streamer.update_settings(scale=float(data.get("scale", 0.65)))
                            elif t == "ping":
                                pong = json.dumps({"type": "pong", "time": data.get("time")}).encode("utf-8")
                                async with write_lock:
                                    writer.write(encode_ws_frame(pong, opcode=0x1))
                                    await writer.drain()
                        except Exception:
                            pass
            except Exception:
                pass

        recv_task = asyncio.create_task(incoming_loop())

        try:
            while not writer.is_closing():
                packet_bytes = await queue.get()
                wire_frame = encode_ws_frame(packet_bytes, opcode=0x2)
                async with write_lock:
                    writer.write(wire_frame)
                    await writer.drain()
        except Exception:
            pass
        finally:
            self.streamer.unsubscribe(queue)
            recv_task.cancel()
            try:
                await recv_task
            except (asyncio.CancelledError, Exception):
                pass
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            await self.register_disconnect(client_ip)

    async def _handle_ws_input(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_ip: str):
        await self.register_connect(client_ip)

        try:
            while True:
                frame = await self._read_ws_frame(reader)
                if not frame:
                    break
                opcode, payload = frame
                if opcode == 0x8:  # Close
                    break
                if opcode == 0x9:  # Ping
                    writer.write(encode_ws_frame(payload, opcode=0xA))
                    await writer.drain()
                    continue

                if opcode == 0x1:  # Text command
                    try:
                        cmd = json.loads(payload.decode("utf-8"))
                        cmd_type = cmd.get("type")
                        if cmd_type not in ALLOWED_COMMANDS:
                            continue

                        if cmd_type == "mouse_move_abs":
                            norm_x = float(cmd.get("norm_x", 0.0))
                            norm_y = float(cmd.get("norm_y", 0.0))
                            self.input_ctrl.move_mouse_abs(
                                norm_x, norm_y,
                                self.streamer.screen_width, self.streamer.screen_height,
                                self.streamer.screen_left, self.streamer.screen_top
                            )

                        elif cmd_type == "mouse_move":
                            dx = float(cmd.get("dx", 0.0))
                            dy = float(cmd.get("dy", 0.0))
                            self.input_ctrl.move_mouse(dx, dy)

                        elif cmd_type == "mouse_click":
                            button = str(cmd.get("button", "left"))[:10]
                            count = min(3, max(1, int(cmd.get("clicks", 1))))
                            self.input_ctrl.click_mouse(button, count)

                        elif cmd_type == "mouse_down":
                            button = str(cmd.get("button", "left"))[:10]
                            self.input_ctrl.mouse_down(button)

                        elif cmd_type == "mouse_up":
                            button = str(cmd.get("button", "left"))[:10]
                            self.input_ctrl.mouse_up(button)

                        elif cmd_type == "mouse_scroll":
                            dy = float(cmd.get("dy", 0.0))
                            dx = float(cmd.get("dx", 0.0))
                            self.input_ctrl.scroll_mouse(dx, dy)

                        elif cmd_type == "key_tap":
                            key = str(cmd.get("key", ""))[:20]
                            modifiers = [str(m)[:10] for m in cmd.get("modifiers", [])[:5]]
                            self.input_ctrl.key_tap(key, modifiers)

                        elif cmd_type == "key_down":
                            key = str(cmd.get("key", ""))[:20]
                            self.input_ctrl.key_down(key)

                        elif cmd_type == "key_up":
                            key = str(cmd.get("key", ""))[:20]
                            self.input_ctrl.key_up(key)

                        elif cmd_type == "text_input":
                            text = str(cmd.get("text", ""))[:500]
                            self.input_ctrl.type_text(text)

                        elif cmd_type == "android_nav":
                            action = str(cmd.get("action", ""))[:20]
                            if hasattr(self.input_ctrl, "android_nav"):
                                self.input_ctrl.android_nav(action)

                        elif cmd_type == "reset_inputs":
                            self.input_ctrl.release_all()

                    except Exception:
                        pass

        except Exception:
            pass
        finally:
            self.input_ctrl.release_all()
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            await self.register_disconnect(client_ip)

    async def run(self):
        loop = asyncio.get_running_loop()
        self.devices_lock = asyncio.Lock()
        self.streamer.set_event_loop(loop)
        self.streamer.start()

        self._server = await asyncio.start_server(
            self.handle_connection,
            self.host,
            self.port,
            reuse_address=True
        )

        print("\n" + "=" * 65)
        if self.platform == "android":
            print("      VOLATOUCH - ANDROID PHONE CONTROL (Plug & Play)")
        else:
            print("      VOLATOUCH - AIR CONTROL & TRACKPAD (PC Host)")
        print("=" * 65)
        print(f"  [+] Mode: {'Android Phone (Control Phone from PC Browser)' if self.platform == 'android' else 'PC Host (Control PC from Mobile Device)'}")
        print(f"  [+] Open in Browser: http://localhost:{self.port} (or http://{LOCAL_IP}:{self.port})")
        print("=" * 65)
        print("[*] Ready. Waiting for client connections...\n", flush=True)

        try:
            await self._server.serve_forever()
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            if self._server:
                self._server.close()
                try:
                    await self._server.wait_closed()
                except Exception:
                    pass
            self.input_ctrl.release_all()
            self.streamer.stop()

def run_server(host: str = "0.0.0.0", port: int = 8000, mode: str = "auto"):
    server = VolatouchServer(host=host, port=port, mode=mode)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        pass
