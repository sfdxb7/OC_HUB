"""
Dependency injection for FastAPI routes.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

from .config import settings

# Security scheme
security = HTTPBearer()


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> dict:
    """
    Validate JWT token and return current user.
    
    Raises:
        HTTPException: If token is invalid or expired.
    """
    token = credentials.credentials
    
    try:
        # Verify the JWT with Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "role": user_response.user.role,
            "user_metadata": user_response.user.user_metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Ensure current user is an admin.
    
    Raises:
        HTTPException: If user is not an admin.
    """
    # Check if user is admin by email (simple approach)
    # In production, use roles in user_metadata
    if current_user.get("email") != settings.admin_email:
        # Also check user metadata for admin role
        metadata = current_user.get("user_metadata", {})
        if not metadata.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    try:
        user_response = supabase.auth.get_user(credentials.credentials)
        if user_response and user_response.user:
            return {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "role": user_response.user.role,
                "user_metadata": user_response.user.user_metadata
            }
    except Exception:
        pass
    
    return None
