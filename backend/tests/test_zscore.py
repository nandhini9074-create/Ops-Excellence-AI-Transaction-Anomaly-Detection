import pytest
import pandas as pd
from ml.zscore import ZScoreDetector

def test_zscore_detector_normal():
    baseline = {
        "amount": {"mean_amount": 100.0, "std_amount": 10.0},
        "thresholds": {"z_score_threshold": 3.0}
    }
    detector = ZScoreDetector(baseline)
    
    # Create a dummy dataframe with normal amounts
    df = pd.DataFrame([{"transaction_amount": 110.0}, {"transaction_amount": 90.0}])
    
    results = detector.detect(df)
    assert len(results) == 0 # No anomalies expected

def test_zscore_detector_anomaly():
    baseline = {
        "amount": {"mean_amount": 100.0, "std_amount": 10.0},
        "thresholds": {"z_score_threshold": 3.0}
    }
    detector = ZScoreDetector(baseline)
    
    # 150 is 5 std devs away, which > 3.0 threshold
    df = pd.DataFrame([{"transaction_amount": 150.0}])
    
    results = detector.detect(df)
    assert len(results) == 1
    assert results[0].anomaly_type == "AMOUNT_SPIKE"
    assert results[0].raw_score > 0.5
