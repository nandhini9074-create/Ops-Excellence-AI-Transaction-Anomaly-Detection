from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from app.schemas.transaction import TransactionCreate


class TransactionCleaner:
    def clean_transaction(self, tx: Any) -> Any:
        is_pydantic = hasattr(tx, 'model_dump')
        c_tx = tx.model_dump() if is_pydantic else dict(tx)
        
        # 1. Null validation / cleanup
        for key in ['transaction_id', 'transaction_no', 'group_id', 'group_transaction_id']:
            if c_tx.get(key) in ('', 'null', 'None', None):
                c_tx[key] = None
                
        # 2. Timestamp normalization
        for ts_field in ['transaction_timestamp', 'posting_timestamp', 'created_on', 'last_updated_on', 'silver_updated_at']:
            val = c_tx.get(ts_field)
            if val:
                if isinstance(val, str):
                    try:
                        parsed = pd.to_datetime(val)
                        c_tx[ts_field] = parsed.to_pydatetime() if is_pydantic else parsed.isoformat()
                    except:
                        c_tx[ts_field] = None
                elif isinstance(val, datetime):
                    c_tx[ts_field] = val if is_pydantic else val.isoformat()
        
        # 3. Amount validation (ensure float)
        try:
            c_tx['transaction_amount'] = float(c_tx.get('transaction_amount', 0.0))
        except (ValueError, TypeError):
            pass
            
        # 4. Card scheme normalization
        scheme = c_tx.get('card_scheme')
        if scheme:
            scheme = str(scheme).strip().upper()
            if 'VISA' in scheme:
                c_tx['card_scheme'] = 'VISA'
            elif 'MASTER' in scheme:
                c_tx['card_scheme'] = 'MASTERCARD'
                
        if is_pydantic:
            return TransactionCreate(**c_tx)
        return c_tx

    def clean_batch(self, transactions: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        return [self.clean_transaction(tx) for tx in transactions]
