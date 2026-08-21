import pandas as pd
import httpx
import uuid
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_

from app.config import settings
from app.database.models import Outlet, MerchantWhitelist, Baseline
from baseline.features import extract_volume_features, extract_amount_features, extract_card_features
from baseline.seasonality import extract_time_and_seasonality_features
from baseline.thresholds import calculate_dynamic_thresholds

logger = logging.getLogger(__name__)

class BaselineBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.worker_url = f"{settings.D1_WORKER_URL}/historical/window"
        self.headers = {"X-API-Key": settings.D1_WORKER_API_KEY} if settings.D1_WORKER_API_KEY else {}

    async def fetch_historical_data(self, outlet_id: str, days: int) -> pd.DataFrame:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self.worker_url,
                    params={"outlet_id": outlet_id, "days": days},
                    headers=self.headers,
                    timeout=30.0
                )
                resp.raise_for_status()
                data = resp.json().get("results", [])
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch historical data for outlet {outlet_id}: {e}")
            return pd.DataFrame()

    async def build_for_all_outlets(self, days: int = settings.BASELINE_HISTORY_DAYS):
        stmt = select(Outlet)
        result = await self.db.execute(stmt)
        outlets = result.scalars().all()
        
        for outlet in outlets:
            outlet_id_str = str(outlet.id)
            logger.info(f"Building baseline for outlet {outlet.id} ({outlet.name})")
            
            # Fetch data from D1
            df = await self.fetch_historical_data(outlet_id_str, days)
            
            if df.empty:
                logger.warning(f"No historical data for outlet {outlet.id}. Skipping baseline.")
                continue
                
            # Check if merchant is in whitelist
            stmt_wl = select(MerchantWhitelist).where(
                or_(MerchantWhitelist.outlet_id == outlet.id, MerchantWhitelist.merchant_id == outlet.merchant_id)
            )
            wl_res = await self.db.execute(stmt_wl)
            wl = wl_res.scalar_one_or_none()
            
            # Default values if merchant is not whitelisted
            multiplier = 1.0
            is_whitelisted = False
            
            # If whitelist record exists, update values
            if wl:
                if wl.threshold_multiplier:
                    multiplier = float(wl.threshold_multiplier)
                if str(wl.is_whitelisted).lower() == 'true':
                    is_whitelisted = True

            # Extract features
            vol_feat = extract_volume_features(df)
            amt_feat = extract_amount_features(df)
            card_feat = extract_card_features(df)
            time_feat = extract_time_and_seasonality_features(df)
            thresh_feat = calculate_dynamic_thresholds(vol_feat, amt_feat, threshold_multiplier=multiplier)
            thresh_feat['is_whitelisted'] = is_whitelisted
            
            profile_data = {
                "volume": vol_feat,
                "amount": amt_feat,
                "card": card_feat,
                "time": time_feat,
                "thresholds": thresh_feat
            }
            
            # Deactivate old baselines
            stmt_upd = update(Baseline).where(Baseline.outlet_id == outlet.id).where(Baseline.is_active == 'true').values(is_active='false')
            await self.db.execute(stmt_upd)
                
            # Create new baseline
            new_baseline = Baseline(
                id=str(uuid.uuid4()),
                outlet_id=outlet.id,
                profile_data=profile_data,
                analyzed_days=days,
                data_points_count=len(df),
                is_active='true'
            )
            self.db.add(new_baseline)
            
            await self.db.commit()
