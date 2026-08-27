import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    db_url = 'postgresql+asyncpg://postgres:pass%40123@localhost:5432/ops_excellence'
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM issues WHERE merchant_name = 'Test Scenarios Merchant'"))
        await conn.execute(text("DELETE FROM alerts WHERE merchant_name = 'Test Scenarios Merchant'"))
        await conn.execute(text("DELETE FROM baselines WHERE outlet_id IN (SELECT id FROM outlets WHERE merchant_id IN (SELECT id FROM merchants WHERE name = 'Test Scenarios Merchant'))"))
        await conn.execute(text("DELETE FROM transactions WHERE merchant_name = 'Test Scenarios Merchant'"))
        await conn.execute(text("DELETE FROM outlets WHERE merchant_id IN (SELECT id FROM merchants WHERE name = 'Test Scenarios Merchant')"))
        await conn.execute(text("DELETE FROM merchants WHERE name = 'Test Scenarios Merchant'"))
        
        print('Successfully deleted all test scenarios data!')
        
asyncio.run(main())
