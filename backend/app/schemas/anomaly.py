from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class AnomalyResponse(BaseModel):
    id: str
    merchant_id: str
    outlet_id: str
    anomaly_type: str
    anomaly_score: float
    confidence_score: float
    severity: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    explanation: Optional[str] = None
    detector_outputs: Optional[Dict] = None
    detected_at: datetime
    processing_run_id: Optional[str] = None
    
    class Config:
        from_attributes = True
