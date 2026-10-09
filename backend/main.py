import asyncio
import json
import logging
import os
import ipaddress
import math
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

try:
    from volatouch.config import config, LOCAL_IP
    from volatouch.screen_streamer import ScreenStreamer
    from volatouch.input_controller import InputController
except ImportError:
    from config import config, LOCAL_IP
    from screen_streamer import ScreenStreamer
    from input_controller import InputController

# Silence third-party logs (uvicorn, websockets, asyncio)
for log_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "websockets", "asyncio", "fastapi"]:
    logging.getLogger(log_name).setLevel(logging.CRITICAL)

logger = logging.getLogger("volatouch")
logger.setLevel(logging.WARNING)

streamer = ScreenStreamer()
input_ctrl = InputController()

# Active device tracking (IP -> socket count)
active_device_sockets: Dict[str, int] = {}
devices_lock = asyncio.Lock()

async def register_device_connect(client_ip: str):
    async with devices_lock:
        prev_count = active_device_sockets.get(client_ip, 0)
        active_device_sockets[client_ip] = prev_count + 1
        if prev_count == 0:
            total_unique = len(active_device_sockets)
            print(f"[+] Device connected: {client_ip} | Active devices: {total_unique}", flush=True)

async def register_device_disconnect(client_ip: str):
    async with devices_lock:
        if client_ip in active_device_sockets:
            active_device_sockets[client_ip] -= 1
            if active_device_sockets[client_ip] <= 0:
                del active_device_sockets[client_ip]
                total_unique = len(active_device_sockets)
                print(f"[-] Device disconnected: {client_ip} | Active devices: {total_unique}", flush=True)

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
    "reset_inputs"
}

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

def validate_origin(headers: Any, host_ip: str) -> bool:
    origin = headers.get("origin")
    if not origin:
        return True
    origin = origin.lower()
    return "localhost" in origin or "127.0.0.1" in origin or host_ip in origin

@asynccontextmanager
async def lifespan(app: FastAPI):
    streamer.set_event_loop(asyncio.get_running_loop())
    streamer.start()
    print("\n" + "="*65)
    print("                 VOLATOUCH - AIR CONTROL SYSTEM")
    print("="*65)
    print(f"  [+] Local Network URL: http://{LOCAL_IP}:{config.port}")
    print("="*65)
    print("[*] Ready. Waiting for client connections...\n", flush=True)
    yield
    input_ctrl.release_all()
    streamer.stop()

app = FastAPI(title="Volatouch Backend", lifespan=lifespan)

# Allow local CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{LOCAL_IP}:{config.port}", f"http://localhost:{config.port}", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security headers & Subnet verification middleware
@app.middleware("http")
async def security_headers_and_network_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else None
    
    if not is_same_network(client_ip, LOCAL_IP):
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": f"Access Denied: You must be connected to the same local Wi-Fi subnet ({LOCAL_IP}) to control this PC."
            }
        )

    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none';"
    )
    return response

@app.get("/api/info")
async def get_info():
    settings = streamer.get_settings()
    return {
        "status": "online",
        "lan_ip": LOCAL_IP,
        "port": config.port,
        "screen": {
            "width": streamer.screen_width,
            "height": streamer.screen_height
        },
        "stream": settings
    }

@app.post("/api/settings")
async def update_settings(payload: Dict[str, Any]):
    streamer.update_settings(
        quality=payload.get("quality"),
        scale=payload.get("scale")
    )
    return {"status": "ok", "current": streamer.get_settings()}


@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host if websocket.client else None
    if not is_same_network(client_ip, LOCAL_IP) or not validate_origin(websocket.headers, LOCAL_IP):
        await websocket.close(code=1008, reason="Policy Violation")
        return

    await websocket.accept()
    if client_ip:
        await register_device_connect(client_ip)

    client_queue = streamer.subscribe()

    async def incoming_listener():
        try:
            while True:
                msg_text = await websocket.receive_text()
                if len(msg_text) > 4096:
                    continue
                try:
                    data = json.loads(msg_text)
                    msg_type = data.get("type")
                    if msg_type == "set_quality":
                        q = int(data.get("quality", 50))
                        streamer.update_settings(quality=max(10, min(95, q)))
                    elif msg_type == "set_scale":
                        s = float(data.get("scale", 0.65))
                        streamer.update_settings(scale=max(0.2, min(1.0, s)))
                    elif msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "time": data.get("time")}))
                except Exception:
                    pass
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    receiver_task = asyncio.create_task(incoming_listener())

    try:
        while True:
            # Instant asyncio wakeup upon frame encoding - ZERO delay, ZERO polling
            frame_bytes = await client_queue.get()
            await websocket.send_bytes(frame_bytes)
    except Exception:
        pass
    finally:
        streamer.unsubscribe(client_queue)
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass
        if client_ip:
            await register_device_disconnect(client_ip)


