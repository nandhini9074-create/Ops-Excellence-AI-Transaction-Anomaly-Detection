from fastapi import APIRouter, Depends, HTTPException, status
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
