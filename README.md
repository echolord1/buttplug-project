# ⚡ Buttplug Project: Buttplug.io Serial Gateway ⚡

This project is a Python-based Buttplug.io (v3) protocol gateway that connects serial devices (like the ESP32-CAM) directly to games and Buttplug clients, eliminating the need for Intiface Central.

- **Python Version**: Recommended `3.12.13` (managed via `uv`)

## 📊 Data Flow

```mermaid
graph LR
    A[Game Event] -->|Buttplug.io/Intiface Protocol| B[Python Gateway]
    B -->|USB-Serial Protocol| C[ESP32-CAM]
    C -->|Proprietary Bluetooth| D[Generic Chinese Toy]
```

## 🚀 Setup and Verification Flow

This project uses [uv](https://docs.astral.sh/uv/) for dependency and environment management.

### 1. Preparation

- **Configure Firmware**: Edit `PlatformIO/config.cfg` to set your initial serial and server parameters for the ESP32.
- **Configure Gateway**: Edit `config.yaml` in the root directory. Ensure the `Serial: port` matches your ESP32-CAM COM port.

![ESP32-CAM Hardware](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/esp32-cam-mb.png)
> [!NOTE]
> This project was successfully tested and verified using the **ESP32-CAM-MB** model shown above (featuring built-in **WiFi and Bluetooth**).
- **USB Driver (Windows 11)**: Ensure you have the `USB-SERIAL CH340 v3.7.2022.1` driver installed.
  
  ![CH340 Driver](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/drive%20USB-SERIAL%20CH340%20v3.7.2022.1.png)
  ![Driver Property](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/drive%20property.png)

### 2. Firmware Installation

1. Connect your **ESP32-CAM** to your PC.
2. Turn on your **Bluetooth Toy** (it must be on before the next steps).
3. Install the PlatformIO tools and upload the firmware:

```powershell
uv sync
cd PlatformIO
uv run pio run -e esp32cam -t upload
```

#### Step-by-Step Installation Screenshots:
![Install 1](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/install-1.png)
![Install 2](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/install-2.png)
![Install 3](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/install-3.png)
![Install 4](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/install-4.png)

### 3. Connection Test (Manual Verification)

Before starting the gateway, verify that the ESP32 can control the toy directly:

```powershell
uv run python ..\test\test.py
```

If the toy vibrates correctly, your serial-to-Bluetooth bridge is ready.

### 4. Running the Gateway

1. Start the gateway server:
   ```powershell
   cd ..
   uv run python main.py
   ```
2. **Success Confirmation**: When the gateway connects to the ESP32, the toy will **vibrate briefly**. This confirms the software and hardware are talking.

![Gateway Success](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/gateway.png)

### 5. Game Integration (Simulated or Real)

For a quick test without launching a real game, you can use our built-in simulator:
```powershell
uv run python test/simulated_game.py
```

![Simulated Game Success](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/simulated_game.png)
This script will:
- Connect to your Gateway via WebSocket.
- Perform the Buttplug handshake.
- Send random combat-like vibration events.

Alternatively, connect your real game (Femboy Survival, etc.) following the standard [Buttplug.io](https://buttplug.io) interface.

## ✅ Verified Test Results

Our comprehensive testing has confirmed the following successes:

1.  **Firmware Upload**: Successfully flashed the ESP32-CAM via PlatformIO with correct serial configurations.
2.  **Hardware Handshake**: Verified that the ESP32-CAM correctly bridges to Lovense-compatible hardware upon gateway connection.
3.  **Protocol Emulation**: Confirmed that the Python Gateway correctly emulates a Buttplug.io server, allowing external clients to discover and control the device.
4.  **Game Simulation**: The `simulated_game.py` test (as shown above) successfully performs the handshake and sends complex haptic events like the new **"Punch" Combat Pattern**.

![Music Vibes Integration](file:///c:/Users/echol/OneDrive/Documentos/GitHub/buttplug-project/doc/images/music-vibes.png)
_Example of successful haptic integration using the [Music Vibes](https://github.com/Shadlock0133/music-vibes/releases) software._

---

### ⚠️ Important Usage Tips

- **Order of Operations**: Always follow this sequence for a stable connection:
  1. Connect **ESP32** via USB.
  2. Start the **Python Gateway** (`uv run python main.py`).
  3. Launch the **Game**.
- **Reconnecting**: If you restart the Python Gateway for any reason, you **must close and reopen the game** to re-establish the Buttplug handshake.
- **Stopping**: To safely shut down the gateway, press `Ctrl+C` in the terminal. This will automatically send a stop signal to your hardware.

## 🛡️ Safety (Watchdog)

The Gateway includes an automatic **Safety Watchdog**:

- If vibration lasts for more than **2 seconds** (configurable) without a new update command or stop command, the Gateway sends an emergency `Vibrate:0` command to the hardware.
- This protects against game crashes or unexpected disconnections.

## 📁 Structure

- `main.py`: WebSocket Gateway entry point.
- `buttplug/`: Protocol implementation and serial connector (derived from [buttplug-py](https://github.com/buttplugio/buttplug-py)).
- `test/test.py`: Direct Serial communication test.
- `test/simulated_game.py`: Full WebSocket Gateway connection simulator.
- `config.yaml`: Central configuration file.
- `PlatformIO/`: C++ source code for the ESP32-CAM (use PlatformIO to upload).

## 🔖 Credits and License

- **Solution Developer**: [EchoLord](https://github.com/echolord1)
- **Buttplug Library**: The core protocol logic in the `buttplug/` directory is based on the [buttplugio/buttplug-py](https://github.com/buttplugio/buttplug-py) repository.
- **License**: This project follows the **BSD 3-Clause License**. See the original [LICENSE](https://github.com/buttplugio/buttplug-py/blob/master/LICENSE) for full details.

## ⚖️ Disclaimer

- **Testing Purposes Only**: All protocol emulations and features in this project are intended for testing and personal research only.
- **Non-Commercial**: This project is **not** for commercial use.
- **Protocol Notice**: This implementation is a custom bridge and is not affiliated with, endorsed by, or meant to replace official hardware or protocols from Lovense or other manufacturers.

---

_Maintained by EchoLord_