@app.websocket("/ws/input")
async def websocket_input_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host if websocket.client else None
    if not is_same_network(client_ip, LOCAL_IP) or not validate_origin(websocket.headers, LOCAL_IP):
        await websocket.close(code=1008, reason="Policy Violation")
        return

    await websocket.accept()
    if client_ip:
        await register_device_connect(client_ip)

    try:
        while True:
            raw_data = await websocket.receive_text()
            if len(raw_data) > 16384:
                continue

            try:
                cmd = json.loads(raw_data)
                cmd_type = cmd.get("type")

                if cmd_type not in ALLOWED_COMMANDS:
                    continue

                if cmd_type == "mouse_move_abs":
                    norm_x = float(cmd.get("norm_x", 0.0))
                    norm_y = float(cmd.get("norm_y", 0.0))
                    if not (math.isnan(norm_x) or math.isnan(norm_y)):
                        input_ctrl.move_mouse_abs(
                            norm_x, norm_y,
                            streamer.screen_width, streamer.screen_height,
                            streamer.screen_left, streamer.screen_top
                        )

                elif cmd_type == "mouse_move":
                    dx = float(cmd.get("dx", 0.0))
                    dy = float(cmd.get("dy", 0.0))
                    if not (math.isnan(dx) or math.isnan(dy) or math.isinf(dx) or math.isinf(dy)):
                        input_ctrl.move_mouse(dx, dy)

                elif cmd_type == "mouse_click":
                    button = str(cmd.get("button", "left"))[:10]
                    count = min(3, max(1, int(cmd.get("clicks", 1))))
                    input_ctrl.click_mouse(button, count)

                elif cmd_type == "mouse_down":
                    button = str(cmd.get("button", "left"))[:10]
                    input_ctrl.mouse_down(button)

                elif cmd_type == "mouse_up":
                    button = str(cmd.get("button", "left"))[:10]
                    input_ctrl.mouse_up(button)

                elif cmd_type == "mouse_scroll":
                    dy = float(cmd.get("dy", 0.0))
                    dx = float(cmd.get("dx", 0.0))
                    if not (math.isnan(dy) or math.isinf(dy)):
                        input_ctrl.scroll_mouse(dx, dy)

                elif cmd_type == "key_tap":
                    key = str(cmd.get("key", ""))[:20]
                    modifiers = [str(m)[:10] for m in cmd.get("modifiers", [])[:5]]
                    input_ctrl.key_tap(key, modifiers)

                elif cmd_type == "key_down":
                    key = str(cmd.get("key", ""))[:20]
                    input_ctrl.key_down(key)

                elif cmd_type == "key_up":
                    key = str(cmd.get("key", ""))[:20]
                    input_ctrl.key_up(key)

                elif cmd_type == "text_input":
                    text = str(cmd.get("text", ""))[:500]
                    input_ctrl.type_text(text)

                elif cmd_type == "reset_inputs":
                    input_ctrl.release_all()

            except Exception:
                pass

    except Exception:
        pass
    finally:
        input_ctrl.release_all()
        if client_ip:
            await register_device_disconnect(client_ip)


# Serve built frontend
package_web_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "web"))
dev_web_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

if os.path.exists(os.path.join(package_web_path, "index.html")):
    frontend_dist_path = package_web_path
elif os.path.exists(os.path.join(dev_web_path, "index.html")):
    frontend_dist_path = dev_web_path
else:
    frontend_dist_path = package_web_path

assets_dist_path = os.path.join(frontend_dist_path, "assets")

if os.path.exists(assets_dist_path):
    app.mount("/assets", StaticFiles(directory=assets_dist_path), name="assets")

@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    file_path = os.path.join(frontend_dist_path, catchall)
    if catchall and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    index_file = os.path.join(frontend_dist_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"error": "Frontend not found. Please build or install package correctly."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("volatouch.main:app", host=config.host, port=config.port, log_level="warning", access_log=False)
