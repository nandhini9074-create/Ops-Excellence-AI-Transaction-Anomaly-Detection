from typing import List, Dict, Any, Tuple
from app.schemas.transaction import TransactionCreate
from .business_rules import validate_transaction_exclusive_rule, validate_group_id

class TransactionValidator:
    def __init__(self):
        self.errors = []
        
    def validate_batch(self, transactions: List[Dict[Any, Any]]) -> Tuple[List[Dict], List[Dict]]:
        valid_txs = []
        invalid_txs = []
        
        seen_group_tx_ids = set()
        seen_normal_tx_ids = set()
        
        for idx, tx in enumerate(transactions):
            try:
                # 1. Rule validation
                if not validate_transaction_exclusive_rule(tx):
                    tx['_error'] = "Failed exclusive rule: must have normal OR group IDs, not both/neither"
                    invalid_txs.append(tx)
                    continue
                    
                if not validate_group_id(tx):
                    tx['_error'] = "Invalid group_id"
                    invalid_txs.append(tx)
                    continue
                
                # 2. Check for intra-batch duplicates
                group_tx_id = tx.get('group_transaction_id')
                normal_tx_id = tx.get('transaction_id')
                
                if group_tx_id:
                    if group_tx_id in seen_group_tx_ids:
                        tx['_error'] = "Duplicate group_transaction_id in batch"
                        invalid_txs.append(tx)
                        continue
                    seen_group_tx_ids.add(group_tx_id)
                    
                if normal_tx_id:
                    if normal_tx_id in seen_normal_tx_ids:
                        tx['_error'] = "Duplicate transaction_id in batch"
                        invalid_txs.append(tx)
                        continue
                    seen_normal_tx_ids.add(normal_tx_id)

                # 3. Pydantic validation
                valid_txs.append(TransactionCreate(**tx).model_dump())
                
            except Exception as e:
                tx['_error'] = str(e)
                invalid_txs.append(tx)
                
        return valid_txs, invalid_txs
