import asyncio
import sys
import os
import argparse
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from backend.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_schema(db: AsyncSession):
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "database", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            sql = f.read()
        logger.info("Applying schema.sql...")
        await db.execute(text(sql))
        await db.commit()
        logger.info("Schema applied successfully.")
    else:
        logger.error(f"Schema file not found at {schema_path}")

async def seed_merchants_and_outlets(db: AsyncSession):
    logger.info("Seeding merchants and outlets...")
    import uuid
    
    # 1. Create Merchants
    m1_id = str(uuid.uuid4())
    m2_id = str(uuid.uuid4())
    m3_id = str(uuid.uuid4())
    
    await db.execute(text("INSERT INTO merchants (id, name, mcc) VALUES (:id, :name, :mcc)"), {"id": m1_id, "name": "India Bistro", "mcc": "5812"})
    await db.execute(text("INSERT INTO merchants (id, name, mcc) VALUES (:id, :name, :mcc)"), {"id": m2_id, "name": "Coffee Planet", "mcc": "5814"})
    await db.execute(text("INSERT INTO merchants (id, name, mcc) VALUES (:id, :name, :mcc)"), {"id": m3_id, "name": "fnp.ae", "mcc": "5992"})

    # 2. Create Outlets
    o1_id = str(uuid.uuid4())
    o2_id = str(uuid.uuid4())
    o3_id = str(uuid.uuid4())
    o4_id = str(uuid.uuid4())
    
    await db.execute(text("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES (:id, :mid, :name, :city)"), {"id": o1_id, "mid": m1_id, "name": "Dubai WTC", "city": "Dubai"})
    await db.execute(text("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES (:id, :mid, :name, :city)"), {"id": o2_id, "mid": m1_id, "name": "Sharjah Center", "city": "Sharjah"})
    await db.execute(text("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES (:id, :mid, :name, :city)"), {"id": o3_id, "mid": m2_id, "name": "Etihad Plaza", "city": "Abu Dhabi"})
    await db.execute(text("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES (:id, :mid, :name, :city)"), {"id": o4_id, "mid": m3_id, "name": "E-Commerce", "city": "Online"})

    await db.commit()
    logger.info("Merchants and outlets seeded.")

