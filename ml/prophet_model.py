import pandas as pd
import logging
from typing import List, Any
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
    def __init__(self, baseline_profile: dict, history_df: pd.DataFrame = None):
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
            self.history_df['date'] = self.history_df['datetime'].dt.date
            daily_volumes = self.history_df.groupby('date').size().reset_index()
            daily_volumes.columns = ['ds', 'y']
            
            if len(daily_volumes) < 7:
                # Not enough history for Prophet
                return results

            model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
            model.fit(daily_volumes)
            
            # Predict for the current date of the recent transactions
            df_recent['datetime'] = pd.to_datetime(df_recent['transaction_timestamp'])
            current_date = df_recent['datetime'].dt.date.iloc[0]
            
            # [BASELINE COMPARISON]: Fits Prophet time-series model on historical baseline & predicts expected range
            future = pd.DataFrame({'ds': [pd.to_datetime(current_date)]})
            forecast = model.predict(future)
            
            expected_vol = forecast['yhat'].iloc[0]
            yhat_lower = forecast['yhat_lower'].iloc[0]
            yhat_upper = forecast['yhat_upper'].iloc[0]
            
            actual_vol = len(df_recent) # this is 4-5 hours volume, so we need to project it to daily
            # Project 4-5 hours to daily based on hourly distribution
            hours_covered = df_recent['datetime'].dt.hour.nunique()
            if hours_covered == 0: hours_covered = 1
            projected_daily_vol = actual_vol * (24 / hours_covered)
            
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
                    raw_score=float(raw_score),
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
