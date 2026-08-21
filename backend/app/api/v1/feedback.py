from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List

from app.database.connection import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService
from app.repositories.feedback_repo import FeedbackRepository

import logging

logger = logging.getLogger("ops_excellence.api.feedback")
router = APIRouter()

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(fb_in: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received human feedback for issue {fb_in.issue_id}: classification={fb_in.feedback_type}")
    service = FeedbackService(db)
    fb = await service.process_feedback(fb_in)
    logger.info(f"Feedback successfully logged for issue {fb_in.issue_id}.")
    return fb


@router.get("/")
async def get_all_feedback(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT 
            f.id,
            f.issue_id,
            i.anomaly_type,
            i.merchant_name,
            i.outlet_name,
            f.feedback_type,
            f.root_cause,
            f.comments,
            f.submitted_by,
            f.created_at
        FROM feedback f
        LEFT JOIN issues i ON f.issue_id = i.id
        ORDER BY f.created_at DESC;
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    res = []
    for d in rows:
        d = dict(d)
        d['id'] = str(d['id'])
        d['issue_id'] = str(d['issue_id'])
        if d.get('created_at'):
            d['created_at'] = d['created_at'].isoformat()
        res.append(d)
    return res
