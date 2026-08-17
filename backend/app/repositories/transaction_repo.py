from typing import List, Optional
import asyncpg
import uuid
from datetime import datetime, timezone

from app.schemas.transaction import TransactionCreate

class TransactionRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_recent_transactions(self, hours: int = 4) -> List[dict]:
        """Fetch transactions from the last N hours."""
        query = """
            SELECT * FROM transactions 
            WHERE transaction_timestamp >= NOW() - INTERVAL '1 hour' * $1
            ORDER BY transaction_timestamp ASC
        """
        records = await self.conn.fetch(query, hours)
        return [dict(r) for r in records]

    async def create_bulk(self, transactions: List[TransactionCreate]) -> List[dict]:
        """Bulk insert using executemany for better performance."""
        if not transactions:
            return []

        query = """
            INSERT INTO transactions (
                id, transaction_id, transaction_no, group_id, group_transaction_id, payout_transaction_id,
                outlet_id, merchant_id, profile_id, transaction_timestamp, posting_timestamp,
                txn_date, txn_hour, created_on, last_updated_on, silver_updated_at,
                transaction_amount, card_scheme, merchant_name, outlet_name, outlet_status
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
            ) RETURNING id
        """

        values = []
        for tx in transactions:
            tx_id = str(uuid.uuid4())
            
            # Parse txn_date to datetime.date if it is passed as a string
            txn_date_val = tx.txn_date
            if isinstance(txn_date_val, str):
                from datetime import datetime as dt_class
                txn_date_val = dt_class.strptime(txn_date_val, "%Y-%m-%d").date()
                
            values.append((
                tx_id,
                tx.transaction_id,
                tx.transaction_no,
                tx.group_id,
                tx.group_transaction_id,
                tx.payout_transaction_id,
                tx.outlet_id,
                tx.merchant_id,
                tx.profile_id,
                tx.transaction_timestamp.replace(tzinfo=timezone.utc) if tx.transaction_timestamp else None,
                tx.posting_timestamp.replace(tzinfo=timezone.utc) if tx.posting_timestamp else None,
                txn_date_val,
                int(tx.txn_hour) if tx.txn_hour is not None else None,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
                tx.silver_updated_at.replace(tzinfo=timezone.utc) if tx.silver_updated_at else None,
                tx.transaction_amount,
                tx.card_scheme,
                tx.merchant_name,
                tx.outlet_name,
                tx.outlet_status
            ))

        # Because we need RETURNING, we might want to run them in a loop or use unnest.
        # However, for pure speed asyncpg has copy_records_to_table but it doesn't return IDs easily.
        # We'll use a transaction and executemany, but executemany doesn't support RETURNING in asyncpg.
        # So we will execute them individually inside a transaction block if we really need IDs,
        # or we just assume success. Let's do individual inserts in a transaction since it's batch anyway.
        
        inserted = []
        async with self.conn.transaction():
            for val in values:
                res_id = await self.conn.fetchval(query, *val)
                inserted.append({"id": res_id})
                
        return inserted
