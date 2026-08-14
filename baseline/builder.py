import pandas as pd
import httpx
import uuid
import json
import logging
import asyncpg

from app.config import settings
from baseline.features import extract_volume_features, extract_amount_features, extract_card_features
from baseline.seasonality import extract_time_and_seasonality_features
from baseline.thresholds import calculate_dynamic_thresholds

logger = logging.getLogger(__name__)

class BaselineBuilder:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
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
        query = "SELECT * FROM outlets"
        outlets = await self.conn.fetch(query)
        
        for outlet in outlets:
            outlet_id_str = str(outlet['id'])
            logger.info(f"Building baseline for outlet {outlet['id']} ({outlet['name']})")
            
            # Fetch data from D1
            df = await self.fetch_historical_data(outlet_id_str, days)
            
            if df.empty:
                logger.warning(f"No historical data for outlet {outlet['id']}. Skipping baseline.")
                continue
                
            # Extract features
            vol_feat = extract_volume_features(df)
            amt_feat = extract_amount_features(df)
            card_feat = extract_card_features(df)
            time_feat = extract_time_and_seasonality_features(df)
            thresh_feat = calculate_dynamic_thresholds(vol_feat, amt_feat)
            
            profile_data = {
                "volume": vol_feat,
                "amount": amt_feat,
                "card": card_feat,
                "time": time_feat,
                "thresholds": thresh_feat
            }
            
            async with self.conn.transaction():
                # Deactivate old baselines
                await self.conn.execute(
                    "UPDATE baselines SET is_active = 'false' WHERE outlet_id = $1 AND is_active = 'true'",
                    outlet['id']
                )
                    
                # Create new baseline
                await self.conn.execute(
                    """
                    INSERT INTO baselines (id, outlet_id, profile_data, analyzed_days, data_points_count, is_active)
                    VALUES ($1, $2, $3, $4, $5, 'true')
                    """,
                    str(uuid.uuid4()),
                    outlet['id'],
                    json.dumps(profile_data),
                    days,
                    len(df)
                )
