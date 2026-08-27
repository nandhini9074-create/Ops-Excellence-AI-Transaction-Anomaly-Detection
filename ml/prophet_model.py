import pandas as pd
import logging
from typing import List, Any, Optional
from app.config import settings
from ml.zscore import DetectorResult

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    logger.warning("Prophet not available. Time-series forecasting will be skipped.")
    PROPHET_AVAILABLE = False

class ProphetDetector:
    def __init__(self, baseline_profile: dict, history_df: Optional[pd.DataFrame] = None):
        """
        Prophet needs historical data to fit the model.
        We pass history_df when initializing the detector for a run.
        """
        self.baseline = baseline_profile
        self.history_df = history_df

    def detect(self, df_recent: Any) -> List[DetectorResult]:
        results = []
        if not PROPHET_AVAILABLE or df_recent.empty or self.history_df is None or self.history_df.empty:
            return results
            
        try:
            # Prepare data for Prophet (daily volume)
            # Combine history and recent to see if recent is out of bounds
            # For simplicity, we just train on history and predict the current day's expected volume
            
            self.history_df['datetime'] = pd.to_datetime(self.history_df['transaction_timestamp'])
            self.history_df['date'] = self.history_df['datetime'].dt.normalize()
            daily_volumes = self.history_df.groupby('date').size().reset_index()
            daily_volumes.columns = ['ds', 'y']
            
            if len(daily_volumes) < 7:
                # Not enough history for Prophet
                return results

            # Predict for the current date of the recent transactions
            df_recent['datetime'] = pd.to_datetime(df_recent['transaction_timestamp'])
            current_date = pd.to_datetime(df_recent['transaction_timestamp'].iloc[0]).date()
            
            try:
                if not PROPHET_AVAILABLE:
                    raise Exception("Prophet not available")
                model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
                model.fit(daily_volumes)
                # [BASELINE COMPARISON]: Fits Prophet time-series model on historical baseline & predicts expected range
                future = pd.DataFrame({'ds': [pd.to_datetime(current_date)]})
                forecast = model.predict(future)
                expected_vol = forecast['yhat'].iloc[0]
                yhat_lower = forecast['yhat_lower'].iloc[0]
                yhat_upper = forecast['yhat_upper'].iloc[0]
            except Exception as e:
                logger.warning(f"Prophet failed, using statistical fallback: {e}")
                # Fallback: simple mean and standard deviation
                mean_vol = daily_volumes['y'].mean()
                std_vol = daily_volumes['y'].std()
                if pd.isna(std_vol) or std_vol == 0:
                    std_vol = max(1.0, mean_vol * 0.1)
                
                expected_vol = mean_vol
                yhat_lower = max(0, mean_vol - (3 * std_vol))
                yhat_upper = mean_vol + (3 * std_vol)
            
            actual_vol = len(df_recent) # this is 24 hours volume, no projection needed
            projected_daily_vol = actual_vol
            
            # [ANOMALY DECISION]: Checks if projected volume falls outside expected baseline forecast bounds [yhat_lower, yhat_upper]
            if projected_daily_vol > yhat_upper or projected_daily_vol < yhat_lower:
                # Anomaly
                anomaly_type = "VOLUME_SPIKE" if projected_daily_vol > yhat_upper else "VOLUME_DROP"
                
                # Calculate normalized score
                diff = abs(projected_daily_vol - expected_vol)
                margin = (yhat_upper - expected_vol) if expected_vol > 0 else 1
                raw_score = min(1.0, 0.5 + (diff / margin) * 0.5)
                
                res = DetectorResult(
                    detector_name="prophet",
                    raw_score=raw_score,
                    anomaly_type=anomaly_type,
                    expected_value=float(expected_vol),
                    actual_value=float(projected_daily_vol),
                    explanation=f"Projected daily volume {projected_daily_vol:.0f} is outside forecasted range [{yhat_lower:.0f}, {yhat_upper:.0f}].",
                    details={"yhat": expected_vol, "yhat_lower": yhat_lower, "yhat_upper": yhat_upper}
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"Prophet detector failed: {e}")
            
        return results