async def seed_transactions(db: AsyncSession, file_path: str = None):
    logger.info("Loading generated transactions...")
    import os
    import httpx
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta, timezone
    from data_pipeline.generators.dataset_generator import load_dataset
    from backend.app.schemas.transaction import TransactionCreate
    from data_pipeline.ingestion.ingestion_service import IngestionService
    
    if not file_path:
        file_path = "transactions.json"
        if not os.path.exists(file_path):
            file_path = "data/development_dataset.csv"
        
    df = load_dataset(file_path)
    
    if df.empty:
        logger.warning("Dataset is empty. Run dataset_generator.py first.")
        return
        
    logger.info(f"Loaded {len(df)} total transactions from dataset.")
    
    df = df.replace({np.nan: None})
    
    # 1. Dynamically seed missing merchants and outlets to satisfy foreign keys
    logger.info("Resolving foreign key constraints for merchants and outlets...")
    unique_merchants = df[['merchant_id', 'merchant_name']].dropna().drop_duplicates()
    for _, m_row in unique_merchants.iterrows():
        m_id = str(m_row['merchant_id'])
        m_name = m_row['merchant_name']
        await db.execute(
            text("INSERT INTO merchants (id, name, mcc) VALUES (:id, :name, '0000') ON CONFLICT (id) DO NOTHING"),
            {"id": m_id, "name": m_name}
        )
        
    unique_outlets = df[['outlet_id', 'outlet_name', 'merchant_id']].dropna().drop_duplicates()
    for _, o_row in unique_outlets.iterrows():
        o_id = str(o_row['outlet_id'])
        o_name = o_row['outlet_name']
        m_id = str(o_row['merchant_id'])
        await db.execute(
            text("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES (:id, :mid, :name, 'Unknown') ON CONFLICT (id) DO NOTHING"),
            {"id": o_id, "mid": m_id, "name": o_name}
        )
        
    unique_profiles = df[['profile_id', 'outlet_id']].dropna().drop_duplicates()
    for _, p_row in unique_profiles.iterrows():
        p_id = str(p_row['profile_id'])
        o_id = str(p_row['outlet_id'])
        await db.execute(
            text("INSERT INTO profiles (id, outlet_id, risk_score, segment) VALUES (:id, :oid, 0.0, 'STANDARD') ON CONFLICT (id) DO NOTHING"),
            {"id": p_id, "oid": o_id}
        )
    
    await db.commit()
    
    # Calculate cutoff for past 1 week (using UTC timezone for compatibility)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    
    recent_txs = []
    historical_txs = []
    
    for _, row in df.iterrows():
        # Parse transaction_timestamp properly
        ts_val = row['transaction_timestamp']
        if isinstance(ts_val, str):
            ts = pd.to_datetime(ts_val).to_pydatetime().replace(tzinfo=timezone.utc)
        else:
            ts = ts_val.replace(tzinfo=timezone.utc)
            
        # Parse posting_timestamp if available
        posting_ts = row.get('posting_timestamp')
        if posting_ts:
            if isinstance(posting_ts, str):
                posting_ts = pd.to_datetime(posting_ts).to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                posting_ts = posting_ts.replace(tzinfo=timezone.utc)
                
        # Parse silver_updated_at if available
        silver_ts = row.get('silver_updated_at')
        if silver_ts:
            if isinstance(silver_ts, str):
                silver_ts = pd.to_datetime(silver_ts).to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                silver_ts = silver_ts.replace(tzinfo=timezone.utc)
                
        tx = TransactionCreate(
            transaction_id=row.get('transaction_id'),
            transaction_no=row.get('transaction_no'),
            group_id=row.get('group_id'),
            group_transaction_id=row.get('group_transaction_id'),
            payout_transaction_id=row.get('payout_transaction_id'),
            outlet_id=str(row['outlet_id']),
            merchant_id=str(row['merchant_id']),
            profile_id=str(row.get('profile_id')) if row.get('profile_id') else "a154a1d8-c6f5-47af-a14d-11052271c3e7",
            transaction_timestamp=ts,
            posting_timestamp=posting_ts,
            txn_date=row['txn_date'],
            txn_hour=str(row['txn_hour']),
            transaction_amount=float(row['transaction_amount']),
            card_scheme=row.get('card_scheme'),
            merchant_name=row.get('merchant_name'),
            outlet_name=row.get('outlet_name'),
            outlet_status=row.get('outlet_status', 'ACTIVE'),
            silver_updated_at=silver_ts
        )
        
        if ts >= cutoff_date:
            recent_txs.append(tx)
        else:
            historical_txs.append(tx)
            
    # 2. Ingest recent transactions into PostgreSQL
    logger.info(f"Ingesting {len(recent_txs)} recent (past 1 week) transactions to PostgreSQL...")
    if recent_txs:
        service = IngestionService(db)
        res = await service.process_batch(recent_txs)
        logger.info(f"PostgreSQL Ingestion result: {res}")
        
    # 3. Ingest historical transactions into Cloudflare D1
    logger.info(f"Ingesting {len(historical_txs)} historical (>1 week old) transactions to Cloudflare D1...")
    if historical_txs:
        payload_txs = []
        for tx in historical_txs:
            tx_dict = tx.model_dump()
            # Serialize datetimes for JSON transmission
            for k, v in tx_dict.items():
                if isinstance(v, datetime):
                    tx_dict[k] = v.isoformat()
            payload_txs.append(tx_dict)
            
        # Send in batches of 100
        chunk_size = 100
        worker_url = f"{settings.D1_WORKER_URL}/historical/transactions"
        headers = {"X-API-Key": settings.D1_WORKER_API_KEY} if settings.D1_WORKER_API_KEY else {}
        
        success_count = 0
        async with httpx.AsyncClient() as client:
            for i in range(0, len(payload_txs), chunk_size):
                chunk = payload_txs[i:i + chunk_size]
                try:
                    response = await client.post(
                        worker_url,
                        json={"transactions": chunk},
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    success_count += len(chunk)
                except Exception as e:
                    logger.error(f"Failed to ingest batch to D1: {e}")
                    
        logger.info(f"Cloudflare D1 Ingestion result: successfully loaded {success_count}/{len(historical_txs)} transactions.")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", action="store_true", help="Apply database schema")
    parser.add_argument("--merchants", action="store_true", help="Seed merchants and outlets")
    parser.add_argument("--transactions", action="store_true", help="Seed transactions from CSV")
    parser.add_argument("--file", type=str, default=None, help="Custom JSON/CSV dataset path to seed transactions from")
    args = parser.parse_args()

    dsn = settings.DATABASE_URL
    if not dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(dsn)
    
    # We must try connecting to see if the DB exists
    try:
        async with engine.connect() as conn:
            pass
    except Exception as e:
        if "does not exist" in str(e):
            import urllib.parse
            parsed = urllib.parse.urlparse(dsn)
            postgres_dsn = parsed._replace(path="/postgres").geturl()
            
            logger.info("Database 'ops_excellence' does not exist. Connecting to 'postgres' database to create it...")
            temp_engine = create_async_engine(postgres_dsn, isolation_level="AUTOCOMMIT")
            async with temp_engine.connect() as conn:
                await conn.execute(text("CREATE DATABASE ops_excellence"))
            await temp_engine.dispose()
            logger.info("Database 'ops_excellence' created successfully.")
    
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as db:
        if args.schema:
            await apply_schema(db)
        
        if args.merchants:
            await seed_merchants_and_outlets(db)
            
        if args.transactions:
            await seed_transactions(db, args.file)
            
        if not any([args.schema, args.merchants, args.transactions]):
            logger.info("No flags provided. Use --schema, --merchants, or --transactions.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
