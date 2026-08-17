from fastapi import APIRouter, Depends, status
import asyncpg
from typing import List

from app.database.connection import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService
from app.repositories.feedback_repo import FeedbackRepository

router = APIRouter()

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(fb_in: FeedbackCreate, db: asyncpg.Connection = Depends(get_db)):
    service = FeedbackService(db)
    fb = await service.process_feedback(fb_in)
    return fb

@router.get("/issue/{issue_id}", response_model=List[FeedbackResponse])
async def get_feedback_for_issue(issue_id: str, db: asyncpg.Connection = Depends(get_db)):
    repo = FeedbackRepository(db)
    return await repo.get_by_issue_id(issue_id)

@router.get("/")
async def get_all_feedback(db: asyncpg.Connection = Depends(get_db)):
    query = """
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
    """
    rows = await db.fetch(query)
    res = []
    for r in rows:
        d = dict(r)
        d['id'] = str(d['id'])
        d['issue_id'] = str(d['issue_id'])
        if d.get('created_at'):
            d['created_at'] = d['created_at'].isoformat()
        res.append(d)
    return res

