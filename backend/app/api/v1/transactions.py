from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List

from app.database.connection import get_db
from app.schemas.transaction import TransactionCreate
from data_pipeline.ingestion.ingestion_service import IngestionService

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def ingest_transaction(transaction: TransactionCreate, db: asyncpg.Connection = Depends(get_db)):
    service = IngestionService(db)
    result = await service.process_batch([transaction])
    if result["failed"] > 0:
        raise HTTPException(status_code=400, detail="Transaction validation failed")
    return {"message": "Transaction ingested successfully"}

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_transactions_bulk(transactions: List[TransactionCreate], db: asyncpg.Connection = Depends(get_db)):
    service = IngestionService(db)
    result = await service.process_batch(transactions)
    if result["failed"] > 0:
        raise HTTPException(status_code=400, detail=f"Failed to ingest {result['failed']} transactions")
    return {"message": f"Successfully ingested {result['successful']} transactions"}
