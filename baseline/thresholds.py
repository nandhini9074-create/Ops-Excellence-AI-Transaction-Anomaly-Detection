def calculate_dynamic_thresholds(volume_features: dict, amount_features: dict) -> dict:
    """
    Calculate dynamic Z-score and Isolation Forest thresholds based on the outlet's volatility.
    High volatility outlets get wider thresholds.
    """
    if not amount_features or not volume_features:
        return {}
        
    mean_amt = amount_features.get("mean_amount", 1)
    std_amt = amount_features.get("std_amount", 0)
    
    # Coefficient of variation
    cv = std_amt / mean_amt if mean_amt > 0 else 0
    
    # Base thresholds
    z_score_threshold = 3.0
    if cv > 1.0:
        # High volatility -> relax Z-score
        z_score_threshold = 4.0
    elif cv < 0.2:
        # Low volatility -> tighten Z-score
        z_score_threshold = 2.5
        
    return {
        "z_score_threshold": z_score_threshold,
        "cv_amount": cv
    }
