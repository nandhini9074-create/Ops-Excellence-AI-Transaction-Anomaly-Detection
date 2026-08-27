import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import asyncio
from app.database.connection import init_db_pool, close_db_pool, async_session_maker
from sqlalchemy import text

async def update_and_detect():
    await init_db_pool()
    async with async_session_maker() as db:
        # Update the 55000 transaction to NOW so it gets picked up
        await db.execute(text("UPDATE transactions SET transaction_timestamp = NOW() WHERE transaction_amount = 55000.00"))
        await db.commit()
    await close_db_pool()

asyncio.run(update_and_detect())
