from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List, Optional

from app.database.connection import get_db
from app.schemas.issue import IssueResponse, IssueUpdate, IssueCreate, IssueStatusUpdate
from app.repositories.issue_repo import IssueRepository
from app.schemas.feedback import FeedbackCreate
from app.services.feedback_service import FeedbackService

router = APIRouter()

@router.get("/", response_model=List[IssueResponse])
async def list_issues(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: asyncpg.Connection = Depends(get_db)
):
    repo = IssueRepository(db)
    return await repo.get_all(status=status, skip=skip, limit=limit)

@router.post("/{id}/acknowledge", response_model=IssueResponse)
async def acknowledge_issue(id: str, db: asyncpg.Connection = Depends(get_db)):
    repo = IssueRepository(db)
    issue = await repo.update(id, IssueUpdate(status="ACKNOWLEDGED"))
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@router.post("/{id}/resolve", response_model=IssueResponse)
async def resolve_issue(id: str, payload: IssueStatusUpdate, db: asyncpg.Connection = Depends(get_db)):
    repo = IssueRepository(db)
    issue = await repo.update(id, IssueUpdate(status=payload.status, resolution=payload.resolution))
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Automatically record human feedback for model calibration
    feedback_type = "TRUE_ALERT" if payload.status == "RESOLVED" else "FALSE_POSITIVE"
    fb_service = FeedbackService(db)
    await fb_service.process_feedback(FeedbackCreate(
        issue_id=id,
        feedback_type=feedback_type,
        root_cause=payload.resolution,
        comments=payload.resolution or f"Marked as {payload.status} by operator",
        submitted_by="operator"
    ))
    
    return issue
