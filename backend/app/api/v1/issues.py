from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List, Optional

from app.database.connection import get_db
from app.schemas.issue import IssueResponse, IssueUpdate, IssueCreate, IssueStatusUpdate
from app.repositories.issue_repo import IssueRepository

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

@router.get("/{id}", response_model=IssueResponse)
async def get_issue(id: str, db: asyncpg.Connection = Depends(get_db)):
    repo = IssueRepository(db)
    issue = await repo.get_by_id(id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(issue_in: IssueCreate, db: asyncpg.Connection = Depends(get_db)):
    repo = IssueRepository(db)
    issue = await repo.create(issue_in)
    return issue

@router.patch("/{id}", response_model=IssueResponse)
async def update_issue(id: str, issue_in: IssueUpdate, db: asyncpg.Connection = Depends(get_db)):
    repo = IssueRepository(db)
    issue = await repo.update(id, issue_in)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

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
    return issue
