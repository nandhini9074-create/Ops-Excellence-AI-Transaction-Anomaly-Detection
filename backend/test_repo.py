import asyncio
from app.database.connection import async_session
from app.repositories.issue_repo import IssueRepository
import traceback

async def test():
    try:
        async with async_session() as db:
            repo = IssueRepository(db)
            issues = await repo.get_all()
            print("Success, found:", len(issues))
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
