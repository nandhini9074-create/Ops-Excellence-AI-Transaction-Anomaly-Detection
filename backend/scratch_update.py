import asyncio
from sqlalchemy import text
from app.database.connection import async_session_maker

async def update_statuses():
    async with async_session_maker() as db:
        # Update issues with status 'OPEN' to 'NEW'
        await db.execute(text("UPDATE issues SET status = 'NEW' WHERE status = 'OPEN'"))
        await db.commit()
        print("Successfully updated old 'OPEN' statuses to 'NEW'.")

if __name__ == "__main__":
    asyncio.run(update_statuses())
