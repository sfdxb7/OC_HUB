"""
Library API endpoints - browse, search, and view reports.
"""
import json
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.services.supabase import get_supabase_service
from app.services.ragflow import get_ragflow_client

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class ReportSummary(BaseModel):
    """Report list item."""
    id: str
    title: str
    source: str
    year: Optional[int]
    category: Optional[str]
    page_count: Optional[int]
    has_summary: bool
    created_at: str


class PaginatedReports(BaseModel):
    """Paginated report list."""
    items: list[ReportSummary]
    total: int
    page: int
    limit: int
    has_more: bool


class KeyFinding(BaseModel):
    """Extracted key finding."""
    finding: str
    evidence: Optional[str] = None
    page: Optional[int] = None
    significance: Optional[str] = None


class Statistic(BaseModel):
    """Extracted statistic."""
    stat: str
    context: Optional[str] = None
    source_page: Optional[int] = None
    comparisons: Optional[str] = None


class Quote(BaseModel):
    """Extracted quote."""
    quote: str
    speaker: Optional[str] = None
    context: Optional[str] = None
    page: Optional[int] = None


class AhaMoment(BaseModel):
    """Contrarian/surprising insight."""
    insight: str
    why_contrarian: Optional[str] = None
    implications: Optional[str] = None


class Recommendation(BaseModel):
    """Report recommendation."""
    recommendation: str
    rationale: Optional[str] = None
    page: Optional[int] = None
    priority: Optional[str] = None


class RelatedReport(BaseModel):
    """Related report via GraphRAG."""
    id: str
    title: str
    source: str
    connection_type: str
    shared_entities: list[str] = []


class ReportDetail(BaseModel):
    """Full report with all extracted intelligence."""
    id: str
    title: str
    source: str
    year: Optional[int]
    category: Optional[str]
    page_count: Optional[int]
    original_filename: Optional[str]
    
    executive_summary: Optional[str]
    key_findings: list[KeyFinding] = []
    statistics: list[Statistic] = []
    quotes: list[Quote] = []
    aha_moments: list[AhaMoment] = []
    recommendations: list[Recommendation] = []
    methodology: Optional[str] = None
    limitations: Optional[str] = None
    
    related_reports: list[RelatedReport] = []
    
    created_at: str
    processed_at: Optional[str] = None


class ReportBrief(BaseModel):
    """Condensed 1-page report brief."""
    id: str
    title: str
    source: str
    year: Optional[int]
    executive_summary: str
    top_findings: list[KeyFinding]
    key_statistics: list[Statistic]
    main_recommendation: Optional[Recommendation] = None


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(min_length=1, max_length=1000)
    semantic: bool = Field(default=True)
    limit: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    """Search result item."""
    id: str
    title: str
    source: str
    year: Optional[int]
    excerpt: str
    relevance_score: float
    matched_section: Optional[str] = None


# === Helper Functions ===

def parse_json_field(data: Optional[str], default: list = None) -> list:
    """Parse JSON string field to list."""
    if default is None:
        default = []
    if not data:
        return default
    try:
        if isinstance(data, str):
            return json.loads(data)
        return data
    except:
        return default


# === Endpoints ===

