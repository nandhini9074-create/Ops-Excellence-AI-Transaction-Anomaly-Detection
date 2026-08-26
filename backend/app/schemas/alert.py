from pydantic import BaseModel
from typing import Optional, Any, Dict, Union
from datetime import datetime
from uuid import UUID

class AlertBase(BaseModel):
    anomaly_type: str
    anomaly_score: float
    confidence_score: float
    severity: str
    description: Optional[str] = None
    volume_class: Optional[str] = None
    scheme: Optional[str] = None
    alert_metadata: Optional[Dict[str, Any]] = None

class AlertCreate(AlertBase):
    run_id: Union[UUID, str]
    outlet_id: Union[UUID, str]
    merchant_id: Union[UUID, str]
    merchant_name: str
    outlet_name: str
    detected_at: datetime
    issue_id: Optional[Union[UUID, str]] = None

class AlertResponse(AlertCreate):
    id: Union[UUID, str]
    created_at: datetime

    class Config:
        from_attributes = True
