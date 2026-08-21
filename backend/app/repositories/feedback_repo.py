from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import class_mapper

from app.schemas.feedback import FeedbackCreate
from app.database.models import Feedback

def row2dict(row):
    return {c.name: getattr(row, c.name) for c in class_mapper(row.__class__).columns}

class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_issue_id(self, issue_id: str) -> List[dict]:
        stmt = select(Feedback).where(Feedback.issue_id == issue_id).order_by(Feedback.created_at.desc())
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [row2dict(r) for r in records]

    async def create(self, feedback_data: FeedbackCreate) -> dict:
        new_id = str(uuid.uuid4())
        
        feedback = Feedback(
            id=new_id,
            issue_id=feedback_data.issue_id,
            feedback_type=feedback_data.feedback_type,
            root_cause=feedback_data.root_cause,
            comments=feedback_data.comments,
            submitted_by=feedback_data.submitted_by,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return row2dict(feedback)
