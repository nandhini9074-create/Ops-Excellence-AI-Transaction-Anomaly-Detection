import pandas as pd
from typing import List, Dict, Optional
import logging

from ml.zscore import ZScoreDetector
from ml.isolation_forest import IsolationForestDetector
from ml.prophet_model import ProphetDetector
from ml.change_point import ChangePointDetector
from ml.scoring import fuse_scores

logger = logging.getLogger(__name__)

class AnomalyDetectionEngine:
    def __init__(self, baseline_profile: dict, historical_df: pd.DataFrame = None):
        self.baseline = baseline_profile
        
        # Initialize detectors
        self.z_score = ZScoreDetector(baseline_profile)
        self.iso_forest = IsolationForestDetector(baseline_profile)
        self.prophet = ProphetDetector(baseline_profile, historical_df)
        self.change_point = ChangePointDetector(baseline_profile, historical_df)
        
    def analyze(self, recent_transactions_df: pd.DataFrame) -> List[Dict]:
        """
        Runs all detectors and fuses their results by family.
        Returns a list of dictionaries representing the anomalies (if any).
        """
        if recent_transactions_df.empty:
            return []
            
        logger.info(f"Running AnomalyDetectionEngine on {len(recent_transactions_df)} recent transaction records...")
        all_results = []
        
        # 1. Z-Score
        try:
            z_res = self.z_score.detect(recent_transactions_df)
            all_results.extend(z_res)
        except Exception as e:
            logger.error(f"Z-Score detection failed: {e}")
            
        # 2. Isolation Forest
        try:
            if_res = self.iso_forest.detect(recent_transactions_df)
            all_results.extend(if_res)
        except Exception as e:
            logger.error(f"Isolation Forest detection failed: {e}")
            
        # 3. Prophet
        try:
            p_res = self.prophet.detect(recent_transactions_df)
            all_results.extend(p_res)
        except Exception as e:
            logger.error(f"Prophet detection failed: {e}")
            
        # 4. Change Point
        try:
            cp_res = self.change_point.detect(recent_transactions_df)
            all_results.extend(cp_res)
        except Exception as e:
            logger.error(f"Change Point detection failed: {e}")
            
        # If no anomalies detected
        if not all_results:
            logger.info("No anomaly signals triggered across the 4 ML detectors (Normal Execution).")
            return []
            
        # Fuse scores (now returns a list)
        final_anomalies = fuse_scores(all_results)
        
        for anomaly in final_anomalies:
            logger.info(f"Anomaly detected! Fused Score: {anomaly.get('anomaly_score', 0):.2f}, Severity: {anomaly.get('severity')}, Type: {anomaly.get('anomaly_type')}")
        
        return final_anomalies
