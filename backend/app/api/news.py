"""
News API endpoints - article scraping and "So What?" analysis.
"""
import json
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.services.firecrawl import get_firecrawl_service
from app.services.llm import get_llm_service
from app.services.supabase import get_supabase_service
from app.prompts.so_what import SO_WHAT_PROMPT

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class SoWhatAnalysis(BaseModel):
    """Strategic analysis of news article."""
    summary: str = Field(description="2-3 sentence summary of what happened")
    so_what: str = Field(description="Why this matters strategically")
    uae_implications: list[str] = Field(description="Specific impact on UAE AI goals")
    opportunities: list[str] = Field(description="What UAE could do")
    risks: list[str] = Field(description="What to watch out for")
    talking_point: str = Field(description="Quotable response if asked")


class NewsItem(BaseModel):
    """News article with analysis."""
    id: str
    url: str
    title: str
    source: str
    author: Optional[str] = None
    published_at: Optional[str] = None
    content_preview: Optional[str] = None
    analysis: Optional[SoWhatAnalysis] = None
    analyzed_at: Optional[str] = None
    created_at: str


class AnalyzeRequest(BaseModel):
    """Request to analyze a news article."""
    url: HttpUrl = Field(description="URL of article to analyze")


class AnalyzeResponse(BaseModel):
    """Analysis response."""
    news_item: NewsItem
    is_cached: bool = Field(description="Whether analysis was already cached")


class NewsListResponse(BaseModel):
    """List of news items."""
    items: list[NewsItem]
    total: int


# === Endpoints ===

