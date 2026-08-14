from typing import List, Optional
import asyncpg
import uuid
from datetime import datetime, timezone

from app.schemas.issue import IssueCreate, IssueUpdate

class IssueRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_by_id(self, issue_id: str) -> Optional[dict]:
        query = "SELECT * FROM issues WHERE id = $1"
        record = await self.conn.fetchrow(query, issue_id)
        return dict(record) if record else None

    async def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[dict]:
        if status:
            query = "SELECT * FROM issues WHERE status = $1 ORDER BY created_at DESC OFFSET $2 LIMIT $3"
            records = await self.conn.fetch(query, status, skip, limit)
        else:
            query = "SELECT * FROM issues ORDER BY created_at DESC OFFSET $1 LIMIT $2"
            records = await self.conn.fetch(query, skip, limit)
        return [dict(r) for r in records]

    async def create(self, issue_data: IssueCreate) -> dict:
        new_id = str(uuid.uuid4())
        query = """
            INSERT INTO issues (
                id, anomaly_id, merchant_id, merchant_name, outlet_id, outlet_name,
                anomaly_type, anomaly_score, confidence_score, severity, detected_at, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            ) RETURNING *
        """
        record = await self.conn.fetchrow(
            query,
            new_id,
            issue_data.anomaly_id,
            issue_data.merchant_id,
            issue_data.merchant_name,
            issue_data.outlet_id,
            issue_data.outlet_name,
            issue_data.anomaly_type,
            issue_data.anomaly_score,
            issue_data.confidence_score,
            issue_data.severity,
            issue_data.detected_at.replace(tzinfo=timezone.utc),
            datetime.now(timezone.utc)
        )
        return dict(record)

    async def update(self, issue_id: str, issue_data: IssueUpdate) -> Optional[dict]:
        update_data = issue_data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(issue_id)
            
        if "status" in update_data and update_data["status"] in ["RESOLVED", "FALSE_POSITIVE", "CLOSED"]:
            update_data["resolved_at"] = datetime.now(timezone.utc)
            
        set_clauses = []
        values = []
        for i, (k, v) in enumerate(update_data.items(), start=1):
            set_clauses.append(f"{k} = ${i}")
            values.append(v)
            
        values.append(issue_id) # Last parameter is the ID
        
        query = f"UPDATE issues SET {', '.join(set_clauses)} WHERE id = ${len(values)} RETURNING *"
        record = await self.conn.fetchrow(query, *values)
        return dict(record) if record else None
