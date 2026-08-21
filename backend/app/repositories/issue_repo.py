from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import class_mapper

from app.schemas.issue import IssueCreate, IssueUpdate
from app.database.models import Issue

def row2dict(row):
    return {c.name: getattr(row, c.name) for c in class_mapper(row.__class__).columns}

class IssueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, issue_id: str) -> Optional[dict]:
        result = await self.db.execute(select(Issue).where(Issue.id == issue_id))
        issue = result.scalar_one_or_none()
        return row2dict(issue) if issue else None

    async def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[dict]:
        stmt = select(Issue).order_by(Issue.created_at.desc()).offset(skip).limit(limit)
        if status:
            stmt = stmt.where(Issue.status == status)
            
        result = await self.db.execute(stmt)
        issues = result.scalars().all()
        return [row2dict(issue) for issue in issues]

    async def create(self, issue_data: IssueCreate) -> dict:
        new_id = str(uuid.uuid4())
        
        issue = Issue(
            id=new_id,
            anomaly_id=issue_data.anomaly_id,
            merchant_id=issue_data.merchant_id,
            merchant_name=issue_data.merchant_name,
            outlet_id=issue_data.outlet_id,
            outlet_name=issue_data.outlet_name,
            anomaly_type=issue_data.anomaly_type,
            anomaly_score=issue_data.anomaly_score,
            confidence_score=issue_data.confidence_score,
            severity=issue_data.severity,
            scheme=issue_data.scheme,
            remarks=issue_data.remarks,
            detected_at=issue_data.detected_at.replace(tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue)
        return row2dict(issue)

    async def update(self, issue_id: str, issue_data: IssueUpdate) -> Optional[dict]:
        update_data = issue_data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(issue_id)
            
        if "status" in update_data and update_data["status"] in ["RESOLVED", "FALSE_POSITIVE", "CLOSED"]:
            update_data["resolved_at"] = datetime.now(timezone.utc)
            
        stmt = update(Issue).where(Issue.id == issue_id).values(**update_data).returning(Issue)
        result = await self.db.execute(stmt)
        updated_issue = result.scalar_one_or_none()
        await self.db.commit()
        
        return row2dict(updated_issue) if updated_issue else None
