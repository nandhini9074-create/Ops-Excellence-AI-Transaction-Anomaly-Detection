import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, text
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
from ml.remarks_builder import build_human_remarks
from app.database.models import ProcessingRun, Issue, MerchantWhitelist, Baseline

logger = logging.getLogger(__name__)

async def run_historical_sync():
    logger.info("Starting scheduled historical sync...")
    async with db_conn.async_session_maker() as db:
        service = HistoricalSyncService(db)
        res = await service.sync_older_than(days=7)
        logger.info(f"Historical sync finished: {res}")

async def run_baseline_builder():
    logger.info("Starting scheduled baseline builder...")
    async with db_conn.async_session_maker() as db:
        import uuid
        from datetime import datetime, timezone
        
        run_id = str(uuid.uuid4())
        pr = ProcessingRun(id=run_id, run_type='BASELINE_BUILDER', status='RUNNING')
        db.add(pr)
        await db.commit()
        
        try:
            builder = BaselineBuilder(db)
            await builder.build_for_all_outlets(settings.BASELINE_HISTORY_DAYS)
            
            pr.status = 'COMPLETED'
            pr.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as e:
            pr.status = 'FAILED'
            pr.error_message = str(e)
            await db.commit()
            logger.error(f"Baseline builder failed: {e}")

