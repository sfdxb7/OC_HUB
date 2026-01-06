"""
DCAI Intelligence Platform - FastAPI Application Entry Point
Updated: 2025-01-04 - Added test endpoints for meeting-prep, talking-points, news-analyze, databank
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import DCIAException
from app.api.router import api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(
        "Starting DCAI Intelligence Platform",
        version="1.0.0",
        debug=settings.debug
    )
    
    # Verify critical services
    # TODO: Add RAGFlow health check
    # TODO: Add Supabase health check
    
    yield
    
    # Shutdown
    logger.info("Shutting down DCAI Intelligence Platform")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered executive intelligence platform for UAE Minister of AI",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(DCIAException)
async def dcia_exception_handler(request: Request, exc: DCIAException):
    """Handle custom DCAI exceptions."""
    logger.error(
        "Application error",
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected error",
        error=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred" if not settings.debug else str(exc)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "dcai-backend"
    }


# Test RAGFlow retrieval endpoint (no auth - for development only)
@app.get("/test/ragflow")
async def test_ragflow(query: str = "What are the key AI governance recommendations?"):
    """Test RAGFlow retrieval without authentication."""
    from app.services.ragflow import get_ragflow_client
    from app.core.config import settings
    
    ragflow = get_ragflow_client()
    
    try:
        # Use configured dataset ID
        dataset_id = settings.ragflow_dataset_id
        
        chunks = await ragflow.retrieve(
            dataset_ids=[dataset_id],
            question=query,
            top_k=3
        )
        
        return {
            "query": query,
            "dataset_id": dataset_id,
            "results_count": len(chunks),
            "results": [
                {
                    "document": c.get("document_keyword", c.get("document_name", "Unknown")),
                    "excerpt": c.get("content", "")[:300] + "...",
                    "score": c.get("similarity", c.get("score", 0))
                }
                for c in chunks
            ]
        }
    except Exception as e:
        return {"error": str(e)}


# Test Supabase connection (no auth - for development only)
@app.get("/test/supabase")
async def test_supabase():
    """Test Supabase connection."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        stats = await supabase.get_stats()
        return {
            "status": "connected",
            "url": supabase.url,
            "stats": stats
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Test LLM connection (no auth - for development only)
@app.get("/test/llm")
async def test_llm(prompt: str = "Say hello in one sentence."):
    """Test LLM connection via OpenRouter."""
    from app.services.llm import get_llm_service
    
    try:
        llm = get_llm_service()
        response = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            model_type="chat",
            max_tokens=100
        )
        return {
            "status": "connected",
            "model": response.model,
            "response": response.content,
            "tokens": response.tokens_prompt + response.tokens_completion
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Test full chat flow (no auth - for development only)
from pydantic import BaseModel
from typing import Optional

class TestChatRequest(BaseModel):
    message: str = "What are the key AI governance recommendations?"
    mode: str = "all"
    document_id: Optional[str] = None

@app.post("/test/chat")
async def test_chat(request: TestChatRequest):
    """Test full RAG chat without authentication."""
    from app.services.ragflow import get_ragflow_client
    from app.services.llm import get_llm_service
    from app.core.config import settings
    from app.prompts.chat import CHAT_SYSTEM_PROMPTS
    
    ragflow = get_ragflow_client()
    llm = get_llm_service()
    
    message = request.message
    mode = request.mode
    document_id = request.document_id
    
    try:
        # 1. Retrieve context from RAGFlow
        chunks = await ragflow.retrieve(
            dataset_ids=[settings.ragflow_dataset_id],
            question=message,
            top_k=10 if document_id else 5,  # Get more chunks if filtering
            document_ids=[document_id] if document_id else None
        )
        
        # 2. Format context
        context_parts = []
        citations = []
        for i, chunk in enumerate(chunks[:5], 1):
            doc_name = chunk.get("document_keyword", chunk.get("document_name", "Unknown"))
            content = chunk.get("content", "")
            score = chunk.get("similarity", 0)
            
            context_parts.append(f"[{i}] {doc_name} (relevance: {score:.2f})\n{content[:500]}")
            citations.append({
                "source": doc_name,
                "excerpt": content[:200] + "...",
                "score": score
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 3. Build prompt - use single mode prompt if document specified
        effective_mode = "single" if document_id else mode
        system_prompt = CHAT_SYSTEM_PROMPTS.get(effective_mode, CHAT_SYSTEM_PROMPTS["all"]).format(
            retrieved_context=context,
            question=message
        )
        
        # 4. Generate response
        response = await llm.complete(
            messages=[{"role": "user", "content": message}],
            model_type="chat",
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        return {
            "query": message,
            "mode": effective_mode,
            "document_id": document_id,
            "response": response.content,
            "model": response.model,
            "citations": citations,
            "tokens_used": response.tokens_prompt + response.tokens_completion
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# Test reports endpoint (no auth - for development only)
@app.get("/test/reports")
async def test_reports(
    search: str | None = None,
    source: str | None = None,
    year: int | None = None,
    page: int = 1,
    limit: int = 20
):
    """List reports without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        reports, total = await supabase.get_reports(
            search=search,
            source=source,
            year=year,
            page=page,
            limit=limit
        )
        
        return {
            "items": [
                {
                    "id": r["id"],
                    "title": r.get("title", "Untitled"),
                    "source": r.get("source", "Unknown"),
                    "year": r.get("year"),
                    "category": r.get("category"),
                    "page_count": r.get("page_count"),
                    "has_summary": bool(r.get("executive_summary")),
                    "created_at": r.get("created_at", "")
                }
                for r in reports
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (page * limit) < total
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/test/reports/{report_id}")
async def test_report_detail(report_id: str):
    """Get single report without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    from uuid import UUID
    import json
    
    def parse_json_field(data, default=None):
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
    
    try:
        supabase = get_supabase_service()
        report = await supabase.get_report(UUID(report_id))
        
        if not report:
            return {"error": "Report not found"}
        
        return {
            "id": report["id"],
            "title": report.get("title", "Untitled"),
            "source": report.get("source", "Unknown"),
            "year": report.get("year"),
            "category": report.get("category"),
            "page_count": report.get("page_count"),
            "original_filename": report.get("original_filename"),
            "executive_summary": report.get("executive_summary"),
            "key_findings": parse_json_field(report.get("key_findings")),
            "statistics": parse_json_field(report.get("statistics")),
            "quotes": parse_json_field(report.get("quotes")),
            "aha_moments": parse_json_field(report.get("aha_moments")),
            "recommendations": parse_json_field(report.get("recommendations")),
            "methodology": report.get("methodology"),
            "limitations": report.get("limitations"),
            "created_at": report.get("created_at", ""),
            "processed_at": report.get("updated_at")
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/test/sources")
async def test_sources():
    """Get report sources without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        sources = await supabase.get_report_sources()
        return {"sources": sources}
    except Exception as e:
        return {"error": str(e)}


@app.get("/test/years")
async def test_years():
    """Get report years without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        years = await supabase.get_report_years()
        return {"years": years}
    except Exception as e:
        return {"error": str(e)}


# Test conversations endpoint (no auth - for development)
@app.get("/test/conversations")
async def test_conversations(user_id: str = "c496f932-a855-4690-825c-a9f52637f6df"):
    """List conversations without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    from uuid import UUID
    
    try:
        supabase = get_supabase_service()
        conversations = await supabase.get_conversations(
            user_id=UUID(user_id),
            limit=50
        )
        
        result = []
        for conv in conversations:
            messages = await supabase.get_messages(UUID(conv["id"]))
            result.append({
                "id": conv["id"],
                "mode": conv["mode"],
                "title": conv.get("title"),
                "report_id": conv.get("report_id"),
                "message_count": len(messages),
                "created_at": conv["created_at"],
                "updated_at": conv.get("updated_at", conv["created_at"])
            })
        
        return {"conversations": result}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/test/conversations/{conversation_id}")
async def test_conversation_detail(conversation_id: str):
    """Get conversation detail without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    from uuid import UUID
    import json
    
    try:
        supabase = get_supabase_service()
        conv = await supabase.get_conversation(UUID(conversation_id))
        
        if not conv:
            return {"error": "Conversation not found"}
        
        messages = []
        for msg in conv.get("messages", []):
            citations = []
            if msg.get("citations"):
                try:
                    cit_data = json.loads(msg["citations"]) if isinstance(msg["citations"], str) else msg["citations"]
                    citations = cit_data
                except:
                    pass
            
            messages.append({
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "citations": citations,
                "model_used": msg.get("model_used"),
                "created_at": msg["created_at"]
            })
        
        return {
            "id": conv["id"],
            "mode": conv["mode"],
            "title": conv.get("title"),
            "report_id": conv.get("report_id"),
            "messages": messages,
            "created_at": conv["created_at"]
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.delete("/test/conversations/{conversation_id}")
async def test_delete_conversation(
    conversation_id: str, 
    user_id: str = "c496f932-a855-4690-825c-a9f52637f6df"
):
    """Delete conversation without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    from uuid import UUID
    
    try:
        supabase = get_supabase_service()
        await supabase.delete_conversation(UUID(conversation_id), UUID(user_id))
        return {"status": "deleted", "id": conversation_id}
    except Exception as e:
        return {"error": str(e)}


# Test Meeting Prep generation (no auth - for development)
class MeetingPrepRequest(BaseModel):
    title: str
    participants: str
    purpose: str
    angle: str = "balanced"

@app.post("/test/meeting-prep")
async def test_meeting_prep(request: MeetingPrepRequest):
    """Generate meeting prep briefing without authentication (for development)."""
    from app.services.ragflow import get_ragflow_client
    from app.services.llm import get_llm_service
    from app.core.config import settings
    
    ragflow = get_ragflow_client()
    llm = get_llm_service()
    
    try:
        # Retrieve relevant context based on meeting topic
        chunks = await ragflow.retrieve(
            dataset_ids=[settings.ragflow_dataset_id],
            question=f"{request.title} {request.purpose}",
            top_k=8
        )
        
        # Format context
        context_parts = []
        sources = []
        for chunk in chunks[:8]:
            doc_name = chunk.get("document_keyword", chunk.get("document_name", "Unknown"))
            content = chunk.get("content", "")
            context_parts.append(f"From {doc_name}:\n{content[:600]}")
            if doc_name not in sources:
                sources.append(doc_name)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generate briefing
        system_prompt = f"""You are a strategic advisor preparing a 2-minute briefing for the UAE Minister of AI.

MEETING DETAILS:
- Topic: {request.title}
- Participants: {request.participants}
- Purpose: {request.purpose}
- Requested Angle: {request.angle}

RELEVANT INTELLIGENCE FROM REPORTS:
{context}

Generate a concise executive briefing with:
1. CONTEXT (2-3 sentences on why this matters now)
2. KEY TALKING POINTS (3-5 bullet points with statistics where available)
3. POTENTIAL QUESTIONS (2-3 questions you might be asked and suggested responses)
4. STRATEGIC RECOMMENDATION (1 key takeaway)

Keep it actionable and cite specific sources where possible."""

        response = await llm.complete(
            messages=[{"role": "user", "content": f"Generate briefing for: {request.title}"}],
            model_type="chat",
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        return {
            "briefing": response.content,
            "sources": sources[:5],
            "model": response.model,
            "tokens_used": response.tokens_prompt + response.tokens_completion
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# Test Talking Points generation (no auth - for development)
class TalkingPointsRequest(BaseModel):
    topic: str
    audience: str
    tone: str = "professional"
    num_points: int = 5

@app.post("/test/talking-points")
async def test_talking_points(request: TalkingPointsRequest):
    """Generate talking points without authentication (for development)."""
    from app.services.ragflow import get_ragflow_client
    from app.services.llm import get_llm_service
    from app.core.config import settings
    
    ragflow = get_ragflow_client()
    llm = get_llm_service()
    
    try:
        # Retrieve relevant context
        chunks = await ragflow.retrieve(
            dataset_ids=[settings.ragflow_dataset_id],
            question=request.topic,
            top_k=10
        )
        
        context_parts = []
        sources = []
        for chunk in chunks[:10]:
            doc_name = chunk.get("document_keyword", chunk.get("document_name", "Unknown"))
            content = chunk.get("content", "")
            context_parts.append(f"From {doc_name}:\n{content[:500]}")
            if doc_name not in sources:
                sources.append(doc_name)
        
        context = "\n\n".join(context_parts)
        
        system_prompt = f"""You are preparing talking points for the UAE Minister of AI.

TOPIC: {request.topic}
AUDIENCE: {request.audience}
TONE: {request.tone}
NUMBER OF POINTS: {request.num_points}

RELEVANT DATA FROM STRATEGIC REPORTS:
{context}

Generate exactly {request.num_points} talking points. Each point should:
1. Make a clear, memorable claim
2. Include a supporting statistic or evidence (cite the source)
3. Be appropriate for the specified audience and tone

Format as:
## Talking Point 1: [Title]
**Main Point:** [Clear statement]
**Evidence:** [Statistic or fact with source]
**Why It Matters:** [One sentence on significance]

Repeat for all {request.num_points} points."""

        response = await llm.complete(
            messages=[{"role": "user", "content": f"Generate talking points about: {request.topic}"}],
            model_type="chat",
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        return {
            "talking_points": response.content,
            "sources": sources[:5],
            "model": response.model
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# Test News Analysis (no auth - for development)
class NewsAnalysisRequest(BaseModel):
    url: str
    title: str | None = None
    content: str | None = None

@app.post("/test/news-analyze")
async def test_news_analyze(request: NewsAnalysisRequest):
    """Analyze news article with 'So What?' framework (for development)."""
    from app.services.llm import get_llm_service
    
    llm = get_llm_service()
    
    # For now, require content to be provided (Firecrawl integration TBD)
    if not request.content:
        return {
            "error": "Content scraping not yet implemented. Please provide article content.",
            "note": "Firecrawl integration coming soon"
        }
    
    try:
        system_prompt = f"""You are a strategic analyst for the UAE Minister of AI.

Analyze this news article through the lens of UAE AI leadership priorities:
- Sovereign AI development
- Regional AI leadership
- Talent attraction
- Regulatory positioning
- Economic diversification

ARTICLE:
{request.content[:3000]}

Provide analysis in this exact format:

## SO WHAT?
Why this news matters for AI leadership (2-3 sentences)

## UAE IMPLICATIONS
- [Specific impact 1]
- [Specific impact 2]
- [Specific impact 3]

## OPPORTUNITIES
What actions UAE could take based on this development

## RISKS
Potential challenges or threats to monitor

## MINISTERIAL TALKING POINT
One quotable response the Minister could give if asked about this"""

        response = await llm.complete(
            messages=[{"role": "user", "content": f"Analyze: {request.title or request.url}"}],
            model_type="chat",
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        return {
            "url": request.url,
            "title": request.title,
            "analysis": response.content,
            "model": response.model
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# Test Batch Processing (no auth - for development)
class BatchProcessRequest(BaseModel):
    path: str | None = None
    max_concurrent: int = 3
    force_reprocess: bool = False
    limit: int | None = None

@app.post("/test/process-batch")
async def test_process_batch(request: BatchProcessRequest):
    """
    Trigger batch processing of MinerU reports from local folder.
    
    Default path: C:\\myprojects\\REVIEW\\NewHUB\\processed_reports_mineru
    """
    from app.services.processing import get_processing_service
    from pathlib import Path
    import asyncio
    
    # Default path to MinerU reports
    base_path = request.path or r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru"
    
    try:
        processor = get_processing_service()
        base = Path(base_path)
        
        if not base.exists():
            return {"error": f"Path does not exist: {base_path}"}
        
        # Get all folders
        folders = [f for f in base.iterdir() if f.is_dir()]
        total = len(folders)
        
        # Apply limit if specified
        if request.limit:
            folders = folders[:request.limit]
        
        results = {
            "total_found": total,
            "processing": len(folders),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def process_one(folder: Path):
            async with semaphore:
                try:
                    result = await processor.process_mineru_folder(
                        str(folder),
                        force_reprocess=request.force_reprocess
                    )
                    if result["status"] == "already_exists":
                        results["skipped"] += 1
                    else:
                        results["processed"] += 1
                    results["details"].append({
                        "folder": folder.name,
                        "status": result["status"],
                        "title": result.get("title", "")[:100]
                    })
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "folder": folder.name,
                        "status": "failed",
                        "error": str(e)[:200]
                    })
        
        # Run all processing tasks
        await asyncio.gather(*[process_one(f) for f in folders])
        
        return results
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/test/process-status")
async def test_process_status():
    """Check processing status - count of reports with/without extraction."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        reports, total = await supabase.get_reports(limit=1000)
        
        with_summary = sum(1 for r in reports if r.get("executive_summary"))
        with_source = sum(1 for r in reports if r.get("source") and r.get("source") != "Unknown")
        with_findings = sum(1 for r in reports if r.get("key_findings"))
        
        return {
            "total_reports": total,
            "with_summary": with_summary,
            "with_source": with_source,
            "with_findings": with_findings,
            "missing_extraction": total - with_summary
        }
    except Exception as e:
        return {"error": str(e)}


# Test Data Bank endpoints (no auth - for development)
@app.get("/test/databank")
async def test_databank(
    type: str | None = None,
    search: str | None = None,
    limit: int = 50
):
    """Get data bank items without authentication (for development)."""
    from app.services.supabase import get_supabase_service
    
    try:
        supabase = get_supabase_service()
        items, total = await supabase.get_databank_items(
            item_type=type,
            search=search,
            limit=limit
        )
        
        return {
            "items": items,
            "total": total
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# Include API router
app.include_router(api_router, prefix="/api")


# Root redirect
@app.get("/")
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "DCAI Intelligence Platform API",
        "docs": "/docs" if settings.debug else "Docs disabled in production",
        "health": "/health"
    }
