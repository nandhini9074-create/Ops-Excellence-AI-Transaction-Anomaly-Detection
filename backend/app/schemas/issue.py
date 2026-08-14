from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.anomaly import AnomalyResponse # Will create this in next phase if not created, or just use basic

class IssueBase(BaseModel):
    status: Optional[str] = "OPEN"
    assigned_to: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None

class IssueCreate(BaseModel):
    anomaly_id: str
    merchant_id: str
    merchant_name: str
    outlet_id: str
    outlet_name: str
    anomaly_type: str
    anomaly_score: float
    confidence_score: float
    severity: str
    detected_at: datetime

class IssueUpdate(IssueBase):
    pass

class IssueResponse(IssueBase, IssueCreate):
    id: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IssueStatusUpdate(BaseModel):
    status: str # ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE, CLOSED
    resolution: Optional[str] = None
