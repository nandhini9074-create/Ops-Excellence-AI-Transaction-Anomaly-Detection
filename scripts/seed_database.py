import asyncio
import sys
import os
import argparse
import asyncpg
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_schema(conn: asyncpg.Connection):
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "database", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            sql = f.read()
        logger.info("Applying schema.sql...")
        await conn.execute(sql)
        logger.info("Schema applied successfully.")
    else:
        logger.error(f"Schema file not found at {schema_path}")

async def seed_merchants_and_outlets(conn: asyncpg.Connection):
    logger.info("Seeding merchants and outlets...")
    import uuid
    
    # 1. Create Merchants
    m1_id = str(uuid.uuid4())
    m2_id = str(uuid.uuid4())
    m3_id = str(uuid.uuid4())
    
    await conn.execute("INSERT INTO merchants (id, name, mcc) VALUES ($1, $2, $3)", m1_id, "India Bistro", "5812")
    await conn.execute("INSERT INTO merchants (id, name, mcc) VALUES ($1, $2, $3)", m2_id, "Coffee Planet", "5814")
    await conn.execute("INSERT INTO merchants (id, name, mcc) VALUES ($1, $2, $3)", m3_id, "fnp.ae", "5992")

    # 2. Create Outlets
    o1_id = str(uuid.uuid4())
    o2_id = str(uuid.uuid4())
    o3_id = str(uuid.uuid4())
    o4_id = str(uuid.uuid4())
    
    await conn.execute("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES ($1, $2, $3, $4)", o1_id, m1_id, "Dubai WTC", "Dubai")
    await conn.execute("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES ($1, $2, $3, $4)", o2_id, m1_id, "Sharjah Center", "Sharjah")
    await conn.execute("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES ($1, $2, $3, $4)", o3_id, m2_id, "Etihad Plaza", "Abu Dhabi")
    await conn.execute("INSERT INTO outlets (id, merchant_id, name, location_city) VALUES ($1, $2, $3, $4)", o4_id, m3_id, "E-Commerce", "Online")

    logger.info("Merchants and outlets seeded.")

async def seed_transactions(conn: asyncpg.Connection):
    logger.info("Loading generated transactions...")
    from data_pipeline.generators.dataset_generator import load_dataset
    df = load_dataset("data/development_dataset.csv")
    
    if df.empty:
        logger.warning("Dataset is empty. Run dataset_generator.py first.")
        return
        
    logger.info(f"Ingesting {len(df)} transactions...")
    
    import httpx
    # Assuming FastAPI is running for bulk endpoint testing, OR we just use the repo
    # To test the repo, we can call it directly
    from backend.app.schemas.transaction import TransactionCreate
    from data_pipeline.ingestion.ingestion_service import IngestionService
    
    service = IngestionService(conn)
    
    # Map dataframe to Pydantic objects
    import numpy as np
    df = df.replace({np.nan: None})
    
    transactions = []
    for _, row in df.iterrows():
        tx = TransactionCreate(
            transaction_id=row.get('transaction_id'),
            transaction_no=row.get('transaction_no'),
            group_id=row.get('group_id'),
            group_transaction_id=row.get('group_transaction_id'),
            outlet_id=str(row['outlet_id']),
            merchant_id=str(row['merchant_id']),
            transaction_timestamp=row['transaction_timestamp'],
            txn_date=row['txn_date'],
            txn_hour=row['txn_hour'],
            transaction_amount=float(row['transaction_amount']),
            card_scheme=row.get('card_scheme')
        )
        transactions.append(tx)
        
    result = await service.process_batch(transactions)
    logger.info(f"Ingestion result: {result}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", action="store_true", help="Apply database schema")
    parser.add_argument("--merchants", action="store_true", help="Seed merchants and outlets")
    parser.add_argument("--transactions", action="store_true", help="Seed transactions from CSV")
    args = parser.parse_args()

    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn=dsn)
    
    try:
        if args.schema:
            await apply_schema(conn)
        
        if args.merchants:
            await seed_merchants_and_outlets(conn)
            
        if args.transactions:
            await seed_transactions(conn)
            
        if not any([args.schema, args.merchants, args.transactions]):
            logger.info("No flags provided. Use --schema, --merchants, or --transactions.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
