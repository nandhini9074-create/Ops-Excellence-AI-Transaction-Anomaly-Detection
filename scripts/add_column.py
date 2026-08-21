import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:pass%40123@localhost:5432/ops_excellence', isolation_level='AUTOCOMMIT')
    async with engine.connect() as conn:
        try:
            await conn.execute(text('ALTER TABLE issues ADD COLUMN user_typing TEXT;'))
        except Exception as e:
            print("issues error:", e)
        try:
            await conn.execute(text('ALTER TABLE feedback ADD COLUMN user_typing TEXT;'))
        except Exception as e:
            print("feedback error:", e)
    await engine.dispose()
    print('Done.')

asyncio.run(main())
