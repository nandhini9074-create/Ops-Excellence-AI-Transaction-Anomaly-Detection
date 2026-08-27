import asyncio
import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.database.connection import init_db_pool, close_db_pool, async_session_maker
from app.database.models import Merchant, Outlet, Transaction
from sqlalchemy import select

def generate_tx(merchant_id, outlet_id, amount, dt, scheme="VISA"):
    tx_uuid = str(uuid.uuid4())
    return Transaction(
        id=tx_uuid,
        transaction_id=tx_uuid,
        transaction_no=f"TXN-{random.randint(100000, 999999)}",
        merchant_id=merchant_id,
        outlet_id=outlet_id,
        transaction_amount=amount,
        transaction_timestamp=dt,
        txn_date=dt.date(),
        txn_hour=dt.hour,
        card_scheme=scheme,
        merchant_name="Test Scenarios Merchant",
        outlet_name="Test Scenarios Outlet",
        outlet_status="ACTIVE"
    )

async def main():
    await init_db_pool()
    try:
        async with async_session_maker() as db:
            print("Creating test merchants and outlets...")
            m_id = str(uuid.uuid4())
            merchant = Merchant(id=m_id, name="Test Scenarios Merchant")
            db.add(merchant)

            outlets = {
                "Normal Outlet": str(uuid.uuid4()),
                "Amount Spike Outlet": str(uuid.uuid4()),
                "Pattern Break Outlet": str(uuid.uuid4()),
                "Dormant Outlet": str(uuid.uuid4()),
            }

            for name, o_id in outlets.items():
                db.add(Outlet(id=o_id, merchant_id=m_id, name=name))

            await db.commit()

            print("Generating historical data (last 30 days)...")
            now = datetime.now(timezone.utc)
            txs = []

            # 1. Normal Outlet (30 days of data, 5 tx per day around $50)
            # 2. Amount Spike Outlet (30 days of data, 5 tx per day around $50)
            # 3. Pattern Break Outlet (30 days of daytime data, 5 tx per day around $50)
            for days_ago in range(30, 0, -1):
                base_dt = now - timedelta(days=days_ago)
                for _ in range(5):
                    # Normal
                    dt = base_dt.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                    txs.append(generate_tx(m_id, outlets["Normal Outlet"], random.uniform(40, 60), dt))
                    
                    # Amount Spike
                    dt = base_dt.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                    txs.append(generate_tx(m_id, outlets["Amount Spike Outlet"], random.uniform(40, 60), dt))

                    # Pattern Break (always daytime)
                    dt = base_dt.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                    txs.append(generate_tx(m_id, outlets["Pattern Break Outlet"], random.uniform(40, 60), dt))

            # 4. Dormant Outlet (30 days of data, but shifted back by 35 days)
            for days_ago in range(65, 35, -1):
                base_dt = now - timedelta(days=days_ago)
                for _ in range(5):
                    dt = base_dt.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                    txs.append(generate_tx(m_id, outlets["Dormant Outlet"], random.uniform(40, 60), dt))

            print("Generating anomalous data (today)...")
            # Normal Outlet - standard day
            for _ in range(5):
                dt = now.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                txs.append(generate_tx(m_id, outlets["Normal Outlet"], random.uniform(40, 60), dt))

            # Amount Spike Outlet - ONE huge transaction
            for _ in range(4):
                dt = now.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                txs.append(generate_tx(m_id, outlets["Amount Spike Outlet"], random.uniform(40, 60), dt))
            txs.append(generate_tx(m_id, outlets["Amount Spike Outlet"], 95000.00, now)) # Spike!

            # Pattern Break Outlet - Sudden burst of 20 txs at 3 AM
            for i in range(20):
                dt = now.replace(hour=3, minute=random.randint(0, 59))
                txs.append(generate_tx(m_id, outlets["Pattern Break Outlet"], random.uniform(10, 20), dt))

            # Dormant Outlet gets nothing today.

            db.add_all(txs)
            await db.commit()
            print(f"Inserted {len(txs)} transactions successfully.")
            
            # Write a mapping of outlet names to IDs for reference
            import json
            with open("test_outlets.json", "w") as f:
                json.dump(outlets, f)

    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())
