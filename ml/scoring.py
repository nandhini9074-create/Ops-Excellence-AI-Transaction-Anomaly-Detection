import sys
import os
from typing import List, Dict, Optional

# Ensure backend directory is in sys.path for IDE linter & standalone execution
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings
from ml.zscore import DetectorResult


def calculate_severity(score: float) -> str:
    if score >= 0.85:
        return "CRITICAL"
    elif score >= 0.70:
        return "HIGH"
    elif score >= 0.50:
        return "MEDIUM"
    else:
        return "LOW"

def fuse_scores(detector_results: List[DetectorResult]) -> Optional[Dict]:
    """
    Fuses the scores from multiple detectors into a single anomaly score and confidence.
    """
    if not detector_results:
        return None
        
    weights = {
        "z_score": settings.ZSCORE_WEIGHT,
        "isolation_forest": settings.ISOLATION_FOREST_WEIGHT,
        "prophet": settings.PROPHET_WEIGHT,
        "change_point": settings.CHANGE_POINT_WEIGHT
    }
    
    total_score = 0.0
    weight_sum = 0.0
    details = {}
    
    # Track the highest scoring detector to use its explanation and values
    primary_detector = detector_results[0]
    max_raw_score = primary_detector.raw_score
    
    for res in detector_results:
        w = weights.get(res.detector_name, 0.25)
        total_score += res.raw_score * w
        weight_sum += w
        details[res.detector_name] = res.__dict__
        
        if res.raw_score > max_raw_score:
            max_raw_score = res.raw_score
            primary_detector = res
            
    if weight_sum == 0:
        return None
        
    final_score = total_score / weight_sum
    
    # If multiple detectors triggered, confidence is higher
    confidence = min(1.0, 0.4 + (len(detector_results) * 0.15))
    
    # If 2 or more detectors triggered, label as a multi-signal anomaly
    anomaly_type = primary_detector.anomaly_type
    if len(detector_results) >= 2:
        anomaly_type = "MULTI_SIGNAL_ANOMALY"
        
    return {
        "anomaly_score": final_score,
        "confidence_score": confidence,
        "severity": calculate_severity(final_score),
        "anomaly_type": anomaly_type,
        "expected_value": primary_detector.expected_value,
        "actual_value": primary_detector.actual_value,
        "explanation": primary_detector.explanation,
        "detector_outputs": details
    }
