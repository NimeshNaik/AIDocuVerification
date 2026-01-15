from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    AADHAAR = "aadhaar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    DRIVING_LICENSE = "driving_license"
    PASSPORT = "passport"
    BIRTH_CERTIFICATE = "birth_certificate"
    UNKNOWN = "unknown"


class Recommendation(str, Enum):
    """AI recommendation types."""
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class Decision(str, Enum):
    """Officer decision types."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


class ExtractedField(BaseModel):
    """Single extracted field with confidence."""
    value: str
    confidence: float


class FraudSignal(BaseModel):
    """Fraud detection signal."""
    type: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH


class VerificationResult(BaseModel):
    """Complete verification result from the pipeline."""
    request_id: str
    document_type: DocumentType
    confidence_score: float
    fields: Dict[str, ExtractedField]
    validation_errors: List[str] = []
    fraud_signals: List[FraudSignal] = []
    recommendation: Recommendation
    explanation: str


class DecisionRequest(BaseModel):
    """Officer decision submission."""
    request_id: str
    final_decision: Decision
    override_reason: Optional[str] = None
    corrected_data: Optional[Dict[str, Any]] = None


class DecisionResponse(BaseModel):
    """Response after logging decision."""
    success: bool
    message: str