async def run_anomaly_detection():
    logger.info("Starting scheduled anomaly detection...")
    async with db_conn.async_session_maker() as db:
        import uuid
        from datetime import datetime, timezone, timedelta
        
        run_id = str(uuid.uuid4())
        pr = ProcessingRun(id=run_id, run_type='ANOMALY_DETECTION', status='RUNNING')
        db.add(pr)
        await db.commit()
        
        try:
            # 1. Sprint 81: Dormancy Check (20+ days inactive)
            dormancy_query = text("""
                SELECT o.id as outlet_id, o.merchant_id, m.name as merchant_name, o.name as outlet_name,
                       MAX(t.transaction_timestamp) as last_tx_date,
                       EXTRACT(DAY FROM (NOW() - MAX(t.transaction_timestamp))) as days_inactive
                FROM outlets o
                JOIN merchants m ON o.merchant_id = m.id
                JOIN transactions t ON t.outlet_id = o.id
                GROUP BY o.id, o.merchant_id, m.name, o.name
                HAVING EXTRACT(DAY FROM (NOW() - MAX(t.transaction_timestamp))) >= 20
            """)
            result = await db.execute(dormancy_query)
            dormant_outlets = result.mappings().all()
            
            issue_repo = IssueRepository(db)
            anomalies_found = 0
            
            for d_out in dormant_outlets:
                # Fix 4: Skip outlets that an operator has suppressed via false-positive feedback
                stmt = select(MerchantWhitelist).where(
                    MerchantWhitelist.outlet_id == d_out['outlet_id'],
                    MerchantWhitelist.dormancy_suppressed_until > datetime.now(timezone.utc)
                )
                suppressed = (await db.execute(stmt)).scalar_one_or_none()
                if suppressed:
                    logger.info(f"Dormancy suppressed for {d_out['outlet_name']} — skipping.")
                    continue

                # Fix 1: Deduplication with 7-day cooldown
                stmt_dup = select(Issue).where(
                    Issue.outlet_id == str(d_out['outlet_id']),
                    Issue.anomaly_type == 'DORMANCY'
                )
                dup_res = await db.execute(stmt_dup)
                issues = dup_res.scalars().all()
                existing = any(
                    i.status in ['OPEN', 'ACKNOWLEDGED'] or 
                    (i.status in ['RESOLVED', 'FALSE_POSITIVE'] and i.resolved_at and i.resolved_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - timedelta(days=7)) 
                    for i in issues
                )
                
                if not existing:
                    days = int(d_out['days_inactive'])
                    issue_in = IssueCreate(
                        anomaly_id=str(uuid.uuid4()),
                        merchant_id=str(d_out['merchant_id']),
                        merchant_name=d_out['merchant_name'],
                        outlet_id=str(d_out['outlet_id']),
                        outlet_name=d_out['outlet_name'],
                        anomaly_type="DORMANCY",
                        anomaly_score=1.0,
                        confidence_score=1.0,
                        severity="MEDIUM",
                        remarks=f"This outlet has had no transactions for {days} days. A runner test or merchant call is recommended.",
                        detected_at=datetime.now(timezone.utc)
                    )
                    await issue_repo.create(issue_in)
                    anomalies_found += 1
                    logger.info(f"Created DORMANCY alert for {d_out['outlet_name']} ({days} days inactive)")

            # 2. Get recent transactions for normal ML anomaly detection
            tx_repo = TransactionRepository(db)
            recent_txs = await tx_repo.get_recent_transactions(hours=24)
            
            if not recent_txs:
                logger.info("No recent transactions to analyze.")
                pr.status = 'COMPLETED'
                pr.completed_at = datetime.now(timezone.utc)
                pr.records_processed = 0
                await db.commit()
                return
                
            import pandas as pd
            df = pd.DataFrame(recent_txs)
            
            # Group by outlet
            outlets = df['outlet_id'].unique()
            
            for outlet_id in outlets:
                outlet_df = pd.DataFrame(df[df['outlet_id'] == outlet_id])
                
                # Fetch baseline
                stmt_base = select(Baseline).where(Baseline.outlet_id == outlet_id, Baseline.is_active == 'true')
                record = (await db.execute(stmt_base)).scalar_one_or_none()
                
                if not record:
                    continue # Cannot detect without baseline
                    
                profile_data = record.profile_data
                if isinstance(profile_data, str):
                    profile_data = json.loads(profile_data)
                    
                engine = AnomalyDetectionEngine(profile_data)
                anomaly_results = engine.analyze(outlet_df)
                
                if anomaly_results:
                    row = outlet_df.iloc[0]
                    for anomaly_result in anomaly_results:
                        # Sprint 81: Alert Deduplication
                        stmt_dup_ml = select(Issue).where(
                            Issue.outlet_id == str(row['outlet_id']),
                            Issue.anomaly_type == anomaly_result['anomaly_type'],
                            Issue.status.in_(['OPEN', 'ACKNOWLEDGED'])
                        )
                        existing = (await db.execute(stmt_dup_ml)).scalar_one_or_none()
                        
                        if existing:
                            logger.info(f"Suppressed duplicate alert for {row['outlet_name']} ({anomaly_result['anomaly_type']})")
                            continue
                            
                        anomalies_found += 1
                        
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
                            scheme=str(row.get('card_scheme', '')) if 'card_scheme' in row else None,
                            remarks=build_human_remarks(anomaly_result),
                            detected_at=datetime.now(timezone.utc)
                        )
                        
                        await issue_repo.create(issue_in)
                        
                        # Notify
                        anomaly_result['merchant_name'] = row['merchant_name']
                        anomaly_result['outlet_name'] = row['outlet_name']
                        await NotificationService.broadcast_anomaly(anomaly_result)
            
            pr.status = 'COMPLETED'
            pr.completed_at = datetime.now(timezone.utc)
            pr.records_processed = len(recent_txs)
            pr.anomalies_detected = anomalies_found
            await db.commit()
            
        except Exception as e:
            pr.status = 'FAILED'
            pr.error_message = str(e)
            await db.commit()
            logger.error(f"Anomaly detection failed: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_historical_sync, CronTrigger(day='1,15', hour=3, minute=0))
    scheduler.add_job(run_baseline_builder, CronTrigger(day='1,15', hour=3, minute=0))
    scheduler.add_job(run_anomaly_detection, CronTrigger(hour=6, minute=0))
    scheduler.start()
    logger.info("Scheduler started.")
