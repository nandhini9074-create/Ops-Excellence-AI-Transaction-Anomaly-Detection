from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class DetectorResult:
    detector_name: str
    raw_score: float          # 0.0–1.0 (normalized)
    anomaly_type: str
    expected_value: float
    actual_value: float
    explanation: str
    details: dict

class ZScoreDetector:
    def __init__(self, baseline_profile: dict):
        self.baseline = baseline_profile
        self.threshold = self.baseline.get("thresholds", {}).get("z_score_threshold", 3.0)

    def detect(self, df_recent: Any) -> List[DetectorResult]:
        """
        df_recent is a pandas DataFrame of the last 4-5 hours of transactions.
        """
        results = []
        if df_recent.empty:
            return results
            
        mean_amt = self.baseline.get("amount", {}).get("mean_amount", 0.0)
        std_amt = self.baseline.get("amount", {}).get("std_amount", 0.1)
        if std_amt == 0:
            std_amt = 0.1 # Prevent division by zero
            
        # Vectorized Z-Score calculation for high performance on daily batches
        df_calc = df_recent.copy()
        df_calc['transaction_amount'] = df_calc['transaction_amount'].astype(float)
        df_calc['z_score'] = (df_calc['transaction_amount'] - mean_amt) / std_amt
        
        # [ANOMALY DECISION]: Filter rows where Z-score deviation exceeds baseline threshold
        anomalies = df_calc[df_calc['z_score'].abs() >= self.threshold]
        
        for _, row in anomalies.iterrows():
            amt = float(row['transaction_amount'])
            z = float(row['z_score'])
            
            # Incorporate Card Scheme Settlement Delay Buffers (Visa: 0.5h, Mastercard: 1.0h)
            scheme = str(row.get('card_scheme', '')).upper()
            scheme_delay_buffer = 1.0 if 'MASTERCARD' in scheme else 0.5
            
            # Calculate a normalized score 0-1 based on how far past the threshold it is
            excess = abs(z) - self.threshold
            raw_score = min(1.0, 0.5 + (excess / self.threshold) * 0.5)
            
            anomaly_type = "AMOUNT_SPIKE" if z > 0 else "AMOUNT_DROP"
            
            res = DetectorResult(
                detector_name="z_score",
                raw_score=raw_score,
                anomaly_type=anomaly_type,
                expected_value=mean_amt,
                actual_value=amt,
                explanation=f"Transaction amount {amt} ({scheme or 'VISA'}) is {abs(z):.2f} std dev from mean {mean_amt:.2f} (Scheme Delay Buffer: {scheme_delay_buffer}h).",
                details={"z_score": float(z), "threshold": float(self.threshold), "scheme_delay_buffer_hours": scheme_delay_buffer, "card_scheme": scheme}
            )
            results.append(res)
                
        return results
