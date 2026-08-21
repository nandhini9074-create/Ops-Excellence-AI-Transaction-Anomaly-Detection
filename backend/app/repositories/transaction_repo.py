from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import class_mapper

from app.schemas.transaction import TransactionCreate
from app.database.models import Transaction

def row2dict(row):
    return {c.name: getattr(row, c.name) for c in class_mapper(row.__class__).columns}

class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_transactions(self, hours: int = 4) -> List[dict]:
        """Fetch transactions from the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(Transaction).where(Transaction.transaction_timestamp >= cutoff_time).order_by(Transaction.transaction_timestamp.asc())
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [row2dict(r) for r in records]

    async def create_bulk(self, transactions: List[TransactionCreate]) -> List[dict]:
        """Bulk insert using SQLAlchemy."""
        if not transactions:
            return []

        inserted = []
        for tx in transactions:
            tx_id = str(uuid.uuid4())
            
            txn_date_val = tx.txn_date
            if isinstance(txn_date_val, str):
                from datetime import datetime as dt_class
                txn_date_val = dt_class.strptime(txn_date_val, "%Y-%m-%d").date()
                
            db_tx = Transaction(
                id=tx_id,
                transaction_id=tx.transaction_id,
                transaction_no=tx.transaction_no,
                group_id=tx.group_id,
                group_transaction_id=tx.group_transaction_id,
                payout_transaction_id=tx.payout_transaction_id,
                outlet_id=tx.outlet_id,
                merchant_id=tx.merchant_id,
                profile_id=tx.profile_id,
                transaction_timestamp=tx.transaction_timestamp.replace(tzinfo=timezone.utc) if tx.transaction_timestamp else None,
                posting_timestamp=tx.posting_timestamp.replace(tzinfo=timezone.utc) if tx.posting_timestamp else None,
                txn_date=txn_date_val,
                txn_hour=int(tx.txn_hour) if tx.txn_hour is not None else 0,
                created_on=datetime.now(timezone.utc),
                last_updated_on=datetime.now(timezone.utc),
                silver_updated_at=tx.silver_updated_at.replace(tzinfo=timezone.utc) if tx.silver_updated_at else None,
                transaction_amount=tx.transaction_amount,
                card_scheme=tx.card_scheme,
                merchant_name=tx.merchant_name,
                outlet_name=tx.outlet_name,
                outlet_status=tx.outlet_status
            )
            self.db.add(db_tx)
            inserted.append({"id": tx_id})
            
        await self.db.commit()
        return inserted
