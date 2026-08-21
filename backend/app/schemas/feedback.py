from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    issue_id: str
    feedback_type: str # TRUE_ALERT, FALSE_POSITIVE, UNCERTAIN
    root_cause: Optional[str] = None
    comments: Optional[str] = None
    user_typing: Optional[str] = None
    submitted_by: Optional[str] = None

class FeedbackResponse(FeedbackCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
