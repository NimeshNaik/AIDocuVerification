from typing import Optional, List
from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.db.supabase import get_supabase
from pydantic import BaseModel
from datetime import datetime


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: str
    request_id: str
    officer_id: str
    officer_decision: str
    was_overridden: bool
    override_reason: Optional[str]
    created_at: str
    document_type: Optional[str] = None


class AuditLogsResponse(BaseModel):
    """Paginated audit logs response."""
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated audit logs with verification details.
    """
    supabase = get_supabase()
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Fetch logs with join to verification_requests
    result = supabase.table("audit_logs")\
        .select("*, verification_requests(document_type)")\
        .order("created_at", desc=True)\
        .range(offset, offset + page_size - 1)\
        .execute()
    
    # Get total count
    count_result = supabase.table("audit_logs").select("id", count="exact").execute()
    total = count_result.count if count_result.count else 0
    
    # Transform results
    logs = []
    for entry in result.data:
        doc_type = None
        if entry.get("verification_requests"):
            doc_type = entry["verification_requests"].get("document_type")
        
        logs.append(AuditLogEntry(
            id=entry["id"],
            request_id=entry["request_id"],
            officer_id=entry["officer_id"],
            officer_decision=entry["officer_decision"],
            was_overridden=entry["was_overridden"],
            override_reason=entry.get("override_reason"),
            created_at=entry["created_at"],
            document_type=doc_type
        ))
    
    return AuditLogsResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size
    )
