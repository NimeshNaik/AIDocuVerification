import uuid
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.schemas.document import VerificationResult, DecisionRequest, DecisionResponse
from app.core.security import get_current_user
from app.db.supabase import get_supabase
from app.services.pipeline import run_verification_pipeline

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.post("/process", response_model=VerificationResult)
async def process_document(
    file: UploadFile = File(...),
    document_type_hint: Optional[str] = None,
    current_officer: dict = Depends(get_current_user)
):
    """
    Upload and process a document through the verification pipeline.
    
    - Accepts image (JPEG, PNG) or PDF files
    - Runs: Classification → Extraction → Validation → Fraud Detection
    - Returns recommendation with confidence scores
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Create initial record in database
    supabase = get_supabase()
    supabase.table("verification_requests").insert({
        "id": request_id,
        "status": "PROCESSING"
    }).execute()
    
    try:
        # Run verification pipeline
        start_time = time.time()
        result = await run_verification_pipeline(
            request_id=request_id,
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            document_type_hint=document_type_hint
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Update database with results
        supabase.table("verification_requests").update({
            "status": "COMPLETED",
            "document_type": result.document_type.value,
            "raw_response": result.model_dump(),
            "fraud_flag": len(result.fraud_signals) > 0
        }).eq("id", request_id).execute()
        
        return result
        
    except Exception as e:
        # Mark as failed
        supabase.table("verification_requests").update({
            "status": "FAILED",
            "raw_response": {"error": str(e)}
        }).eq("id", request_id).execute()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/decision", response_model=DecisionResponse)
async def submit_decision(
    decision: DecisionRequest,
    current_officer: dict = Depends(get_current_user)
):
    """
    Submit officer's final decision on a verification request.
    Logs the decision for audit trail.
    """
    supabase = get_supabase()
    
    # Verify the request exists
    request = supabase.table("verification_requests").select("*").eq("id", decision.request_id).single().execute()
    
    if not request.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification request not found")
    
    # Determine if this was an override
    original_recommendation = request.data.get("raw_response", {}).get("recommendation", "REVIEW")
    was_overridden = original_recommendation != decision.final_decision.value
    
    # Log the decision
    audit_entry = {
        "request_id": decision.request_id,
        "officer_id": current_officer["id"],
        "officer_decision": decision.final_decision.value,
        "was_overridden": was_overridden,
        "override_reason": decision.override_reason if was_overridden else None,
    }
    
    supabase.table("audit_logs").insert(audit_entry).execute()
    
    return DecisionResponse(
        success=True,
        message=f"Decision '{decision.final_decision.value}' recorded successfully"
    )
