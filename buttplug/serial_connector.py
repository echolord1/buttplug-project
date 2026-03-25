"""Serial connector for Buttplug devices.
Bridges the Buttplug message protocol to raw serial commands.
"""

from __future__ import annotations

import asyncio
import serial
from typing import TYPE_CHECKING, Any, Callable

from buttplug._messages import (
    ButtplugMessage,
    ServerInfo,
    DeviceList,
    Ok,
    ScanningFinished,
    Error,
)
from buttplug._messages.device_info import (
    DeviceInfo,
    DeviceAdded,
    DeviceFeatureDefinition,
    FeatureOutputDefinition,
)
from buttplug._messages.commands import OutputCmd, SensorReadCmd, SensorReading, StopCmd, ScalarCmd, StopDeviceCmd
from buttplug.enums import ErrorCode, OutputType

if TYPE_CHECKING:
    from collections.abc import Awaitable


class SerialConnector:
    """Serial connector that emulates a Buttplug server.
    
    This allows a direct serial device to be used with the ButtplugClient
    as if it were a native device on a server.
    """

    def __init__(self, port: str, baud: int = 115200, settings: dict | None = None) -> None:
        self._port = port
        self._baud = baud
        self._connected = False
        self._ser: serial.Serial | None = None
        self._last_vibrate_level = -1
        
        # Load Device Settings from Config
        device_cfg = settings or {}
        self._device_name = device_cfg.get("name", "Lovense Device")
        self._device_index = int(device_cfg.get("index", 0))
        self._timing_gap = int(device_cfg.get("timing_gap", 100))
        self._vibration_steps = int(device_cfg.get("vibration_steps", 20))
        self._vibration_cmd_fmt = device_cfg.get("vibration_command", "Vibrate:{level}\n").replace("\\n", "\n")
        self._vibration_timeout_ms = int(device_cfg.get("vibration_timeout_ms", 2000))
        self._enable_startup_test = str(device_cfg.get("enable_startup_test", "true")).lower() == "true"
        
        self._timeout_task: asyncio.Task | None = None
        
        # Callbacks
        self._on_message: Callable[[ButtplugMessage], Awaitable[None]] | None = None
        self._on_disconnect: Callable[[], Awaitable[None]] | None = None
        
        # Discovery state to prevent duplicates
        self._device_already_sent = False

    @property
    def connected(self) -> bool:
        return self._connected

    def set_message_callback(self, callback: Callable[[ButtplugMessage], Awaitable[None]]) -> None:
        self._on_message = callback

    def set_disconnect_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_disconnect = callback

    async def connect(self) -> None:
        if self._connected:
            return
        
        try:
            self._ser = serial.Serial(self._port, self._baud, timeout=1, write_timeout=2)
            self._ser.setDTR(False)
            self._ser.setRTS(False)
            await asyncio.sleep(1) # Wait for ESP32 boot
            self._connected = True
            
            if self._enable_startup_test:
                print("[DEBUG] Sending startup vibration test...")
                self._write_serial(self._vibration_cmd_fmt.format(level=int(self._vibration_steps/2)))
                await asyncio.sleep(1.0)
                self._write_serial(self._vibration_cmd_fmt.format(level=0))
        except Exception as e:
            print(f"[!] SERIAL ERROR: Failed to write to {self._port}: {e}")

    async def disconnect(self) -> None:
        self._connected = False
        if self._ser:
            self._ser.close()
            self._ser = None
        if self._on_disconnect:
            await self._on_disconnect()

    def _refresh_timeout(self) -> None:
        """Restarts the vibration watchdog timer."""
        if self._timeout_task:
            self._timeout_task.cancel()
        
        async def _timeout_vibration():
            await asyncio.sleep(self._vibration_timeout_ms / 1000.0)
            print(f"[WATCHDOG] Safety timeout reached ({self._vibration_timeout_ms}ms). Stopping vibration.")
            self._write_serial(self._vibration_cmd_fmt.format(level=0))
            self._last_vibrate_level = 0
            
        self._timeout_task = asyncio.create_task(_timeout_vibration())

    async def stop(self) -> None:
        """Emergency stop for all vibrations."""
        print("[DEBUG] Emergency stop (stop() method called)")
        if self._timeout_task:
            self._timeout_task.cancel()
        self._write_serial(self._vibration_cmd_fmt.format(level=0))
        self._last_vibrate_level = 0
        self._device_already_sent = False

    def reset_discovery(self) -> None:
        """Resets the discovery flag for new client sessions."""
        self._device_already_sent = False

    def _write_serial(self, cmd: str) -> None:
        """Helper to write to the serial port with basic error handling."""
        if self._ser and self._connected:
            try:
                self._ser.write(cmd.encode("ascii"))
                self._ser.flush()
            except Exception as e:
                print(f"Serial Write Error: {e}")

    async def _emit_device_added(self) -> None:
        """Delayed push of DeviceAdded to ensure client is ready."""
        if self._device_already_sent:
            print("[DEBUG] Device already reported to client, skipping DeviceAdded push.")
            return

        await asyncio.sleep(0.5)
        if self._on_message:
            self._device_already_sent = True
            device_info = DeviceAdded(
                id=0,
                device_name=self._device_name,
                device_index=self._device_index,
                device_messages={
                    "ScalarCmd": [
                        {"ActuatorType": "Vibrate", "FeatureDescriptor": "", "StepCount": self._vibration_steps}
                    ],
                    "SensorReadCmd": [
                        {
                            "FeatureDescriptor": "battery Level",
                            "SensorRange": [[0, 100]],
                            "SensorType": "Battery"
                        }
                    ],
                    "StopDeviceCmd": {}
                }
            )
            await self._on_message(device_info)

    async def _emit_scanning_finished(self) -> None:
        """Delayed push of ScanningFinished."""
        await asyncio.sleep(1.5)
        if self._on_message:
            await self._on_message(ScanningFinished(id=0))

    async def send(self, message: ButtplugMessage) -> ButtplugMessage | None:
        """Process an incoming Buttplug message and return a response if required."""
        msg_type = message.get_message_type()
        msg_id = getattr(message, "id", 0)

        handle_map = {
            "RequestServerInfo": self._handle_server_info,
            "RequestDeviceList": self._handle_device_list,
            "StartScanning": self._handle_start_scanning,
            "StopScanning": self._handle_stop_scanning,
            "ScalarCmd": self._handle_scalar_cmd,
            "StopDeviceCmd": self._handle_stop_device,
            "StopCmd": self._handle_stop_all,
            "SensorReadCmd": self._handle_sensor_read,
            "Ping": self._handle_ping,
        }

        if msg_type in handle_map:
            return await handle_map[msg_type](message, msg_id)
        
        return Error(id=msg_id, error_message=f"Unsupported message: {msg_type}", error_code=ErrorCode.UNKNOWN)

    async def _handle_server_info(self, msg, msg_id):
        return ServerInfo(
            id=msg_id,
            server_name="Buttplug.io Serial Gateway",
            message_version=3,
            max_ping_time=0
        )

    async def _handle_device_list(self, msg, msg_id):
        device_info = DeviceInfo(
            device_name=self._device_name,
            device_index=self._device_index,
            device_messages={
                "ScalarCmd": [
                    {"ActuatorType": "Vibrate", "FeatureDescriptor": "", "StepCount": self._vibration_steps}
                ],
                "SensorReadCmd": [
                    {
                        "FeatureDescriptor": "battery Level",
                        "SensorRange": [[0, 100]],
                        "SensorType": "Battery"
                    }
                ],
                "StopDeviceCmd": {}
            }
        )
        self._device_already_sent = True
        return DeviceList(id=msg_id, devices={self._device_index: device_info})

    async def _handle_start_scanning(self, msg, msg_id):
        asyncio.create_task(self._emit_device_added())
        asyncio.create_task(self._emit_scanning_finished())
        return Ok(id=msg_id)

    async def _handle_stop_scanning(self, msg, msg_id):
        return Ok(id=msg_id)

    async def _handle_scalar_cmd(self, msg, msg_id):
        if msg.device_index != self._device_index:
            return Error(id=msg_id, error_message="Invalid device index", error_code=ErrorCode.DEVICE_NOT_FOUND)
        
        for scalar in msg.scalars:
            if scalar.actuator_type == "Vibrate":
                level = int(scalar.scalar * self._vibration_steps)
                if level != self._last_vibrate_level:
                    self._write_serial(self._vibration_cmd_fmt.format(level=level))
                    self._last_vibrate_level = level
                
                if level > 0:
                    self._refresh_timeout()
                elif self._timeout_task:
                    self._timeout_task.cancel()
        
        return Ok(id=msg_id)

    async def _handle_stop_device(self, msg, msg_id):
        if self._timeout_task:
            self._timeout_task.cancel()
        self._write_serial(self._vibration_cmd_fmt.format(level=0))
        self._last_vibrate_level = 0
        return Ok(id=msg_id)

    async def _handle_stop_all(self, msg, msg_id):
        if self._timeout_task:
            self._timeout_task.cancel()
        self._write_serial(self._vibration_cmd_fmt.format(level=0))
        self._last_vibrate_level = 0
        return Ok(id=msg_id)

    async def _handle_sensor_read(self, msg, msg_id):
        return SensorReading(
            id=msg_id,
            device_index=self._device_index,
            sensor_index=msg.sensor_index,
            sensor_type=msg.sensor_type,
            data=[100] # Dummy battery
        )

    async def _handle_ping(self, msg, msg_id):
        return Ok(id=msg_id)
