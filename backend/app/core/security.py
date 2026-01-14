"""
Supabase Auth integration for FastAPI.
Uses Supabase's built-in authentication system.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.supabase import get_supabase, get_supabase_service_client

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from Supabase.
    Validates the JWT token and returns user data.
    """
    token = credentials.credentials
    supabase = get_supabase()
    
    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        
        # Get officer profile
        # Get officer profile using service role client (bypasses RLS)
        # We can trust the user.id because we verified the token above
        supabase_admin = get_supabase_service_client()
        
        profile_result = supabase_admin.table("officer_profiles")\
            .select("*")\
            .eq("id", user.id)\
            .maybe_single()\
            .execute()
        
        if not profile_result or not profile_result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Officer profile not found"
            )
        
        profile = profile_result.data
        
        # Check if account is active
        if not profile.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": profile.get("full_name"),
            "department": profile.get("department"),
            "role": profile.get("role", "OFFICER"),
            "is_active": profile.get("is_active", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires admin role."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
