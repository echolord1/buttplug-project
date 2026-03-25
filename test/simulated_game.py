import asyncio
import json
import websockets
import random
import time

async def send_vibration(websocket, level, device_index=0, msg_id=100):
    """Helper to send a ScalarCmd vibration level."""
    command = [
        {
            "ScalarCmd": {
                "Id": msg_id,
                "DeviceIndex": device_index,
                "Scalars": [
                    {"Index": 0, "Scalar": max(0.0, min(1.0, level)), "ActuatorType": "Vibrate"}
                ]
            }
        }
    ]
    await websocket.send(json.dumps(command))
    await websocket.recv()

# --- Game Event Patterns ---

async def event_combat(websocket, device_index):
    print("⚔️ Event: Combat Started (Punches)!")
    num_punches = random.randint(4, 8)
    
    for _ in range(num_punches):
        # High intensity punch pulse
        level = round(random.uniform(0.7, 1.0), 2)
        await send_vibration(websocket, level, device_index)
        await asyncio.sleep(random.uniform(0.1, 0.2)) # Duration of hit
        
        # Brief pause between punches
        await send_vibration(websocket, 0.0, device_index)
        await asyncio.sleep(random.uniform(0.15, 0.4)) # Gap between hits
    
    print("🏁 Combat Ended. Cooling down...")
    await send_vibration(websocket, 0.0, device_index)
    await asyncio.sleep(2.0) # Mandatory pause after combat

async def event_damage(websocket, device_index):
    print("💥 Event: Damage Received!")
    # One strong short pulse
    await send_vibration(websocket, 1.0, device_index)
    await asyncio.sleep(0.3)
    await send_vibration(websocket, 0.0, device_index)
    await asyncio.sleep(0.5)

async def event_pickup(websocket, device_index):
    print("💎 Event: Item Pickup!")
    # Double pulse (pip-pip)
    for _ in range(2):
        await send_vibration(websocket, 0.6, device_index)
        await asyncio.sleep(0.15)
        await send_vibration(websocket, 0.0, device_index)
        await asyncio.sleep(0.1)
    await asyncio.sleep(0.5)

async def event_ambient(websocket, device_index):
    print("🍃 Event: Ambient / Stealth...")
    duration = random.uniform(2.0, 4.0)
    # Steady low hum
    level = round(random.uniform(0.1, 0.15), 2)
    await send_vibration(websocket, level, device_index)
    await asyncio.sleep(duration)
    await send_vibration(websocket, 0.0, device_index)
    await asyncio.sleep(0.5)

async def simulate_game():
    uri = "ws://127.0.0.1:12345"
    print(f"🎮 Connecting to Gateway at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Gateway!")
            
            # 1. Handshake
            handshake = [{"RequestServerInfo": {"Id": 1, "ClientName": "Simulated Game Pro", "MessageVersion": 3}}]
            await websocket.send(json.dumps(handshake))
            await websocket.recv()
            
            # 2. Start Scanning
            await websocket.send(json.dumps([{"StartScanning": {"Id": 2}}]))
            
            # Wait for DeviceAdded
            while True:
                resp = json.loads(await websocket.recv())
                if any("DeviceAdded" in msg for msg in resp) or any("Ok" in msg for msg in resp):
                    break
            
            print("\n[✔] Simulation Ready. Sending dynamic events...")
            device_index = 0
            
            events = [event_combat, event_damage, event_pickup, event_ambient]
            weights = [0.4, 0.2, 0.2, 0.2] # Combat is more frequent
            
            try:
                for i in range(15): # Run 15 events
                    event_func = random.choices(events, weights=weights)[0]
                    await event_func(websocket, device_index)
                    await asyncio.sleep(1.0) # Gap between different events
                
                print("\n🏁 All simulation events completed.")
                
            except asyncio.CancelledError:
                print("\n🛑 Simulation interrupted. Cleaning up...")
                raise
            except Exception as e:
                print(f"❌ Unexpected Loop Error: {e}")
            finally:
                print("🧹 Stopping all haptics...")
                try:
                    await send_vibration(websocket, 0.0, device_index)
                    print("✅ Stopped.")
                except:
                    pass
    
    except ConnectionRefusedError:
        print("❌ Error: Gateway not found. Run 'main.py' first.")
    except websockets.ConnectionClosed:
        print("🔌 Gateway disconnected.")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_game())
