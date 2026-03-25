"""Base Buttplug message handling and parsing."""

from __future__ import annotations

import json
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound="ButtplugMessage")


class ButtplugMessage(BaseModel):
    """Base class for all Buttplug protocol messages."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    # Message type name used in JSON (set by subclasses)
    _message_type: ClassVar[str] = ""

    id: int = Field(alias="Id")

    def get_message_type(self) -> str:
        """Returns the Buttplug message type string."""
        return self._message_type

    def to_protocol(self) -> list[dict[str, Any]]:
        """Serialize message to Buttplug protocol format."""
        return [{self._message_type: self.model_dump(by_alias=True, exclude_none=True)}]


def parse_message(data: dict[str, Any]) -> ButtplugMessage:
    """Parse a single Buttplug message dictionary."""
    if len(data) != 1:
        msg = f"Expected single message type in dict, got {len(data)}"
        raise ValueError(msg)

    msg_type = next(iter(data.keys()))
    payload = data[msg_type]

    # Map message types to their classes
    from buttplug._messages.commands import (
        InputCmd,
        InputReading,
        OutputCmd,
        ScalarCmd,
        SensorReadCmd,
        SensorReading,
        StopDeviceCmd,
        StopCmd,
    )
    from buttplug._messages.device_info import DeviceAdded, DeviceList
    from buttplug._messages.handshake import (
        Disconnect,
        Error,
        Ok,
        Ping,
        RequestDeviceList,
        RequestServerInfo,
        ScanningFinished,
        ServerInfo,
        StartScanning,
        StopScanning,
    )

    message_types: dict[str, type[ButtplugMessage]] = {
        "RequestServerInfo": RequestServerInfo,
        "ServerInfo": ServerInfo,
        "Ok": Ok,
        "Error": Error,
        "Ping": Ping,
        "Disconnect": Disconnect,
        "StartScanning": StartScanning,
        "StopScanning": StopScanning,
        "ScanningFinished": ScanningFinished,
        "RequestDeviceList": RequestDeviceList,
        "DeviceList": DeviceList,
        "DeviceAdded": DeviceAdded,
        "OutputCmd": OutputCmd,
        "ScalarCmd": ScalarCmd,
        "SensorReadCmd": SensorReadCmd,
        "SensorReading": SensorReading,
        "StopDeviceCmd": StopDeviceCmd,
        "InputCmd": InputCmd,
        "InputReading": InputReading,
        "StopCmd": StopCmd,
    }

    if msg_type not in message_types:
        msg = f"Unknown message type: {msg_type}"
        raise ValueError(msg)

    return message_types[msg_type].model_validate(payload)


def parse_messages(data: list[dict[str, Any]]) -> list[ButtplugMessage]:
    """Parse an array of messages from protocol format."""
    return [parse_message(msg) for msg in data]
