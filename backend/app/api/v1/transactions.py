from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.connection import get_db
from app.schemas.transaction import TransactionCreate
from data_pipeline.ingestion.ingestion_service import IngestionService

import logging

logger = logging.getLogger("ops_excellence.api.transactions")
router = APIRouter()

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_transactions_bulk(transactions: List[TransactionCreate], db: AsyncSession = Depends(get_db)):
    logger.info(f"Received bulk transaction ingestion request with {len(transactions)} records.")
    service = IngestionService(db)
    result = await service.process_batch(transactions)
    if result["failed"] > 0:
        logger.warning(f"Batch ingestion completed with {result['failed']} failures out of {result['total']} transactions.")
        raise HTTPException(status_code=400, detail=f"Failed to ingest {result['failed']} transactions")
    logger.info(f"Successfully ingested {result['successful']} transactions into database.")
    return {"message": f"Successfully ingested {result['successful']} transactions"}


