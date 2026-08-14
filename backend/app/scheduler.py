import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncpg
import app.database.connection as db_conn
from app.config import settings
from app.services.historical_sync import HistoricalSyncService
from baseline.builder import BaselineBuilder
from ml.detector import AnomalyDetectionEngine
from app.repositories.transaction_repo import TransactionRepository
from app.services.notification_service import NotificationService
from app.schemas.issue import IssueCreate
from app.repositories.issue_repo import IssueRepository
import json

logger = logging.getLogger(__name__)

async def run_historical_sync():
    logger.info("Starting scheduled historical sync...")
    if not db_conn._pool: return
    async with db_conn._pool.acquire() as conn:
        service = HistoricalSyncService(conn)
        res = await service.sync_older_than(days=7)
        logger.info(f"Historical sync finished: {res}")

async def run_baseline_builder():
    logger.info("Starting scheduled baseline builder...")
    if not db_conn._pool: return
    async with db_conn._pool.acquire() as conn:
        import uuid
        run_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO processing_runs (id, run_type, status) VALUES ($1, 'BASELINE_BUILDER', 'RUNNING')", run_id)
        
        try:
            builder = BaselineBuilder(conn)
            await builder.build_for_all_outlets(settings.BASELINE_HISTORY_DAYS)
            
            await conn.execute("UPDATE processing_runs SET status = 'COMPLETED', completed_at = NOW() WHERE id = $1", run_id)
        except Exception as e:
            await conn.execute("UPDATE processing_runs SET status = 'FAILED', error_message = $1 WHERE id = $2", str(e), run_id)
            logger.error(f"Baseline builder failed: {e}")

async def run_anomaly_detection():
    logger.info("Starting scheduled anomaly detection...")
    if not db_conn._pool: return
    async with db_conn._pool.acquire() as conn:
        import uuid
        run_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO processing_runs (id, run_type, status) VALUES ($1, 'ANOMALY_DETECTION', 'RUNNING')", run_id)
        
        try:
            # 1. Get recent transactions
            tx_repo = TransactionRepository(conn)
            recent_txs = await tx_repo.get_recent_transactions(hours=settings.ANOMALY_INTERVAL_HOURS)
            
            if not recent_txs:
                logger.info("No recent transactions to analyze.")
                await conn.execute("UPDATE processing_runs SET status = 'COMPLETED', completed_at = NOW(), records_processed = 0 WHERE id = $1", run_id)
                return
                
            import pandas as pd
            df = pd.DataFrame(recent_txs)
            
            # Group by outlet
            outlets = df['outlet_id'].unique()
            anomalies_found = 0
            
            for outlet_id in outlets:
                outlet_df = df[df['outlet_id'] == outlet_id]
                
                # Fetch baseline
                record = await conn.fetchrow(
                    "SELECT * FROM baselines WHERE outlet_id = $1 AND is_active = 'true'", 
                    outlet_id
                )
                
                if not record:
                    continue # Cannot detect without baseline
                    
                profile_data = json.loads(record['profile_data'])
                engine = AnomalyDetectionEngine(profile_data)
                anomaly_result = engine.analyze(outlet_df)
                
                if anomaly_result:
                    anomalies_found += 1
                    
                    issue_repo = IssueRepository(conn)
                    row = outlet_df.iloc[0]
                    
                    import datetime
                    from datetime import timezone
                    
                    issue_in = IssueCreate(
                        anomaly_id=str(uuid.uuid4()),
                        merchant_id=str(row['merchant_id']),
                        merchant_name=row['merchant_name'],
                        outlet_id=str(row['outlet_id']),
                        outlet_name=row['outlet_name'],
                        anomaly_type=anomaly_result['anomaly_type'],
                        anomaly_score=anomaly_result['anomaly_score'],
                        confidence_score=anomaly_result['confidence_score'],
                        severity=anomaly_result['severity'],
                        detected_at=datetime.datetime.now(timezone.utc)
                    )
                    
                    await issue_repo.create(issue_in)
                    
                    # Notify
                    anomaly_result['merchant_name'] = row['merchant_name']
                    anomaly_result['outlet_name'] = row['outlet_name']
                    await NotificationService.broadcast_anomaly(anomaly_result)
            
            await conn.execute("UPDATE processing_runs SET status = 'COMPLETED', completed_at = NOW(), records_processed = $1, anomalies_detected = $2 WHERE id = $3", len(recent_txs), anomalies_found, run_id)
            
        except Exception as e:
            await conn.execute("UPDATE processing_runs SET status = 'FAILED', error_message = $1 WHERE id = $2", str(e), run_id)
            logger.error(f"Anomaly detection failed: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_historical_sync, CronTrigger(hour=2, minute=0))
    scheduler.add_job(run_baseline_builder, CronTrigger(hour=3, minute=0))
    scheduler.add_job(run_anomaly_detection, IntervalTrigger(hours=settings.ANOMALY_INTERVAL_HOURS))
    scheduler.start()
    logger.info("Scheduler started.")
