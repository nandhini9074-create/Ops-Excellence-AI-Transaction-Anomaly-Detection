from typing import List, Optional
import asyncpg
import uuid
from datetime import datetime, timezone

from app.schemas.feedback import FeedbackCreate

class FeedbackRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_by_issue_id(self, issue_id: str) -> List[dict]:
        query = "SELECT * FROM feedback WHERE issue_id = $1 ORDER BY created_at DESC"
        records = await self.conn.fetch(query, issue_id)
        return [dict(r) for r in records]

    async def create(self, feedback_data: FeedbackCreate) -> dict:
        new_id = str(uuid.uuid4())
        query = """
            INSERT INTO feedback (id, issue_id, feedback_type, root_cause, comments, submitted_by, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *
        """
        record = await self.conn.fetchrow(
            query,
            new_id,
            feedback_data.issue_id,
            feedback_data.feedback_type,
            feedback_data.root_cause,
            feedback_data.comments,
            feedback_data.submitted_by,
            datetime.now(timezone.utc)
        )
        return dict(record)
