"""
remarks_builder.py
Translates raw ML anomaly output into plain-English remarks for Ops operators.
"""
from typing import Dict, Optional


def build_human_remarks(anomaly_result: Dict) -> Optional[str]:
    """
    Takes the fused anomaly result dict from the ML engine and returns
    a plain-English string suitable for display to a non-technical operator.
    """
    anomaly_type = anomaly_result.get("anomaly_type", "").upper()
    actual = anomaly_result.get("actual_value")
    expected = anomaly_result.get("expected_value")
    confidence = anomaly_result.get("confidence_score", 0.0)
    confidence_pct = int(confidence * 100)

    # Format numbers cleanly
    def fmt(v):
        if v is None:
            return "N/A"
        try:
            return f"{float(v):,.2f}"
        except (TypeError, ValueError):
            return str(v)

    if "VOLUME_DROP" in anomaly_type or ("VOLUME" in anomaly_type and actual is not None and expected is not None and float(actual) < float(expected)):
        return (
            f"Transaction count dropped to {fmt(actual)} vs the expected {fmt(expected)} for this time period. "
            f"Terminal may be offline or experiencing issues. Confidence: {confidence_pct}%."
        )

    if "VOLUME_SPIKE" in anomaly_type:
        return (
            f"Unusually high transaction frequency detected ({fmt(actual)} vs expected {fmt(expected)}). "
            f"Possible duplicate transactions or system replay. Confidence: {confidence_pct}%."
        )

    if "AMOUNT_DROP" in anomaly_type:
        return (
            f"Average transaction value dropped to {fmt(actual)} vs the expected {fmt(expected)}. "
            f"Could indicate a pricing misconfiguration or terminal issue. Confidence: {confidence_pct}%."
        )

    if "AMOUNT_SPIKE" in anomaly_type:
        return (
            f"Unusually high transaction amount detected ({fmt(actual)} vs expected {fmt(expected)}). "
            f"Could indicate fraud, data entry error, or a misconfigured terminal. Confidence: {confidence_pct}%."
        )

    if "MULTI_SIGNAL_ANOMALY" in anomaly_type:
        return (
            f"Multiple simultaneous anomalies detected — both transaction volume and amount are outside "
            f"normal bounds. This is a high-priority signal requiring immediate investigation. Confidence: {confidence_pct}%."
        )

    if "REGIME_CHANGE" in anomaly_type or "PATTERN_BREAK" in anomaly_type:
        return (
            f"A sudden structural change was detected in this outlet's transaction behaviour. "
            f"The normal operating pattern has shifted significantly. Confidence: {confidence_pct}%."
        )

    # Generic fallback — still human readable
    return (
        f"An anomaly was detected ({anomaly_type.replace('_', ' ').title()}). "
        f"Observed value: {fmt(actual)}, Expected: {fmt(expected)}. Confidence: {confidence_pct}%."
    )
