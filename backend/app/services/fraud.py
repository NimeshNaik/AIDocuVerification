"""
Basic fraud detection signals.
Conservative approach - flag for review rather than reject.
"""
from typing import List, Dict, Any

from app.schemas.document import FraudSignal


def check_low_confidence(extraction_result: Dict[str, Any]) -> List[FraudSignal]:
    """Flag fields with suspiciously low confidence."""
    signals = []
    
    overall_confidence = extraction_result.get("confidence", 0)
    if overall_confidence < 0.5:
        signals.append(FraudSignal(
            type="LOW_CONFIDENCE",
            description=f"Overall extraction confidence is very low ({overall_confidence:.2f})",
            severity="MEDIUM"
        ))
    
    fields = extraction_result.get("fields", {})
    for field_name, field_data in fields.items():
        if isinstance(field_data, dict):
            confidence = field_data.get("confidence", 0)
            if confidence < 0.3:
                signals.append(FraudSignal(
                    type="LOW_FIELD_CONFIDENCE",
                    description=f"Field '{field_name}' has very low confidence ({confidence:.2f})",
                    severity="LOW"
                ))
    
    return signals


def check_field_consistency(extraction_result: Dict[str, Any]) -> List[FraudSignal]:
    """Check for inconsistencies between fields."""
    signals = []
    fields = extraction_result.get("fields", {})
    
    # Example: Check if name appears in multiple scripts (could indicate manipulation)
    name = fields.get("name", {}).get("value", "")
    
    # Check for mixed scripts that might indicate tampering
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in name)
    has_latin = any('a' <= c.lower() <= 'z' for c in name)
    
    # Having both is normal for some documents, but flag for review
    if has_devanagari and has_latin and len(name) > 20:
        signals.append(FraudSignal(
            type="MIXED_SCRIPTS",
            description="Name field contains mixed scripts - verify authenticity",
            severity="LOW"
        ))
    
    return signals


def check_issues_from_vlm(extraction_result: Dict[str, Any]) -> List[FraudSignal]:
    """Convert VLM-reported issues to fraud signals."""
    signals = []
    
    issues = extraction_result.get("issues", [])
    for issue in issues:
        if isinstance(issue, str):
            severity = "MEDIUM"
            if "tamper" in issue.lower() or "edit" in issue.lower():
                severity = "HIGH"
            elif "blur" in issue.lower() or "quality" in issue.lower():
                severity = "LOW"
            
            signals.append(FraudSignal(
                type="VLM_DETECTED_ISSUE",
                description=issue,
                severity=severity
            ))
    
    return signals


def check_llm_fraud_analysis(extraction_result: Dict[str, Any]) -> List[FraudSignal]:
    """
    Parse advanced fraud analysis from the VLM JSON response.
    """
    signals = []
    
    fraud_data = extraction_result.get("fraud_analysis", {})
    if not fraud_data:
        return signals
    
    # 1. Check validity score (if provided)
    validity_score = float(fraud_data.get("validity_score", 1.0))
    if validity_score < 0.6:
        reasoning = fraud_data.get("reasoning", "Low validity score detected")
        signals.append(FraudSignal(
            type="LOW_VALIDITY_SCORE",
            description=f"AI Validity Check Failed ({validity_score:.2f}): {reasoning}",
            severity="HIGH" if validity_score < 0.4 else "MEDIUM"
        ))
    
    # 2. Check "is_genuine_appearance"
    is_genuine = fraud_data.get("is_genuine_appearance", True)
    if not is_genuine:
         signals.append(FraudSignal(
            type="VISUAL_ANOMALY",
            description="Document does not appear genuine (visual check failed)",
            severity="HIGH"
        ))
    
    # 3. Add suspicious elements
    suspicious_elements = fraud_data.get("suspicious_elements", [])
    for element in suspicious_elements:
        signals.append(FraudSignal(
            type="SUSPICIOUS_ELEMENT",
            description=f"Suspicious: {element}",
            severity="MEDIUM"
        ))
    
    # 4. Add detected alterations
    alterations = fraud_data.get("alterations_detected", [])
    for alteration in alterations:
         signals.append(FraudSignal(
            type="ALTERATION_DETECTED",
            description=f"Tampering detected: {alteration}",
            severity="HIGH"
        ))
        
    return signals


def detect_fraud_signals(extraction_result: Dict[str, Any]) -> List[FraudSignal]:
    """
    Run all fraud detection checks.
    
    Args:
        extraction_result: Output from VLM extraction
    
    Returns:
        List of fraud signals, empty if none detected
    """
    signals = []
    
    # Legacy/Basic checks
    signals.extend(check_low_confidence(extraction_result))
    signals.extend(check_field_consistency(extraction_result))
    signals.extend(check_issues_from_vlm(extraction_result))
    
    # New Advanced LLM Checks
    signals.extend(check_llm_fraud_analysis(extraction_result))
    
    return signals
