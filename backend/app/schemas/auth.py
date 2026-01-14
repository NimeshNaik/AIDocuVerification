from typing import Optional
from pydantic import BaseModel, EmailStr


class OfficerProfile(BaseModel):
    """Officer profile schema."""
    id: str
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    role: str = "OFFICER"
    is_active: bool = True


class SignUpRequest(BaseModel):
    """Schema for officer signup."""
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None


class SignInRequest(BaseModel):
    """Schema for officer signin."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for auth response."""
    access_token: str
    token_type: str = "bearer"
    user: OfficerProfile


class ProfileUpdateRequest(BaseModel):
    """Schema for updating officer profile."""
    full_name: Optional[str] = None
    department: Optional[str] = None
