"""
Admin API endpoints - user management and system administration.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.core.deps import get_admin_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class UserSummary(BaseModel):
    """User list item."""
    id: UUID
    email: str
    is_admin: bool
    last_sign_in: Optional[str]
    created_at: str


class UserDetail(BaseModel):
    """Full user detail."""
    id: UUID
    email: str
    is_admin: bool
    user_metadata: dict
    last_sign_in: Optional[str]
    created_at: str
    updated_at: str


class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    email: EmailStr
    password: str = Field(min_length=8)
    is_admin: bool = False


class UpdateUserRequest(BaseModel):
    """Request to update user."""
    is_admin: Optional[bool] = None
    user_metadata: Optional[dict] = None


class SystemStats(BaseModel):
    """System statistics for admin dashboard."""
    total_reports: int
    total_users: int
    total_conversations: int
    total_messages: int
    total_news_items: int
    total_databank_items: int
    ragflow_status: str
    supabase_status: str
    last_processing_job: Optional[dict]


# === Endpoints ===

@router.get("/users", response_model=list[UserSummary])
async def list_users(
    current_user: dict = Depends(get_admin_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all users (admin only).
    """
    logger.info(
        "List users",
        admin_id=current_user["id"]
    )
    
    # TODO: Query Supabase auth.users
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List users not yet implemented"
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_admin_user)
):
    """
    Get user details (admin only).
    """
    logger.info(
        "Get user",
        admin_id=current_user["id"],
        user_id=str(user_id)
    )
    
    # TODO: Query Supabase for user
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get user not yet implemented"
    )


@router.post("/users", response_model=UserDetail)
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(get_admin_user)
):
    """
    Create a new user (admin only).
    """
    logger.info(
        "Create user",
        admin_id=current_user["id"],
        new_user_email=request.email
    )
    
    # TODO: Create user via Supabase Admin API
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Create user not yet implemented"
    )


@router.patch("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    current_user: dict = Depends(get_admin_user)
):
    """
    Update user (admin only).
    """
    logger.info(
        "Update user",
        admin_id=current_user["id"],
        user_id=str(user_id)
    )
    
    # TODO: Update user via Supabase Admin API
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update user not yet implemented"
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(get_admin_user)
):
    """
    Delete user (admin only).
    
    This will also delete all their conversations and messages.
    """
    logger.info(
        "Delete user",
        admin_id=current_user["id"],
        user_id=str(user_id)
    )
    
    # Prevent self-deletion
    if str(user_id) == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # TODO: Delete user via Supabase Admin API
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete user not yet implemented"
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get system statistics for admin dashboard.
    """
    logger.info(
        "Get system stats",
        admin_id=current_user["id"]
    )
    
    # TODO: Aggregate stats from various sources
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get system stats not yet implemented"
    )


@router.post("/ragflow/test")
async def test_ragflow_connection(
    current_user: dict = Depends(get_admin_user)
):
    """
    Test connection to RAGFlow.
    """
    logger.info(
        "Test RAGFlow connection",
        admin_id=current_user["id"]
    )
    
    # TODO: Ping RAGFlow API
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Test RAGFlow not yet implemented"
    )


@router.post("/supabase/test")
async def test_supabase_connection(
    current_user: dict = Depends(get_admin_user)
):
    """
    Test connection to Supabase.
    """
    logger.info(
        "Test Supabase connection",
        admin_id=current_user["id"]
    )
    
    # TODO: Ping Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Test Supabase not yet implemented"
    )
