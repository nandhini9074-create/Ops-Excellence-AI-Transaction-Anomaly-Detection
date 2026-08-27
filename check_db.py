import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import asyncio
from app.database.connection import init_db_pool, close_db_pool, async_session_maker
from sqlalchemy import text

async def q():
    await init_db_pool()
    async with async_session_maker() as db:
        res = await db.execute(text("SELECT id, transaction_timestamp, transaction_amount FROM transactions WHERE outlet_id = 'bdbedf80-66fc-11f0-95ba-012c7c8027ee' ORDER BY transaction_timestamp DESC"))
        txs = res.mappings().all()
        print('Txns:', len(txs))
        for t in txs: print(dict(t))
        
        res2 = await db.execute(text("SELECT id, anomaly_type, severity, remarks FROM issues WHERE outlet_id = 'bdbedf80-66fc-11f0-95ba-012c7c8027ee'"))
        issues = res2.mappings().all()
        print('Issues:', len(issues))
        for i in issues: print(dict(i))
    await close_db_pool()

asyncio.run(q())
