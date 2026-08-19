def calculate_dynamic_thresholds(volume_features: dict, amount_features: dict, threshold_multiplier: float = 1.0) -> dict:
    """
    Calculate dynamic Z-score and Isolation Forest thresholds based on the outlet's volatility.
    High volatility outlets get wider thresholds, adjusted by merchant whitelist feedback multipliers.
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
        
    # Apply merchant feedback threshold multiplier (e.g. 1.5x for noisy false-positive merchants)
    final_z_threshold = z_score_threshold * threshold_multiplier

    return {
        "z_score_threshold": final_z_threshold,
        "cv_amount": cv,
        "threshold_multiplier": threshold_multiplier
    }

