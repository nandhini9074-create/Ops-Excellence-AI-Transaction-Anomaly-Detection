import sys
import os
from typing import List, Dict, Optional

# Ensure backend directory is in sys.path for IDE linter & standalone execution
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings
from ml.zscore import DetectorResult


def calculate_severity(score: float, anomaly_type: str = "") -> str:
    # Business Rules (Sprint 81)
    type_upper = anomaly_type.upper()
    if "VOLUME" in type_upper or "FREQUENCY" in type_upper:
        # Escalate to CRITICAL if anomaly score is extreme (complete collapse)
        return "CRITICAL" if score >= 0.85 else "HIGH"
    elif "DORMANCY" in type_upper:
        return "MEDIUM"
    elif "AMOUNT" in type_upper or "VALUE" in type_upper:
        return "LOW"
        
    # Math fallback
    if score >= 0.85:
        return "CRITICAL"
    elif score >= 0.70:
        return "HIGH"
    elif score >= 0.50:
        return "MEDIUM"
    else:
        return "LOW"

def get_family(anomaly_type: str) -> str:
    type_upper = anomaly_type.upper()
    if "AMOUNT" in type_upper or "VALUE" in type_upper:
        return "AMOUNT"
    if "VOLUME" in type_upper or "FREQUENCY" in type_upper:
        return "VOLUME"
    return "OTHER"

def fuse_scores(detector_results: List[DetectorResult]) -> List[Dict]:
    """
    Groups detector results by anomaly family (Volume, Amount, Other)
    and fuses scores within each family to return separate alerts.
    """
    if not detector_results:
        return []
        
    from collections import defaultdict
    groups = defaultdict(list)
    for res in detector_results:
        groups[get_family(res.anomaly_type)].append(res)
        
    fused_results = []
    
    weights = {
        "z_score": settings.ZSCORE_WEIGHT,
        "isolation_forest": settings.ISOLATION_FOREST_WEIGHT,
        "prophet": settings.PROPHET_WEIGHT,
        "change_point": settings.CHANGE_POINT_WEIGHT
    }
    
    for family, group_results in groups.items():
        total_score = 0.0
        weight_sum = 0.0
        details = {}
        
        primary_detector = group_results[0]
        max_raw_score = primary_detector.raw_score
        
        for res in group_results:
            w = weights.get(res.detector_name, 0.25)
            total_score += res.raw_score * w
            weight_sum += w
            details[res.detector_name] = res.__dict__
            
            if res.raw_score > max_raw_score:
                max_raw_score = res.raw_score
                primary_detector = res
                
        if weight_sum == 0:
            continue
            
        final_score = total_score / weight_sum
        
        # If multiple detectors triggered for this family, confidence is higher
        confidence = min(1.0, 0.4 + (len(group_results) * 0.15))
        anomaly_type = primary_detector.anomaly_type
            
        fused_results.append({
            "anomaly_score": final_score,
            "confidence_score": confidence,
            "severity": calculate_severity(final_score, anomaly_type),
            "anomaly_type": anomaly_type,
            "expected_value": primary_detector.expected_value,
            "actual_value": primary_detector.actual_value,
            "explanation": primary_detector.explanation,
            "detector_outputs": details
        })
        
    return fused_results
