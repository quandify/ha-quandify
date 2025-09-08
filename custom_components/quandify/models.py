"""Models for the Quandify integration."""
from dataclasses import dataclass
from typing import Any
@dataclass
class QuandifyDevice:
    """A class representing a Quandify device."""

    id: str
    name: str
    model: str
    serial: str | None
    firmware_version: str | None
    hardware_version: int | None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "QuandifyDevice":
        """Create a device object from the API response."""
        device_type = data.get("type")
        hardware_version = data.get("hardware_version")
        
        model = "Unknown"
        node = data.get("node", {})
        name = node.get("name", "Unknown Device")

        if device_type == "waterfuse" and hardware_version == 5:
            model = "Water Grip"
        else:
            return None
        
        return cls(
            id=data["id"],
            name=name,
            model=model,
            serial=data.get("serial"),
            firmware_version=data.get("firmware_version"),
            hardware_version=hardware_version,
        )