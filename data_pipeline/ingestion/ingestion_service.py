from typing import List, Dict
import logging
import asyncpg
from app.schemas.transaction import TransactionCreate
from data_pipeline.validation.business_rules import validate_transaction_exclusive_rule, validate_group_id
from data_pipeline.cleaning.cleaner import TransactionCleaner
from app.repositories.transaction_repo import TransactionRepository

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.cleaner = TransactionCleaner()
        self.repo = TransactionRepository(conn)

    def validate_transaction(self, tx: TransactionCreate) -> bool:
        tx_dict = tx.model_dump()
        
        # Check rule 1: exclusive tx vs group tx
        if not validate_transaction_exclusive_rule(tx_dict):
            return False
            
        # Check rule 2: if group_id exists, must be the authorized group_id
        if tx_dict.get('group_id') is not None:
            if not validate_group_id(tx_dict):
                return False
                
        return True

    async def process_batch(self, transactions: List[TransactionCreate]) -> Dict:
        """
        Cleans, validates, and ingests a batch of transactions.
        """
        valid_txs = []
        failed_count = 0
        
        for tx in transactions:
            # Clean
            cleaned_tx = self.cleaner.clean_transaction(tx)
            
            # Validate
            if self.validate_transaction(cleaned_tx):
                valid_txs.append(cleaned_tx)
            else:
                failed_count += 1
                
        # Persist valid transactions
        successful_count = 0
        if valid_txs:
            try:
                inserted = await self.repo.create_bulk(valid_txs)
                successful_count = len(inserted)
            except Exception as e:
                logger.error(f"Bulk ingestion failed: {str(e)}")
                # If a chunk fails, we count all as failed (in a real scenario, we might retry individually)
                failed_count += len(valid_txs)
                
        return {
            "total_received": len(transactions),
            "successful": successful_count,
            "failed": failed_count
        }
