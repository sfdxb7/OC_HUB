"""
News API endpoints - article scraping and "So What?" analysis.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from app.core.deps import get_current_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class SoWhatAnalysis(BaseModel):
    """Strategic analysis of news article."""
    summary: str = Field(description="2-3 sentence summary of what happened")
    so_what: str = Field(description="Why this matters strategically")
    uae_implications: str = Field(description="Specific impact on UAE AI goals")
    opportunities: list[str] = Field(description="What UAE could do")
    risks: list[str] = Field(description="What to watch out for")
    talking_point: str = Field(description="Quotable response if asked")


class NewsItem(BaseModel):
    """News article with analysis."""
    id: UUID
    url: str
    title: str
    source: str
    author: Optional[str]
    published_at: Optional[str]
    analysis: Optional[SoWhatAnalysis]
    analyzed_at: Optional[str]
    created_at: str


class AnalyzeRequest(BaseModel):
    """Request to analyze a news article."""
    url: HttpUrl = Field(description="URL of article to analyze")


class AnalyzeResponse(BaseModel):
    """Analysis response."""
    news_item: NewsItem
    is_cached: bool = Field(description="Whether analysis was already cached")


# === Endpoints ===

@router.get("", response_model=list[NewsItem])
async def list_news(
    current_user: dict = Depends(get_current_user),
    analyzed_only: bool = Query(True, description="Only show analyzed articles"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List news articles, most recent first.
    
    By default, only shows articles that have been analyzed.
    """
    logger.info(
        "List news",
        user_id=current_user["id"],
        analyzed_only=analyzed_only,
        limit=limit
    )
    
    # TODO: Query Supabase for news items
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List news not yet implemented"
    )


@router.get("/{news_id}", response_model=NewsItem)
async def get_news_item(
    news_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific news item with its analysis.
    """
    logger.info(
        "Get news item",
        user_id=current_user["id"],
        news_id=str(news_id)
    )
    
    # TODO: Query Supabase for news item
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get news item not yet implemented"
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a news article with "So What?" framework.
    
    Pipeline:
    1. Check if URL already analyzed (return cached)
    2. Scrape article content via Firecrawl
    3. Run "So What?" analysis prompt
    4. Store and return analysis
    
    Analysis includes:
    - **Summary**: What happened (2-3 sentences)
    - **So What?**: Why this matters strategically
    - **UAE Implications**: Impact on UAE AI goals
    - **Opportunities**: What UAE could do
    - **Risks**: What to watch out for
    - **Talking Point**: Quotable ministerial response
    """
    logger.info(
        "Analyze article",
        user_id=current_user["id"],
        url=str(request.url)
    )
    
    # TODO: Implement analysis pipeline
    # 1. Check cache in Supabase
    # 2. Scrape with Firecrawl
    # 3. Run So What prompt
    # 4. Store in Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analyze article not yet implemented"
    )


@router.post("/refresh")
async def refresh_news_feeds(
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger refresh of news feeds.
    
    Fetches latest from configured RSS/news sources and analyzes new articles.
    """
    logger.info(
        "Refresh news feeds",
        user_id=current_user["id"]
    )
    
    # TODO: Fetch from configured news sources
    # TODO: Analyze new articles
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh news not yet implemented"
    )


@router.delete("/{news_id}")
async def delete_news_item(
    news_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a news item.
    """
    logger.info(
        "Delete news item",
        user_id=current_user["id"],
        news_id=str(news_id)
    )
    
    # TODO: Delete from Supabase
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete news item not yet implemented"
    )
