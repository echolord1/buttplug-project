"""Buttplug Gateway - Bridging Serial Hardware to WebSockets"""

import asyncio
import os
import yaml
import json
import websockets
from typing import Any

from buttplug.serial_connector import SerialConnector
from buttplug._messages.base import parse_messages


async def handle_client(websocket, connector: SerialConnector, config_settings):
    """Handle a single WebSocket client connection."""
    print(f"[!] New client connected from {websocket.remote_address}")
    
    # Callback to push messages (like DeviceAdded) to the client
    async def push_to_client(msg):
        try:
            # Ensure we wrap the message in a list as per protocol
            resp_list = msg.to_protocol()
            resp_json = json.dumps(resp_list)
            print(f"[RAW OUT] {resp_json}")
            await websocket.send(resp_json)
        except Exception as e:
            print(f"Error sending pushed message: {e}")

    connector.reset_discovery()
    connector.set_message_callback(push_to_client)
    
    try:
        async for message_str in websocket:
            try:
                data = json.loads(message_str)
                
                # Filter noisy logs if configured
                log_sensors = config_settings.get("Gateway", {}).get("log_sensor_reads", True)
                is_noisy = any(k in ["SensorReadCmd", "Ping"] for msg in data for k in msg.keys())
                
                if not is_noisy or log_sensors:
                    print(f"[RAW IN] {data}")
                
                messages = parse_messages(data)
            except Exception as e:
                print(f"Error parsing client message: {e}")
                continue
            
            # Process each message
            all_responses = []
            for msg in messages:
                resp = await connector.send(msg)
                if resp:
                    all_responses.extend(resp.to_protocol())
            
            # Send collected responses
            if all_responses:
                resp_json = json.dumps(all_responses)
                print(f"[RAW OUT] {resp_json}")
                await websocket.send(resp_json)
                
    except websockets.ConnectionClosed:
        print(f"[!] Client {websocket.remote_address} disconnected")
    except Exception as e:
        import traceback
        print(f"[!] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
    finally:
        print("[!] Cleaning up client connection.")
        await connector.stop()
        connector.set_message_callback(None)


async def main():
    print("===========================================")
    print("      Buttplug.io Protocol Gateway")
    print("===========================================\n")

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(config_path):
        print(f"Error: config.yaml not found at {config_path}")
        return

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error parsing config.yaml: {e}")
        return

    serial_cfg = config.get("Serial", {})
    port = serial_cfg.get("port")
    baud = serial_cfg.get("baud_rate", 115200)
    device_settings = config.get("Device")

    if not port or not device_settings:
        print("Error: Missing Serial or Device config in config.yaml")
        return

    connector = SerialConnector(port=port, baud=baud, settings=device_settings)
    
    print(f"Connecting to Serial {port} at {baud} baud...")
    try:
        await connector.connect()
    except Exception as e:
        print(f"ERROR: Could not open serial port: {e}")
        return
    print("Serial Connected!\n")

    gateway_cfg = config.get("Gateway", {})
    server_host = gateway_cfg.get("host", "127.0.0.1")
    server_port = gateway_cfg.get("port", 12345)
    
    print(f"📡 Starting Buttplug Gateway Server on ws://{server_host}:{server_port}")
    print(f"👉 To use with games, set the server address to: {server_host}:{server_port}")
    print("\n[TIP] Press Ctrl+C to stop the gateway (vibrations will stop automatically).")
    print("Waiting for clients...\n")

    async with websockets.serve(
        lambda ws: handle_client(ws, connector, config), 
        server_host, 
        server_port
    ):
        print("--- GATEWAY ACTIVE ---")
        try:
            await asyncio.Future() 
        except asyncio.CancelledError:
            pass
        finally:
            await connector.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
