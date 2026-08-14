from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import uuid

class TransactionBase(BaseModel):
    transaction_id: Optional[str] = None
    transaction_no: Optional[str] = None
    
    group_id: Optional[str] = None
    group_transaction_id: Optional[str] = None
    
    payout_transaction_id: Optional[str] = None
    
    outlet_id: str
    merchant_id: str
    profile_id: str
    
    transaction_timestamp: datetime
    posting_timestamp: Optional[datetime] = None
    txn_date: str
    txn_hour: str
    
    created_on: Optional[datetime] = None
    last_updated_on: Optional[datetime] = None
    silver_updated_at: Optional[datetime] = None
    
    transaction_amount: float
    card_scheme: Optional[str] = None
    
    merchant_name: Optional[str] = None
    outlet_name: Optional[str] = None
    outlet_status: Optional[str] = None

class TransactionCreate(TransactionBase):
    @model_validator(mode="after")
    def check_transaction_exclusivity(self):
        has_normal = bool(self.transaction_id) and bool(self.transaction_no)
        has_group = bool(self.group_id) and bool(self.group_transaction_id)
        
        if has_normal and has_group:
            raise ValueError("Transaction cannot have both normal IDs and group IDs")
        if not has_normal and not has_group:
            raise ValueError("Transaction must have either normal IDs or group IDs")
            
        if self.group_id and self.group_id != "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e":
            raise ValueError("Unknown group_id provided")
            
        return self

class TransactionResponse(TransactionBase):
    id: str
    ingested_at: datetime
    
    class Config:
        from_attributes = True

class TransactionBulkCreate(BaseModel):
    transactions: List[dict]
    
class BulkIngestionResponse(BaseModel):
    total_received: int
    successful: int
    failed: int
    errors: List[dict] = []
