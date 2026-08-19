import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Any
import numpy as np

from app.config import settings
from ml.zscore import DetectorResult

class IsolationForestDetector:
    def __init__(self, baseline_profile: dict):
        self.baseline = baseline_profile
        self.contamination = settings.ISOLATION_FOREST_CONTAMINATION

    def detect(self, df_recent: Any) -> List[DetectorResult]:
        """
        Runs unsupervised anomaly detection on the recent batch of transactions
        looking for pattern breaks in multidimensional space.
        """
        results = []
        if df_recent.empty or len(df_recent) < 5: # Need a minimum number of samples to find patterns
            return results
            
        # Extract features for model (cast to float to avoid decimal/float TypeError)
        features = df_recent[['transaction_amount']].copy().astype(float)
        
        # Add time features
        df_recent['datetime'] = pd.to_datetime(df_recent['transaction_timestamp'])
        features['hour'] = df_recent['datetime'].dt.hour
        features['dayofweek'] = df_recent['datetime'].dt.dayofweek
        
        # [BASELINE COMPARISON]: Calculates transaction amount deviation relative to baseline mean
        mean_amt = self.baseline.get("amount", {}).get("mean_amount", 0)
        features['amount_deviation'] = features['transaction_amount'] - mean_amt
        
        # Fit Isolation Forest
        clf = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Predict: -1 is anomaly, 1 is normal
        preds = clf.fit_predict(features)
        
        # Scores: The lower, the more abnormal. We want 0-1 where 1 is highest anomaly.
        # decision_function returns negative values for anomalies.
        scores = clf.decision_function(features)
        
        for idx, (pred, score) in enumerate(zip(preds, scores)):
            # [ANOMALY DECISION]: Checks if Isolation Forest predicted an abnormal isolation path (pred == -1)
            if pred == -1:
                # Normalize score to 0-1. Score is typically between -0.5 and 0.5.
                # If score is < 0, it's an anomaly. The more negative, the more severe.
                raw_score = min(1.0, max(0.5, abs(score) * 2 + 0.5))
                
                row = df_recent.iloc[idx]
                amt = float(row['transaction_amount'])
                
                res = DetectorResult(
                    detector_name="isolation_forest",
                    raw_score=float(raw_score),
                    anomaly_type="PATTERN_BREAK",
                    expected_value=mean_amt,
                    actual_value=amt,
                    explanation=f"Unusual transaction pattern detected. Amount: {amt}, Hour: {int(row['datetime'].hour)}.",
                    details={"if_score": float(score)}
                )
                results.append(res)
                
        return results
