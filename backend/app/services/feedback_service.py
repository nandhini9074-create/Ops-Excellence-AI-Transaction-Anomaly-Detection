import asyncpg
from app.schemas.feedback import FeedbackCreate
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.issue_repo import IssueRepository
from app.schemas.issue import IssueUpdate

class FeedbackService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.fb_repo = FeedbackRepository(conn)
        self.issue_repo = IssueRepository(conn)

    async def process_feedback(self, feedback_in: FeedbackCreate):
        # 1. Save feedback
        fb = await self.fb_repo.create(feedback_in)
        
        # 2. Update issue status if needed
        issue = await self.issue_repo.get_by_id(feedback_in.issue_id)
        if issue:
            if feedback_in.feedback_type == "FALSE_POSITIVE":
                await self.issue_repo.update(issue["id"], IssueUpdate(status="FALSE_POSITIVE", root_cause=feedback_in.root_cause))
                # Trigger Continuous Feedback Learning: Increment false positive count & update merchant whitelist
                await self._process_merchant_whitelisting(issue["merchant_id"], issue["outlet_id"])
            elif feedback_in.feedback_type == "TRUE_ALERT":
                await self.issue_repo.update(issue["id"], IssueUpdate(status="RESOLVED", root_cause=feedback_in.root_cause))
            elif feedback_in.feedback_type == "UNCERTAIN":
                await self.issue_repo.update(issue["id"], IssueUpdate(status="UNCERTAIN", root_cause=feedback_in.root_cause))
                
        return fb

    async def _process_merchant_whitelisting(self, merchant_id: str, outlet_id: str):
        try:
            # Check existing whitelist record
            row = await self.conn.fetchrow(
                "SELECT id, false_positive_count FROM merchant_whitelists WHERE merchant_id = $1", 
                merchant_id
            )
            if row:
                new_count = (row["false_positive_count"] or 0) + 1
                is_whitelisted = 'true' if new_count >= 3 else 'false'
                multiplier = 1.5 if new_count >= 3 else 1.0
                await self.conn.execute(
                    """
                    UPDATE merchant_whitelists 
                    SET false_positive_count = $1, is_whitelisted = $2, threshold_multiplier = $3, updated_at = NOW() 
                    WHERE id = $4
                    """,
                    new_count, is_whitelisted, multiplier, row["id"]
                )
            else:
                await self.conn.execute(
                    """
                    INSERT INTO merchant_whitelists (merchant_id, outlet_id, false_positive_count, threshold_multiplier, is_whitelisted)
                    VALUES ($1, $2, 1, 1.0, 'false')
                    """,
                    merchant_id, outlet_id
                )
        except Exception as e:
            # Log error but don't fail main request
            import logging
            logging.getLogger(__name__).error(f"Failed to update merchant whitelist: {e}")

