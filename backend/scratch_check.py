import asyncio
from sqlalchemy import text
from app.database.connection import async_session_maker

async def check():
    async with async_session_maker() as session:
        res = await session.execute(text("SELECT id, status FROM issues"))
        print(res.all())

if __name__ == "__main__":
    asyncio.run(check())
