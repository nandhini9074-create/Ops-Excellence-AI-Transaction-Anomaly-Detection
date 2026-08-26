from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from uuid import UUID
from app.schemas.anomaly import AnomalyResponse # Will create this in next phase if not created, or just use basic

class IssueBase(BaseModel):
    status: Optional[str] = "NEW"
    assigned_to: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    user_typing: Optional[str] = None

class IssueCreate(BaseModel):
    anomaly_id: Union[UUID, str]
    merchant_id: Union[UUID, str]
    merchant_name: str
    outlet_id: Union[UUID, str]
    outlet_name: str
    anomaly_type: str
    anomaly_score: float
    confidence_score: float
    severity: str
    scheme: Optional[str] = None
    remarks: Optional[str] = None
    detected_at: datetime
    occurrence_count: Optional[int] = 1
    last_detected_at: Optional[datetime] = None
    last_run_id: Optional[str] = None
    volume_class: Optional[str] = None
    alert_metadata: Optional[Dict[str, Any]] = None

class IssueUpdate(IssueBase):
    occurrence_count: Optional[int] = None
    last_detected_at: Optional[datetime] = None
    last_run_id: Optional[str] = None
    volume_class: Optional[str] = None
    alert_metadata: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    confidence_score: Optional[float] = None
    remarks: Optional[str] = None

class IssueResponse(IssueBase):
    id: Union[UUID, str]
    anomaly_id: str
    merchant_id: Union[UUID, str]
    merchant_name: str
    outlet_id: Union[UUID, str]
    outlet_name: str
    anomaly_type: str
    anomaly_score: float
    confidence_score: float
    severity: str
    scheme: Optional[str] = None
    remarks: Optional[str] = None
    occurrence_count: int
    last_detected_at: Optional[datetime] = None
    last_run_id: Optional[str] = None
    volume_class: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IssueStatusUpdate(BaseModel):
    status: str # NEW, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, FALSE_POSITIVE, IGNORED, CLOSED
    resolution: Optional[str] = None
    user_typing: Optional[str] = None