@router.get("", response_model=PaginatedReports)
async def list_reports(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Full-text search"),
    source: Optional[str] = Query(None, description="Filter by source"),
    year: Optional[int] = Query(None, description="Filter by year"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: Literal["created_at", "year", "title"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List all reports with optional filtering and pagination.
    """
    logger.info(
        "List reports",
        user_id=current_user["id"],
        search=search,
        source=source,
        year=year,
        page=page
    )
    
    supabase = get_supabase_service()
    
    try:
        reports, total = await supabase.get_reports(
            search=search,
            source=source,
            year=year,
            category=category,
            page=page,
            limit=limit
        )
        
        items = []
        for r in reports:
            items.append(ReportSummary(
                id=r["id"],
                title=r.get("title", "Untitled"),
                source=r.get("source", "Unknown"),
                year=r.get("year"),
                category=r.get("category"),
                page_count=r.get("page_count"),
                has_summary=bool(r.get("executive_summary")),
                created_at=r.get("created_at", "")
            ))
        
        return PaginatedReports(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(page * limit) < total
        )
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sources")
async def get_sources(
    current_user: dict = Depends(get_current_user)
):
    """Get list of all report sources."""
    supabase = get_supabase_service()
    
    try:
        sources = await supabase.get_report_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(get_current_user)
):
    """Get list of all categories."""
    # For now, return static categories
    return {
        "categories": ["Consulting", "Research", "Policy", "News", "Government"]
    }


@router.get("/years")
async def get_years(
    current_user: dict = Depends(get_current_user)
):
    """Get list of all years with reports."""
    supabase = get_supabase_service()
    
    try:
        years = await supabase.get_report_years()
        return {"years": years}
    except Exception as e:
        logger.error(f"Failed to get years: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full report detail with all extracted intelligence.
    """
    logger.info(
        "Get report",
        user_id=current_user["id"],
        report_id=str(report_id)
    )
    
    supabase = get_supabase_service()
    
    try:
        report = await supabase.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Parse JSON fields
        key_findings = parse_json_field(report.get("key_findings"))
        statistics = parse_json_field(report.get("statistics"))
        quotes = parse_json_field(report.get("quotes"))
        aha_moments = parse_json_field(report.get("aha_moments"))
        recommendations = parse_json_field(report.get("recommendations"))
        
        return ReportDetail(
            id=report["id"],
            title=report.get("title", "Untitled"),
            source=report.get("source", "Unknown"),
            year=report.get("year"),
            category=report.get("category"),
            page_count=report.get("page_count"),
            original_filename=report.get("original_filename"),
            executive_summary=report.get("executive_summary"),
            key_findings=[KeyFinding(**f) if isinstance(f, dict) else KeyFinding(finding=str(f)) for f in key_findings],
            statistics=[Statistic(**s) if isinstance(s, dict) else Statistic(stat=str(s)) for s in statistics],
            quotes=[Quote(**q) if isinstance(q, dict) else Quote(quote=str(q)) for q in quotes],
            aha_moments=[AhaMoment(**a) if isinstance(a, dict) else AhaMoment(insight=str(a)) for a in aha_moments],
            recommendations=[Recommendation(**r) if isinstance(r, dict) else Recommendation(recommendation=str(r)) for r in recommendations],
            methodology=report.get("methodology"),
            limitations=report.get("limitations"),
            related_reports=[],  # TODO: Implement GraphRAG connections
            created_at=report.get("created_at", ""),
            processed_at=report.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{report_id}/brief", response_model=ReportBrief)
async def get_report_brief(
    report_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get condensed 1-page brief of a report.
    """
    logger.info(
        "Get report brief",
        user_id=current_user["id"],
        report_id=str(report_id)
    )
    
    supabase = get_supabase_service()
    
    try:
        report = await supabase.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Parse and limit
        key_findings = parse_json_field(report.get("key_findings"))[:5]
        statistics = parse_json_field(report.get("statistics"))[:5]
        recommendations = parse_json_field(report.get("recommendations"))
        
        main_rec = None
        if recommendations:
            rec = recommendations[0]
            main_rec = Recommendation(**rec) if isinstance(rec, dict) else Recommendation(recommendation=str(rec))
        
        return ReportBrief(
            id=report["id"],
            title=report.get("title", "Untitled"),
            source=report.get("source", "Unknown"),
            year=report.get("year"),
            executive_summary=report.get("executive_summary", "No summary available."),
            top_findings=[KeyFinding(**f) if isinstance(f, dict) else KeyFinding(finding=str(f)) for f in key_findings],
            key_statistics=[Statistic(**s) if isinstance(s, dict) else Statistic(stat=str(s)) for s in statistics],
            main_recommendation=main_rec
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report brief: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{report_id}/pdf")
async def get_report_pdf(
    report_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get original PDF file for a report.
    """
    logger.info(
        "Get report PDF",
        user_id=current_user["id"],
        report_id=str(report_id)
    )
    
    supabase = get_supabase_service()
    
    try:
        report = await supabase.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Return path info - actual file serving would depend on storage setup
        return {
            "report_id": str(report_id),
            "original_filename": report.get("original_filename"),
            "mineru_folder": report.get("mineru_folder"),
            "message": "PDF access not yet implemented - files stored locally"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{report_id}/related", response_model=list[RelatedReport])
async def get_related_reports(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get related reports via GraphRAG entity connections.
    """
    logger.info(
        "Get related reports",
        user_id=current_user["id"],
        report_id=str(report_id)
    )
    
    # TODO: Implement GraphRAG-based related reports
    # For now, return empty list
    return []


@router.post("/search", response_model=list[SearchResult])
async def search_reports(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search across all reports using semantic or keyword search.
    """
    logger.info(
        "Search reports",
        user_id=current_user["id"],
        query=request.query[:50],
        semantic=request.semantic
    )
    
    if request.semantic:
        # Use RAGFlow for semantic search
        ragflow = get_ragflow_client()
        supabase = get_supabase_service()
        
        try:
            # Get dataset ID
            datasets = await ragflow.list_datasets()
            dataset_id = None
            for ds in datasets:
                if ds.get("name") == "DCAI Intelligence Hub":
                    dataset_id = ds["id"]
                    break
            
            if not dataset_id:
                # Fall back to keyword search
                reports, _ = await supabase.get_reports(
                    search=request.query,
                    limit=request.limit
                )
                return [
                    SearchResult(
                        id=r["id"],
                        title=r.get("title", "Untitled"),
                        source=r.get("source", "Unknown"),
                        year=r.get("year"),
                        excerpt=r.get("executive_summary", "")[:200] + "...",
                        relevance_score=0.5,
                        matched_section="title/summary"
                    )
                    for r in reports
                ]
            
            # Semantic search via RAGFlow
            chunks = await ragflow.retrieve(
                dataset_ids=[dataset_id],
                question=request.query,
                top_k=request.limit
            )
            
            # Deduplicate by document
            seen_docs = set()
            results = []
            
            for chunk in chunks:
                doc_id = chunk.get("document_id", "")
                if doc_id in seen_docs:
                    continue
                seen_docs.add(doc_id)
                
                results.append(SearchResult(
                    id=doc_id,
                    title=chunk.get("document_name", "Unknown"),
                    source="Unknown",  # Would need to look up from DB
                    year=None,
                    excerpt=chunk.get("content", "")[:200] + "...",
                    relevance_score=chunk.get("score", chunk.get("similarity", 0.5)),
                    matched_section=f"Page {chunk.get('page', '?')}"
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fall through to keyword search
    
    # Keyword search via Supabase
    supabase = get_supabase_service()
    
    try:
        reports, _ = await supabase.get_reports(
            search=request.query,
            limit=request.limit
        )
        
        return [
            SearchResult(
                id=r["id"],
                title=r.get("title", "Untitled"),
                source=r.get("source", "Unknown"),
                year=r.get("year"),
                excerpt=r.get("executive_summary", "")[:200] + "..." if r.get("executive_summary") else "No summary",
                relevance_score=0.5,
                matched_section="title/summary"
            )
            for r in reports
        ]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
