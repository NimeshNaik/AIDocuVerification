"""
Main verification pipeline orchestrator.
Coordinates: Classification → Extraction → Validation → Fraud Detection
"""
from typing import Optional, Dict, Any

from app.schemas.document import (
    DocumentType, 
    Recommendation, 
    VerificationResult, 
    ExtractedField,
    FraudSignal
)
from app.services.extractor import extract_fields
from app.services.validator import validate_fields
from app.services.fraud import detect_fraud_signals


def determine_recommendation(
    validation_errors: list,
    fraud_signals: list,
    overall_confidence: float,
    is_readable: bool
) -> tuple[Recommendation, str]:
    """
    Determine final recommendation based on all signals.
    Conservative approach: when in doubt, recommend REVIEW.
    """
    if not is_readable:
        return Recommendation.REVIEW, "Document is not readable or too low quality"
    
    # High severity fraud signals -> REVIEW
    high_severity_frauds = [s for s in fraud_signals if s.severity == "HIGH"]
    if high_severity_frauds:
        return Recommendation.REVIEW, f"Potential fraud detected: {high_severity_frauds[0].description}"
    
    # Many validation errors -> REVIEW
    if len(validation_errors) >= 3:
        return Recommendation.REVIEW, f"Multiple validation issues found ({len(validation_errors)} errors)"
    
    # Low confidence -> REVIEW
    if overall_confidence < 0.6:
        return Recommendation.REVIEW, f"Low extraction confidence ({overall_confidence:.2f})"
    
    # Some issues but manageable -> APPROVE with notes
    if validation_errors or fraud_signals:
        if overall_confidence >= 0.8:
            return Recommendation.APPROVE, "Minor issues detected but confidence is high"
        else:
            return Recommendation.REVIEW, "Some issues require manual verification"
    
    # All clear
    if overall_confidence >= 0.85:
        return Recommendation.APPROVE, "All checks passed with high confidence"
    else:
        return Recommendation.APPROVE, "Verification complete with acceptable confidence"


async def run_verification_pipeline(
    request_id: str,
    file_content: bytes,
    file_name: str,
    content_type: str,
    document_type_hint: Optional[str] = None
) -> VerificationResult:
    """
    Run the complete document verification pipeline.
    
    Args:
        request_id: Unique request identifier
        file_content: Raw file bytes
        file_name: Original filename
        content_type: MIME type
        document_type_hint: Optional manual document type override
    
    Returns:
        Complete verification result with recommendation
    """
    # Step 1: Extract fields using VLM
    extraction_result = await extract_fields(file_content, content_type)
    
    # Determine document type
    if document_type_hint:
        doc_type = DocumentType(document_type_hint.lower())
    else:
        doc_type_str = extraction_result.get("document_type", "unknown").lower()
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            doc_type = DocumentType.UNKNOWN
    
    overall_confidence = extraction_result.get("confidence", 0.5)
    is_readable = extraction_result.get("is_readable", True)
    
    # Convert extracted fields to schema format
    raw_fields = extraction_result.get("fields", {})
    fields: Dict[str, ExtractedField] = {}
    for field_name, field_data in raw_fields.items():
        if isinstance(field_data, dict):
            fields[field_name] = ExtractedField(
                value=str(field_data.get("value", "")),
                confidence=float(field_data.get("confidence", 0.5))
            )
        else:
            fields[field_name] = ExtractedField(value=str(field_data), confidence=0.5)
    
    # Step 2: Run validation
    validation_errors = validate_fields(doc_type, raw_fields)
    
    # Step 3: Detect fraud signals
    fraud_signals = detect_fraud_signals(extraction_result)
    
    # Step 4: Determine recommendation
    recommendation, explanation = determine_recommendation(
        validation_errors,
        fraud_signals,
        overall_confidence,
        is_readable
    )
    
    return VerificationResult(
        request_id=request_id,
        document_type=doc_type,
        confidence_score=overall_confidence,
        fields=fields,
        validation_errors=validation_errors,
        fraud_signals=fraud_signals,
        recommendation=recommendation,
        explanation=explanation
    )