@router.get("", response_model=NewsListResponse)
async def list_news(
    current_user: dict = Depends(get_current_user),
    analyzed_only: bool = Query(True, description="Only show analyzed articles"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List news articles, most recent first.
    """
    logger.info(
        "List news",
        user_id=current_user["id"],
        analyzed_only=analyzed_only,
        limit=limit
    )
    
    try:
        supabase = get_supabase_service()
        items, total = await supabase.get_news_items(
            analyzed_only=analyzed_only,
            source=source,
            limit=limit,
            offset=offset
        )
        
        return NewsListResponse(
            items=[_format_news_item(item) for item in items],
            total=total
        )
    except Exception as e:
        logger.error("Failed to list news", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list news: {str(e)}"
        )


@router.get("/{news_id}", response_model=NewsItem)
async def get_news_item(
    news_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific news item with its analysis.
    """
    logger.info(
        "Get news item",
        user_id=current_user["id"],
        news_id=news_id
    )
    
    try:
        supabase = get_supabase_service()
        item = await supabase.get_news_item(news_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News item not found"
            )
        
        return _format_news_item(item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get news item", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get news item: {str(e)}"
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
    """
    url = str(request.url)
    logger.info(
        "Analyze article",
        user_id=current_user["id"],
        url=url
    )
    
    supabase = get_supabase_service()
    
    # 1. Check cache
    try:
        existing = await supabase.get_news_by_url(url)
        if existing and existing.get("so_what_analysis"):
            logger.info("Returning cached analysis", url=url)
            return AnalyzeResponse(
                news_item=_format_news_item(existing),
                is_cached=True
            )
    except Exception as e:
        logger.warning("Cache check failed, proceeding with scrape", error=str(e))
    
    # 2. Scrape with Firecrawl
    try:
        firecrawl = get_firecrawl_service()
        scraped = await firecrawl.scrape_url(url)
    except Exception as e:
        logger.error("Firecrawl scraping failed", url=url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to scrape article: {str(e)}"
        )
    
    if not scraped.content or scraped.word_count < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract sufficient content from URL"
        )
    
    # 3. Run So What analysis
    try:
        llm = get_llm_service()
        
        # Truncate content if too long
        content = scraped.content[:8000]
        
        system_prompt = SO_WHAT_PROMPT.format(
            title=scraped.title,
            source=scraped.source_domain,
            published_date=scraped.published_date or "Unknown",
            url=url,
            content=content
        )
        
        response = await llm.complete(
            messages=[{"role": "user", "content": f"Analyze this article: {scraped.title}"}],
            model_type="chat",
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        # Parse the response into structured format
        analysis = _parse_analysis(response.content)
        
    except Exception as e:
        logger.error("LLM analysis failed", url=url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze article: {str(e)}"
        )
    
    # 4. Store in database
    try:
        news_item = {
            "id": str(uuid4()),
            "url": url,
            "title": scraped.title,
            "source": scraped.source_domain,
            "author": scraped.author,
            "published_at": scraped.published_date,
            "raw_content": scraped.content[:10000],  # Store truncated
            "so_what_analysis": json.dumps(analysis.model_dump()),
            "analyzed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        saved = await supabase.save_news_item(news_item)
        
        return AnalyzeResponse(
            news_item=_format_news_item(saved),
            is_cached=False
        )
    except Exception as e:
        logger.error("Failed to save news item", url=url, error=str(e))
        # Return analysis even if save fails
        return AnalyzeResponse(
            news_item=NewsItem(
                id=str(uuid4()),
                url=url,
                title=scraped.title,
                source=scraped.source_domain,
                author=scraped.author,
                published_at=scraped.published_date,
                content_preview=scraped.content[:500],
                analysis=analysis,
                analyzed_at=datetime.utcnow().isoformat(),
                created_at=datetime.utcnow().isoformat()
            ),
            is_cached=False
        )


@router.delete("/{news_id}")
async def delete_news_item(
    news_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a news item.
    """
    logger.info(
        "Delete news item",
        user_id=current_user["id"],
        news_id=news_id
    )
    
    try:
        supabase = get_supabase_service()
        await supabase.delete_news_item(news_id)
        return {"status": "deleted", "id": news_id}
    except Exception as e:
        logger.error("Failed to delete news item", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete news item: {str(e)}"
        )


# === Helper Functions ===

def _format_news_item(item: dict) -> NewsItem:
    """Format database record to NewsItem."""
    analysis = None
    if item.get("so_what_analysis"):
        try:
            analysis_data = item["so_what_analysis"]
            if isinstance(analysis_data, str):
                analysis_data = json.loads(analysis_data)
            analysis = SoWhatAnalysis(**analysis_data)
        except Exception as e:
            logger.warning("Failed to parse analysis", error=str(e))
    
    return NewsItem(
        id=str(item["id"]),
        url=item["url"],
        title=item.get("title", "Untitled"),
        source=item.get("source", "Unknown"),
        author=item.get("author"),
        published_at=item.get("published_at"),
        content_preview=item.get("raw_content", "")[:500] if item.get("raw_content") else None,
        analysis=analysis,
        analyzed_at=item.get("analyzed_at"),
        created_at=item.get("created_at", datetime.utcnow().isoformat())
    )


def _parse_analysis(llm_response: str) -> SoWhatAnalysis:
    """Parse LLM response into structured SoWhatAnalysis."""
    # Try to extract sections from markdown response
    lines = llm_response.split("\n")
    
    summary = ""
    so_what = ""
    uae_implications = []
    opportunities = []
    risks = []
    talking_point = ""
    
    current_section = None
    current_content = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect section headers
        if "so what" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "so_what"
            current_content = []
        elif "summary" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "summary"
            current_content = []
        elif "uae" in line_lower and "implication" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "uae_implications"
            current_content = []
        elif "opportunit" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "opportunities"
            current_content = []
        elif "risk" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "risks"
            current_content = []
        elif "talking point" in line_lower and "#" in line:
            if current_section and current_content:
                _assign_section(current_section, current_content, locals())
            current_section = "talking_point"
            current_content = []
        elif line.strip():
            current_content.append(line.strip())
    
    # Handle last section
    if current_section and current_content:
        _assign_section(current_section, current_content, locals())
    
    # Fallback: if parsing failed, use full response
    if not summary and not so_what:
        summary = llm_response[:500]
        so_what = "See analysis above"
    
    return SoWhatAnalysis(
        summary=summary or "Analysis completed",
        so_what=so_what or "Strategic implications identified",
        uae_implications=uae_implications or ["Analysis pending"],
        opportunities=opportunities or ["Opportunities identified"],
        risks=risks or ["Risks identified"],
        talking_point=talking_point or "No specific talking point generated"
    )


def _assign_section(section: str, content: list, context: dict):
    """Helper to assign parsed content to section."""
    text = "\n".join(content)
    
    if section == "summary":
        context["summary"] = text
    elif section == "so_what":
        context["so_what"] = text
    elif section == "uae_implications":
        context["uae_implications"] = [c.lstrip("- ") for c in content if c.strip()]
    elif section == "opportunities":
        context["opportunities"] = [c.lstrip("- ") for c in content if c.strip()]
    elif section == "risks":
        context["risks"] = [c.lstrip("- ") for c in content if c.strip()]
    elif section == "talking_point":
        context["talking_point"] = text
