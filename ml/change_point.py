import pandas as pd
import numpy as np
import logging
import ruptures as rpt
from typing import List, Any, Optional

from ml.zscore import DetectorResult

logger = logging.getLogger(__name__)

class ChangePointDetector:
    def __init__(self, baseline_profile: dict, history_df: Optional[pd.DataFrame] = None):
        """
        Change point detection needs historical context to identify if the current
        behavior represents a regime shift.
        """
        self.baseline = baseline_profile
        self.history_df = history_df

    def detect(self, df_recent: Any) -> List[DetectorResult]:
        results = []
        if df_recent.empty or self.history_df is None or self.history_df.empty:
            return results
            
        try:
            # We combine historical and recent data to find if a shift occurred recently
            combined = pd.concat([self.history_df, df_recent])
            combined['datetime'] = pd.to_datetime(combined['transaction_timestamp'])
            combined['date'] = combined['datetime'].dt.date  # type: ignore
            
            # Aggregate daily
            daily_stats = combined.groupby('date').agg(
                volume=('transaction_amount', 'count'),
                mean_amt=('transaction_amount', 'mean')
            ).reset_index()
            
            if len(daily_stats) < 14: # Need at least 2 weeks
                return results
                
            signal = daily_stats['volume'].values
            
            # PELT algorithm for change point detection
            algo = rpt.Pelt(model="rbf").fit(signal)
            
            # Predict change points
            # pen is the penalty value. Higher penalty = fewer change points
            result = algo.predict(pen=10)
            
            # The last value in result is always the length of the signal
            change_points = result[:-1]
            
            if not change_points:
                return results
                
            # Check if the most recent change point is very recent (e.g. in the last 3 days)
            latest_cp_idx = change_points[-1]
            if latest_cp_idx >= len(signal) - 3:
                # We have a recent change point!
                before_cp = signal[:latest_cp_idx]
                after_cp = signal[latest_cp_idx:]
                
                # [BASELINE COMPARISON]: Calculates pre-shift baseline volume vs post-shift volume
                mean_before = np.mean(before_cp)
                mean_after = np.mean(after_cp)
                
                # [ANOMALY DECISION]: Checks if post-shift volume deviates by >1.5x (increase) or <0.5x (decrease)
                if mean_after > mean_before * 1.5:
                    anomaly_type = "REGIME_CHANGE_INCREASE"
                    score = 0.8
                elif mean_after < mean_before * 0.5:
                    anomaly_type = "REGIME_CHANGE_DECREASE"
                    score = 0.8
                else:
                    return results # Not significant enough
                    
                res = DetectorResult(
                    detector_name="change_point",
                    raw_score=score,
                    anomaly_type="REGIME_CHANGE",
                    expected_value=float(mean_before),
                    actual_value=float(mean_after),
                    explanation=f"Sustained regime change detected. Volume shifted from ~{mean_before:.0f}/day to ~{mean_after:.0f}/day.",
                    details={"cp_index": int(latest_cp_idx), "mean_before": float(mean_before), "mean_after": float(mean_after)}
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"Change point detector failed: {e}")
            
        return results
