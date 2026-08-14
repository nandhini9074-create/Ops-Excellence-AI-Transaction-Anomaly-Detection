import httpx
from datetime import datetime, timedelta, timezone
import asyncpg
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class HistoricalSyncService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.worker_url = f"{settings.D1_WORKER_URL}/historical/transactions"
        self.headers = {"X-API-Key": settings.D1_WORKER_API_KEY} if settings.D1_WORKER_API_KEY else {}

    async def sync_older_than(self, days: int = 7) -> dict:
        """
        Fetches transactions older than `days` from PostgreSQL,
        sends them to Cloudflare D1, and deletes them from hot storage.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 1. Fetch old transactions
        query = "SELECT * FROM transactions WHERE transaction_timestamp < $1 LIMIT 500"
        old_txs = await self.conn.fetch(query, cutoff_date)
        
        if not old_txs:
            return {"status": "success", "processed": 0, "message": "No transactions to sync"}

        # 2. Prepare payload
        payload_txs = []
        for tx in old_txs:
            tx_dict = dict(tx)
            # Serialize datetimes to isoformat for JSON
            for key, val in tx_dict.items():
                if isinstance(val, datetime):
                    tx_dict[key] = val.isoformat()
            
            payload_txs.append(tx_dict)

        # 3. Send to D1 Worker
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.worker_url,
                    json={"transactions": payload_txs},
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to sync to D1: {str(e)}")
            return {"status": "error", "processed": 0, "error": str(e)}

        # 4. Delete from PostgreSQL if successful
        try:
            ids_to_delete = [tx['id'] for tx in old_txs]
            await self.conn.execute("DELETE FROM transactions WHERE id = ANY($1::uuid[])", ids_to_delete)
            return {"status": "success", "processed": len(ids_to_delete)}
        except Exception as e:
            logger.error(f"Failed to delete from Postgres after sync: {str(e)}")
            return {"status": "error", "processed": 0, "error": f"D1 synced but PG delete failed: {str(e)}"}
