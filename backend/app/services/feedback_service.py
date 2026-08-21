import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.schemas.feedback import FeedbackCreate
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.issue_repo import IssueRepository
from app.schemas.issue import IssueUpdate
from app.database.models import MerchantWhitelist

logger = logging.getLogger("ops_excellence.services.feedback")


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fb_repo = FeedbackRepository(db)
        self.issue_repo = IssueRepository(db)

    async def process_feedback(self, feedback_in: FeedbackCreate):
        # 1. Save feedback
        fb = await self.fb_repo.create(feedback_in)
        logger.info(f"Saved feedback record {fb.get('id')} for issue {feedback_in.issue_id}.")
        
        # 2. Update issue status if needed
        issue = await self.issue_repo.get_by_id(feedback_in.issue_id)
        if issue:
            if feedback_in.feedback_type == "FALSE_POSITIVE":
                logger.info(f"Issue {issue['id']} marked as FALSE_POSITIVE. Initiating continuous feedback learning...")
                await self.issue_repo.update(issue["id"], IssueUpdate(status="FALSE_POSITIVE", root_cause=feedback_in.root_cause))
                # Trigger Continuous Feedback Learning: Increment false positive count & update merchant whitelist
                await self._process_merchant_whitelisting(issue["merchant_id"], issue["outlet_id"], issue.get("anomaly_type", ""))
            elif feedback_in.feedback_type == "TRUE_ALERT":
                logger.info(f"Issue {issue['id']} marked as TRUE_ALERT. Escalating and resolving ticket...")
                await self.issue_repo.update(issue["id"], IssueUpdate(status="RESOLVED", root_cause=feedback_in.root_cause))
                
        return fb

    async def _process_merchant_whitelisting(self, merchant_id: str, outlet_id: str, issue_anomaly_type: str = ""):
        try:
            # Check existing whitelist record
            stmt = select(MerchantWhitelist).where(MerchantWhitelist.merchant_id == merchant_id)
            result = await self.db.execute(stmt)
            whitelist = result.scalar_one_or_none()
            
            if whitelist:
                new_count = (whitelist.false_positive_count or 0) + 1
                whitelist.false_positive_count = new_count
                whitelist.is_whitelisted = 'true' if new_count >= 3 else 'false'
                whitelist.threshold_multiplier = 1.5 if new_count >= 3 else 1.0
                
                logger.info(f"Updated merchant whitelist for merchant {merchant_id}: false_positive_count={new_count}, multiplier={whitelist.threshold_multiplier}x, is_whitelisted={whitelist.is_whitelisted}.")
                
                # Fix 4: If this false-positive is for a DORMANCY alert, suppress dormancy re-alerting for 30 days
                if issue_anomaly_type.upper() == "DORMANCY":
                    whitelist.dormancy_suppressed_until = datetime.now(timezone.utc) + timedelta(days=30)
                    logger.info(f"Dormancy alerts suppressed for outlet {outlet_id} for 30 days due to false-positive feedback.")
            else:
                whitelist = MerchantWhitelist(
                    merchant_id=merchant_id,
                    outlet_id=outlet_id,
                    false_positive_count=1,
                    threshold_multiplier=1.0,
                    is_whitelisted='false'
                )
                
                if issue_anomaly_type.upper() == "DORMANCY":
                    whitelist.dormancy_suppressed_until = datetime.now(timezone.utc) + timedelta(days=30)
                    logger.info(f"Dormancy alerts suppressed for outlet {outlet_id} for 30 days due to false-positive feedback.")
                
                self.db.add(whitelist)
                logger.info(f"Created new merchant whitelist record for merchant {merchant_id}.")
                
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update merchant whitelist: {e}")
