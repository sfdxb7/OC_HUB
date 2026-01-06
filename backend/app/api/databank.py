"""
Data Bank API endpoints - searchable database of extracted intelligence.
"""
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class DataBankItem(BaseModel):
    """Single item from the data bank."""
    id: UUID
    report_id: UUID
    report_title: str
    report_source: str
    type: str  # 'statistic', 'quote', 'finding', 'aha_moment', 'recommendation'
    content: str
    context: Optional[str]
    source_page: Optional[int]
    tags: list[str]
    
    # Type-specific fields
    speaker: Optional[str]  # For quotes
    value: Optional[str]  # For statistics
    unit: Optional[str]  # For statistics
    
    created_at: str


class PaginatedDataBank(BaseModel):
    """Paginated data bank results."""
    items: list[DataBankItem]
    total: int
    page: int
    limit: int
    has_more: bool


class DataBankStats(BaseModel):
    """Statistics about the data bank."""
    total_items: int
    by_type: dict[str, int]
    by_source: dict[str, int]
    top_tags: list[dict[str, int]]


# === Endpoints ===

@router.get("", response_model=PaginatedDataBank)
async def search_databank(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Full-text search"),
    type: Optional[Literal["statistic", "quote", "finding", "aha_moment", "recommendation"]] = Query(
        None, description="Filter by item type"
    ),
    report_id: Optional[UUID] = Query(None, description="Filter by report"),
    source: Optional[str] = Query(None, description="Filter by report source"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search the data bank for extracted intelligence.
    
    The data bank contains:
    - **Statistics**: Numbers and quantitative claims with context
    - **Quotes**: Memorable phrases suitable for speeches
    - **Findings**: Key insights from reports
    - **Aha Moments**: Contrarian or surprising insights
    - **Recommendations**: Action items from reports
    """
    logger.info(
        "Search databank",
        user_id=current_user["id"],
        search=search,
        type=type,
        source=source
    )
    
    # TODO: Query Supabase data_bank table
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Search databank not yet implemented"
    )


@router.get("/stats", response_model=DataBankStats)
async def get_databank_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about the data bank.
    
    Useful for dashboard widgets.
    """
    logger.info(
        "Get databank stats",
        user_id=current_user["id"]
    )
    
    # TODO: Aggregate stats from Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get databank stats not yet implemented"
    )


@router.get("/statistics", response_model=PaginatedDataBank)
async def get_statistics(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get statistics specifically.
    
    Shortcut for type=statistic filter.
    """
    # Delegate to main search with type filter
    return await search_databank(
        current_user=current_user,
        search=search,
        type="statistic",
        source=source,
        page=page,
        limit=limit
    )


@router.get("/quotes", response_model=PaginatedDataBank)
async def get_quotes(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    speaker: Optional[str] = Query(None, description="Filter by speaker"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get quotes specifically.
    
    Great for finding quotable language for speeches.
    """
    # TODO: Add speaker filter support
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get quotes not yet implemented"
    )


@router.get("/aha-moments", response_model=PaginatedDataBank)
async def get_aha_moments(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get aha moments / contrarian insights.
    
    These are insights that challenge conventional wisdom.
    """
    return await search_databank(
        current_user=current_user,
        search=search,
        type="aha_moment",
        source=source,
        page=page,
        limit=limit
    )


@router.get("/{item_id}", response_model=DataBankItem)
async def get_databank_item(
    item_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific data bank item.
    """
    logger.info(
        "Get databank item",
        user_id=current_user["id"],
        item_id=str(item_id)
    )
    
    # TODO: Query Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get databank item not yet implemented"
    )


@router.get("/tags")
async def get_tags(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tags with counts.
    """
    logger.info(
        "Get tags",
        user_id=current_user["id"]
    )
    
    # TODO: Aggregate tags from Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get tags not yet implemented"
    )
