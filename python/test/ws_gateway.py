import asyncio
import websockets
import serial
import configparser
import os
import json
import time
import threading
from flask import Flask, jsonify

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.cfg")

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
        port = config.get("Serial", "port", fallback="COM3")
        baud = config.getint("Serial", "baud_rate", fallback=115200)
        ws_port = config.getint("Server", "port", fallback=30010)
        return port, baud, ws_port
    return "COM3", 115200, 30010

class ESP32Gateway:
    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.ser = None
        self.lock = threading.Lock()
        self.connect_serial()

    def connect_serial(self):
        try:
            print(f"[*] Connecting to ESP32 on {self.port} at {self.baud} baud...")
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            if self.ser:
                self.ser.setDTR(False)
                self.ser.setRTS(False)
                time.sleep(2)
                print("[+] Serial connected.")
            else:
                print("[!] Serial connection failed.")
        except Exception as e:
            print(f"[!] Serial Error: {e}")
            self.ser = None

        # Startup test: Vibrate briefly to confirm connection
        if self.ser and self.ser.is_open:
            print("[*] Performing startup vibration test...")
            self.send_to_esp32("Vibrate:10;")
            time.sleep(1)
            self.send_to_esp32("Vibrate:0;")

    def send_to_esp32(self, cmd):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                # Silently try to reconnect once, but don't block
                self.connect_serial()
            
            if self.ser and self.ser.is_open:
                try:
                    full_cmd = f"{cmd.strip()}\n"
                    self.ser.write(full_cmd.encode())
                    print(f"[DEBUG] Sent to ESP32: {cmd.strip()}")
                except Exception as e:
                    print(f"[!] Send Error (Mode DUMMY): {e}")
                    self.ser = None
            else:
                print(f"[DUMMY] Serial not connected. Simulating: {cmd.strip()}")

    async def handle_ws(self, websocket, path):
        self.clients.add(websocket)
        print(f"[+] WebSocket Client Connected from {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"[DEBUG] WS Received: {message}")
                try:
                    data = json.loads(message)
                    m_type = data.get("type", "")
                    
                    if m_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                        continue
                    
                    if m_type == "access":
                        # Handshake response
                        await websocket.send(json.dumps({
                            "type": "access",
                            "data": {
                                "code": 200,
                                "message": "success"
                            }
                        }))
                        continue

                    # Handle legacy or direct commands
                    if isinstance(data, dict) and "command" in data:
                        cmd = data.get("command")
                        level = data.get("level", 0)
                        if cmd == "Vibrate":
                            self.send_to_esp32(f"Vibrate:{level};")
                except:
                    # Fallback for non-JSON or other formats
                    if message.startswith("Vibrate:"):
                        self.send_to_esp32(message + ";")
        except Exception as e:
            print(f"[!] WS Error: {e}")
        finally:
            self.clients.remove(websocket)

# Discovery Server (HTTP)
discovery_app = Flask(__name__)

@discovery_app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@discovery_app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

@discovery_app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@discovery_app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

WS_PORT = 30010
global_gateway = None

@discovery_app.route('/GetToys', methods=['GET'])
def get_toys():
    # Intiface and games look for this to discover local Lovense devices
    print("[DEBUG] Received GET /GetToys request")
    
    toy_info = {
        "id": "8dbf2e1a3c5d",
        "toyId": "8dbf2e1a3c5d",
        "name": "Max",
        "nickName": "Max",
        "type": "b",
        "status": 1,
        "battery": 100,
        "version": "1.0.0",
        "hVersion": "1",
        "fVersion": "1",
        "isSsl": 0,
        "domain": "127.0.0.1",
        "httpPort": 20010,
        "wsPort": 30010,
        "port": 30010
    }

    resp_data = {
        "code": 200,
        "message": "success",
        "result": True,
        "resultCode": 1,
        "data": {
            "toyList": { "8dbf2e1a3c5d": toy_info },
            "toys": [ toy_info ],
            "appVersion": "3.0.0",
            "stayConnect": 1,
            "isSsl": 0
        }
    }
    print(f"[DEBUG] Sending GET Response (Ultra): {json.dumps(resp_data)}")
    return jsonify(resp_data)

@discovery_app.route('/command', methods=['POST'])
def handle_http_command():
    from flask import request
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        print(f"[DEBUG] HTTP Command Received: {data}")
        
        cmd = data.get("command", "")
        action = data.get("action", "")

        if cmd in ["GetToys", "toy-list", "toy_list", "toy-status"]:
            toy_info = {
                "id": "8dbf2e1a3c5d",
                "toyId": "8dbf2e1a3c5d",
                "name": "Max",
                "nickName": "Max",
                "type": "b",
                "status": 1,
                "battery": 100,
                "version": "1.0.0",
                "hVersion": "1",
                "fVersion": "1",
                "isSsl": 0,
                "domain": "127.0.0.1",
                "httpPort": 20010,
                "wsPort": 30010,
                "port": 30010
            }
            resp_data = {
                "code": 200,
                "message": "success",
                "result": True,
                "resultCode": 1,
                "data": {
                    "toyList": { "8dbf2e1a3c5d": toy_info },
                    "toys": [ toy_info ],
                    "appVersion": "3.0.0",
                    "stayConnect": 1,
                    "isSsl": 0
                }
            }
            print(f"[DEBUG] Sending POST Response (Ultra): {json.dumps(resp_data)}")
            return jsonify(resp_data)
        
        if cmd == "Vibrate" or cmd == "Vibration":
            level = data.get("level", 0)
            if global_gateway:
                global_gateway.send_to_esp32(f"Vibrate:{level};")
            return jsonify({"code": 200, "message": "OK"})

        if global_gateway:
            if cmd == "Function" and action.startswith("Vibrate:"):
                level = action.split(":")[1]
                global_gateway.send_to_esp32(f"Vibrate:{level};")
            elif action == "Stop":
                global_gateway.send_to_esp32("Vibrate:0;")
            elif cmd == "Vibrate":
                level = data.get("level", 0)
                global_gateway.send_to_esp32(f"Vibrate:{level};")
        
        return jsonify({"code": 200, "message": "OK"})
    except Exception as e:
        print(f"[!] HTTP Command Error: {e}")
        return jsonify({"code": 400, "message": str(e)})

def run_discovery():
    global global_gateway
    # Discovery MUST be on 20010 for official Lovense Connect PC emulation
    # (Port 34567 is often used for mobile or Intiface, but 20010 is the PC standard)
    print("[*] Starting Discovery Server on http://127.0.0.1:20010")
    discovery_app.run(host='0.0.0.0', port=20010, debug=False, use_reloader=False)

def run_udp_broadcast():
    import socket
    # Lovense Connect uses UDP broadcast for discovery
    print("[*] Starting UDP Broadcast on port 34567 (pointing to 20010)")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Broadcast message telling apps where our HTTP server is
    msg = json.dumps({
        "type": "discover",
        "domain": "127.0.0.1",
        "httpPort": 20010,
        "wsPort": 30010,
        "name": "Lovense Connect"
    }).encode()
    
    try:
        while True:
            # Broadcast to the local network every 2 seconds
            sock.sendto(msg, ("255.255.255.255", 34567))
            time.sleep(2)
    except Exception as e:
        print(f"[!] UDP Broadcast Error: {e}")

async def run_ws_server(gateway, port):
    print(f"[*] Starting WebSocket Control Server on ws://0.0.0.0:{WS_PORT}")
    async with websockets.serve(global_gateway.handle_ws, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # run forever

def main():
    global global_gateway
    ser_port, baud, ws_port = load_config()
    global_gateway = ESP32Gateway(ser_port, baud)
    
    # Pre-parse common toy data
    toy_data = {
        "id": "1",
        "toyId": "1",
        "name": "Lovense Max",
        "nickName": "ESP32",
        "type": "L",
        "status": 1,
        "vVersion": 1,
        "hVersion": 1,
        "battery": 100,
        "domain": "127.0.0.1",
        "httpPort": 34567,
        "wsPort": 30010,
        "port": 30010
    }
    
    # Start Discovery Server (HTTP)
    threading.Thread(target=run_discovery, daemon=True).start()
    
    # Start UDP Broadcast Discovery
    threading.Thread(target=run_udp_broadcast, daemon=True).start()
    
    # Start WebSocket Server
    try:
        asyncio.run(run_ws_server(global_gateway, ws_port))
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")

if __name__ == "__main__":
    main()
