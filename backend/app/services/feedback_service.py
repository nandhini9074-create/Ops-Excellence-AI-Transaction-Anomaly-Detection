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
            elif feedback_in.feedback_type == "TRUE_ALERT":
                await self.issue_repo.update(issue["id"], IssueUpdate(status="RESOLVED", root_cause=feedback_in.root_cause))
                
        return fb
