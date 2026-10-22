"""
IndusVision Backend - Alert & Maintenance Models
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

AlertSeverity = Literal["critical", "warning", "info"]
AlertSource = Literal["sensor", "detection", "inventory", "manual"]


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: AlertSeverity = "warning"
    source: AlertSource = "manual"
    machine_id: Optional[str] = None


class AlertOut(AlertCreate):
    id: str
    status: Literal["open", "acknowledged", "resolved"] = "open"
    created_at: datetime


class MaintenancePredictionOut(BaseModel):
    id: str
    machine_id: str
    health_score: float
    failure_probability: float
    remaining_useful_life_days: int
    predicted_status: Literal["normal", "warning", "failure"]
    next_maintenance_date: datetime
    generated_at: datetime
    reasons: list[str] = Field(default_factory=list)
    fault_detected: bool = False
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    vibration: Optional[int] = None
    current_amps: Optional[float] = None
    gas_raw: Optional[int] = None
    distance_cm: Optional[float] = None


class MaintenanceEventOut(BaseModel):
    id: str
    source: Literal["sensor", "worker_safety"]
    machine_id: Optional[str] = None
    camera_id: Optional[str] = None
    title: str
    status: str
    causes: list[str]
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    vibration: Optional[int] = None
    current_amps: Optional[float] = None
    gas_raw: Optional[int] = None
    distance_cm: Optional[float] = None
