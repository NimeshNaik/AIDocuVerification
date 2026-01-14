from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import (
    SignUpRequest, 
    SignInRequest, 
    AuthResponse, 
    OfficerProfile,
    ProfileUpdateRequest
)
from app.core.security import get_current_user, require_admin
from app.db.supabase import get_supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    """
    Register a new officer account using Supabase Auth.
    """
    supabase = get_supabase()
    
    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name,
                    "department": request.department or "",
                    "role": "OFFICER"
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create account"
            )
        
        user = auth_response.user
        session = auth_response.session
        
        if not session:
            # Email confirmation might be required
            return AuthResponse(
                access_token="",
                user=OfficerProfile(
                    id=user.id,
                    email=user.email,
                    full_name=request.full_name,
                    department=request.department,
                    role="OFFICER",
                    is_active=True
                )
            )
        
        return AuthResponse(
            access_token=session.access_token,
            user=OfficerProfile(
                id=user.id,
                email=user.email,
                full_name=request.full_name,
                department=request.department,
                role="OFFICER",
                is_active=True
            )
        )
        
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """
    Sign in with email and password using Supabase Auth.
    """
    supabase = get_supabase()
    
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = auth_response.user
        session = auth_response.session
        
        # Get officer profile
        profile_result = supabase.table("officer_profiles")\
            .select("*")\
            .eq("id", user.id)\
            .maybe_single()\
            .execute()
        
        profile = (profile_result and profile_result.data) or {}
        
        return AuthResponse(
            access_token=session.access_token,
            user=OfficerProfile(
                id=user.id,
                email=user.email,
                full_name=profile.get("full_name", ""),
                department=profile.get("department"),
                role=profile.get("role", "OFFICER"),
                is_active=profile.get("is_active", True)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/signout")
async def signout(current_user: dict = Depends(get_current_user)):
    """
    Sign out current user.
    """
    supabase = get_supabase()
    
    try:
        supabase.auth.sign_out()
        return {"message": "Signed out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signout failed: {str(e)}"
        )


@router.get("/me", response_model=OfficerProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated officer profile.
    """
    return OfficerProfile(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        department=current_user.get("department"),
        role=current_user["role"],
        is_active=current_user["is_active"]
    )


@router.patch("/me", response_model=OfficerProfile)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current officer's profile.
    """
    supabase = get_supabase()
    
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.department is not None:
        update_data["department"] = request.department
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    result = supabase.table("officer_profiles")\
        .update(update_data)\
        .eq("id", current_user["id"])\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    updated = result.data[0]
    
    return OfficerProfile(
        id=current_user["id"],
        email=current_user["email"],
        full_name=updated.get("full_name", current_user["full_name"]),
        department=updated.get("department"),
        role=updated.get("role", "OFFICER"),
        is_active=updated.get("is_active", True)
    )
