"""Device information and enumeration messages."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from buttplug._messages.base import ButtplugMessage


class FeatureOutputDefinition(BaseModel):
    """Output capability definition for a feature."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    value: tuple[int, int] = Field(alias="Value")
    duration: tuple[int, int] | None = Field(default=None, alias="Duration")


class FeatureInputDefinition(BaseModel):
    """Input capability definition for a feature."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    value: list[tuple[int, int]] = Field(alias="Value")
    command: list[str] = Field(alias="Command")


class DeviceFeatureDefinition(BaseModel):
    """Definition of a single device feature."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    feature_index: int = Field(alias="FeatureIndex")
    feature_description: str | None = Field(default=None, alias="FeatureDescription")
    output: dict[str, FeatureOutputDefinition] | None = Field(default=None, alias="Output")
    input: dict[str, FeatureInputDefinition] | None = Field(default=None, alias="Input")


class DeviceInfo(BaseModel):
    """Information about a single device."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    device_name: str = Field(alias="DeviceName")
    device_index: int = Field(alias="DeviceIndex")
    device_message_timing_gap: int = Field(default=0, alias="DeviceMessageTimingGap")
    device_display_name: str | None = Field(default=None, alias="DeviceDisplayName")
    device_messages: dict[str, dict[str, Any] | list[dict[str, Any]]] | None = Field(default=None, alias="DeviceMessages")
    device_features: dict[int, DeviceFeatureDefinition] | None = Field(
        default=None, alias="DeviceFeatures"
    )

    @model_validator(mode="before")
    @classmethod
    def parse_features_dict(cls, data: Any) -> Any:
        """Convert string-keyed DeviceFeatures dict to int-keyed and handle V3 exclusion."""
        if isinstance(data, dict):
            # For V3 compatibility, if DeviceMessages is present, we MUST hide V4 fields
            if "DeviceMessages" in data or "device_messages" in data:
                # Remove V4 fields for V3 clients
                data.pop("DeviceFeatures", None)
                data.pop("device_features", None)
                data.pop("DeviceDisplayName", None)
                data.pop("device_display_name", None)
                data.pop("DeviceMessageTimingGap", None)
                data.pop("device_message_timing_gap", None)
                # Ensure device_features is None so it's excluded
                if "DeviceFeatures" not in data and "device_features" not in data:
                    data["device_features"] = None
            
            features = data.get("DeviceFeatures") or data.get("device_features")
            if features and isinstance(features, dict):
                # Protocol uses string keys like "0", "1", etc.
                converted = {}
                for key, value in features.items():
                    converted[int(key)] = value
                if "DeviceFeatures" in data:
                    data["DeviceFeatures"] = converted
                else:
                    data["device_features"] = converted
        return data


class DeviceList(ButtplugMessage):
    """List of connected devices."""

    _message_type: ClassVar[str] = "DeviceList"

    devices: dict[int, DeviceInfo] = Field(default_factory=dict, alias="Devices")

    def to_protocol(self) -> list[dict[str, Any]]:
        """Serialize message to Buttplug protocol format, handling V3 list format."""
        # V3 expects a list of devices, but V4 expects a map.
        # We'll detect if we should provide a list based on the devices themselves or context.
        # For simplicity in this gateway, we'll just check if we have device_messages set.
        
        device_list = []
        for dev in self.devices.values():
            dev_dict = dev.model_dump(by_alias=True, exclude_none=True)
            device_list.append(dev_dict)
            
        return [{self._message_type: {
            "Id": self.id,
            "Devices": device_list
        }}]

    @model_validator(mode="before")
    @classmethod
    def parse_devices_dict(cls, data: Any) -> Any:
        """Convert string-keyed Devices dict to int-keyed."""
        if isinstance(data, dict):
            devices = data.get("Devices") or data.get("devices")
            if devices and isinstance(devices, dict):
                # Protocol uses string keys like "0", "1", etc.
                converted = {}
                for key, value in devices.items():
                    converted[int(key)] = value
                if "Devices" in data:
                    data["Devices"] = converted
                else:
                    data["devices"] = converted
        return data


class DeviceAdded(DeviceInfo, ButtplugMessage):
    """Notification that a device has been added."""

    _message_type: ClassVar[str] = "DeviceAdded"
    
    def to_protocol(self) -> list[dict[str, Any]]:
        """Serialize message to Buttplug protocol format, ensuring strict V3."""
        # Force Id: 0 for pushed notifications
        res = self.model_dump(by_alias=True, exclude_none=True)
        res["Id"] = 0
        
        # Strictly remove V4-only fields for V3-compatible messages
        if "DeviceMessages" in res:
            res.pop("DeviceFeatures", None)
            res.pop("DeviceDisplayName", None)
            res.pop("DeviceMessageTimingGap", None)
            
        return [{self._message_type: res}]
