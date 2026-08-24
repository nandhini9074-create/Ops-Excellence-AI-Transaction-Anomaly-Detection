from typing import List, Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.transaction import TransactionCreate
from data_pipeline.validation.business_rules import validate_transaction_exclusive_rule, validate_group_id
from data_pipeline.cleaning.cleaner import TransactionCleaner
from app.repositories.transaction_repo import TransactionRepository

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cleaner = TransactionCleaner()
        self.repo = TransactionRepository(db)

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
                # Dynamically seed missing merchants and outlets to satisfy foreign keys
                from sqlalchemy.dialects.postgresql import insert
                from app.database.models import Merchant, Outlet, Profile
                
                unique_merchants = {}
                unique_outlets = {}
                unique_profiles = {}
                
                for tx in valid_txs:
                    unique_merchants[tx.merchant_id] = tx.merchant_name or "Unknown"
                    unique_outlets[tx.outlet_id] = {
                        "merchant_id": tx.merchant_id,
                        "name": tx.outlet_name or "Unknown"
                    }
                    if tx.profile_id:
                        unique_profiles[tx.profile_id] = tx.outlet_id
                        
                for m_id, m_name in unique_merchants.items():
                    stmt = insert(Merchant).values(id=m_id, name=m_name, mcc='0000').on_conflict_do_nothing(index_elements=['id'])
                    await self.db.execute(stmt)
                    
                for o_id, o_data in unique_outlets.items():
                    stmt = insert(Outlet).values(id=o_id, merchant_id=o_data["merchant_id"], name=o_data["name"], location_city='Unknown').on_conflict_do_nothing(index_elements=['id'])
                    await self.db.execute(stmt)
                    
                for p_id, o_id in unique_profiles.items():
                    stmt = insert(Profile).values(id=p_id, outlet_id=o_id, risk_score=0.0, segment='STANDARD').on_conflict_do_nothing(index_elements=['id'])
                    await self.db.execute(stmt)
                    
                await self.db.commit()

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
