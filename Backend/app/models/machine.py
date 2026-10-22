"""
IndusVision Backend - Machine & Sensor Models
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

MachineStatus = Literal["running", "idle", "maintenance", "fault", "offline"]


class MachineCreate(BaseModel):
    machine_id: str
    name: str
    location: Optional[str] = None
    machine_type: Optional[str] = None
    installed_on: Optional[datetime] = None


class MachineOut(BaseModel):
    id: str
    machine_id: str
    name: str
    location: Optional[str] = None
    machine_type: Optional[str] = None
    status: MachineStatus = "offline"
    health_score: Optional[float] = None
    last_seen: Optional[datetime] = None


class SensorReadingIn(BaseModel):
    """Matches the exact JSON payload sent by the ESP32 firmware."""
    machine_id: str
    temperature: float = -1
    humidity: float = -1
    vibration: int = 0
    current_amps: float = 0
    gas_raw: int = 0
    distance_cm: float = -1
    fault: bool = False


class SensorReadingOut(SensorReadingIn):
    id: str
    timestamp: datetime
