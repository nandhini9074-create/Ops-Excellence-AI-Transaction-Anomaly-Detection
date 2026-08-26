import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import class_mapper

from app.database.models import Alert
from app.schemas.alert import AlertCreate

def row2dict(row):
    return {c.name: getattr(row, c.name) for c in class_mapper(row.__class__).columns}

class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, alert_id: str) -> Optional[dict]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        return row2dict(alert) if alert else None

    async def create(self, alert_data: AlertCreate) -> dict:
        new_id = str(uuid.uuid4())
        
        alert = Alert(
            id=new_id,
            run_id=str(alert_data.run_id),
            issue_id=str(alert_data.issue_id) if alert_data.issue_id else None,
            outlet_id=str(alert_data.outlet_id),
            merchant_id=str(alert_data.merchant_id),
            merchant_name=alert_data.merchant_name,
            outlet_name=alert_data.outlet_name,
            anomaly_type=alert_data.anomaly_type,
            anomaly_score=alert_data.anomaly_score,
            confidence_score=alert_data.confidence_score,
            severity=alert_data.severity,
            description=alert_data.description,
            volume_class=alert_data.volume_class,
            scheme=alert_data.scheme,
            alert_metadata=alert_data.alert_metadata,
            detected_at=alert_data.detected_at
        )
        
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return row2dict(alert)

    async def link_to_issue(self, alert_id: str, issue_id: str) -> Optional[dict]:
        stmt = update(Alert).where(Alert.id == alert_id).values(issue_id=issue_id).returning(Alert)
        result = await self.db.execute(stmt)
        updated_alert = result.scalar_one_or_none()
        await self.db.commit()
        
        return row2dict(updated_alert) if updated_alert else None
