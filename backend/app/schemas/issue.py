from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID
from app.schemas.anomaly import AnomalyResponse # Will create this in next phase if not created, or just use basic

class IssueBase(BaseModel):
    status: Optional[str] = "OPEN"
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

class IssueUpdate(IssueBase):
    pass

class IssueResponse(IssueBase, IssueCreate):
    id: Union[UUID, str]
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IssueStatusUpdate(BaseModel):
    status: str # ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE, CLOSED
    resolution: Optional[str] = None
    user_typing: Optional[str] = None
