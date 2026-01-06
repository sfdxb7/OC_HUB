"""
Chat API endpoints - supports 3 modes: single document, all documents, digital minister.
"""
import json
from typing import Optional, Literal, AsyncIterator
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.core.config import settings
from app.services.ragflow import get_ragflow_client
from app.services.llm import get_llm_service
from app.services.supabase import get_supabase_service
from app.prompts.chat import CHAT_SYSTEM_PROMPTS, ENHANCE_QUERY_PROMPT

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class ChatRequest(BaseModel):
    """Chat request payload."""
    mode: Literal["single", "all", "minister"] = Field(
        description="Chat mode: single document, all documents, or digital minister"
    )
    message: str = Field(min_length=1, max_length=10000)
    document_id: Optional[UUID] = Field(
        default=None,
        description="Required for 'single' mode"
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Continue existing conversation"
    )
    stream: bool = Field(
        default=True,
        description="Stream response tokens"
    )
    enable_web_search: bool = Field(
        default=False,
        description="Enable web search (minister mode only)"
    )


class Citation(BaseModel):
    """Citation reference."""
    report_id: str
    report_title: str
    source: str
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    """Chat response payload."""
    response: str
    citations: list[Citation] = []
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None
    agent_contributions: Optional[list[dict]] = None  # For minister mode


class EnhanceRequest(BaseModel):
    """Query enhancement request."""
    query: str = Field(min_length=1, max_length=5000)
    context: Optional[str] = None


class EnhanceResponse(BaseModel):
    """Enhanced query response."""
    original: str
    enhanced: str
    improvements: list[str]


class ConversationSummary(BaseModel):
    """Conversation list item."""
    id: str
    mode: str
    title: Optional[str]
    report_id: Optional[str]
    report_title: Optional[str]
    message_count: int
    created_at: str
    updated_at: str


class Message(BaseModel):
    """Chat message."""
    id: str
    role: str
    content: str
    citations: list[Citation] = []
    model_used: Optional[str]
    created_at: str


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: str
    mode: str
    title: Optional[str]
    report_id: Optional[str]
    report_title: Optional[str]
    messages: list[Message]
    created_at: str


# === Helper Functions ===

async def get_dataset_id() -> Optional[str]:
    """Get the main dataset ID from RAGFlow."""
    try:
        ragflow = get_ragflow_client()
        datasets = await ragflow.list_datasets()
        for ds in datasets:
            if ds.get("name") == "DCAI Intelligence Hub":
                return ds["id"]
        return None
    except Exception as e:
        logger.error(f"Failed to get dataset ID: {e}")
        return None


async def retrieve_context(
    query: str,
    dataset_id: str,
    document_ids: Optional[list[str]] = None,
    top_k: int = 10
) -> tuple[str, list[dict]]:
    """
    Retrieve relevant context from RAGFlow.
    
    Returns:
        Tuple of (formatted context string, raw chunks with metadata)
    """
    ragflow = get_ragflow_client()
    
    try:
        chunks = await ragflow.retrieve(
            dataset_ids=[dataset_id],
            question=query,
            top_k=top_k,
            document_ids=document_ids
        )
        
        if not chunks:
            return "No relevant context found.", []
        
        # Format context for prompt
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("document_name", "Unknown")
            content = chunk.get("content", chunk.get("text", ""))
            page = chunk.get("page", chunk.get("page_num", "?"))
            score = chunk.get("score", chunk.get("similarity", 0))
            
            context_parts.append(
                f"[{i}] {doc_name} (p.{page}, relevance: {score:.2f})\n{content}"
            )
        
        context_str = "\n\n---\n\n".join(context_parts)
        return context_str, chunks
        
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return f"Error retrieving context: {e}", []


def format_citations(chunks: list[dict]) -> list[Citation]:
    """Format RAGFlow chunks into citation objects."""
    citations = []
    seen = set()
    
    for chunk in chunks:
        doc_id = chunk.get("document_id", "")
        if doc_id in seen:
            continue
        seen.add(doc_id)
        
        citations.append(Citation(
            report_id=doc_id,
            report_title=chunk.get("document_name", "Unknown"),
            source=chunk.get("source", "Unknown"),
            page=chunk.get("page", chunk.get("page_num", 0)) or 0,
            excerpt=chunk.get("content", "")[:200] + "..."
        ))
    
    return citations[:5]  # Limit to top 5 unique sources


# === Endpoints ===

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Main chat endpoint supporting 3 modes:
    
    - **single**: Chat with one specific document (requires document_id)
    - **all**: Chat across all 405 documents
    - **minister**: Digital Minister deep reasoning with multi-agent system
    
    Responses include citations with page numbers for verification.
    """
    user_id = current_user["id"]
    logger.info(
        "Chat request",
        user_id=user_id,
        mode=request.mode,
        document_id=str(request.document_id) if request.document_id else None
    )
    
    # Validate mode-specific requirements
    if request.mode == "single" and not request.document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is required for 'single' mode"
        )
    
    supabase = get_supabase_service()
    llm = get_llm_service()
    
    # Get or create conversation
    if request.conversation_id:
        conversation = await supabase.get_conversation(
            request.conversation_id,
            UUID(user_id)
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        conversation_id = str(request.conversation_id)
    else:
        # Create new conversation
        conv = await supabase.create_conversation(
            user_id=UUID(user_id),
            mode=request.mode,
            report_id=request.document_id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        conversation_id = conv["id"]
    
    # Save user message
    await supabase.add_message(
        conversation_id=UUID(conversation_id),
        role="user",
        content=request.message
    )
    
    # Get dataset ID
    dataset_id = await get_dataset_id()
    if not dataset_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge base not available. Please contact administrator."
        )
    
    # Retrieve context based on mode
    document_filter = None
    if request.mode == "single" and request.document_id:
        # Get the ragflow doc ID for this report
        report = await supabase.get_report(request.document_id)
        if report and report.get("ragflow_doc_id"):
            document_filter = [report["ragflow_doc_id"]]
    
    context, chunks = await retrieve_context(
        query=request.message,
        dataset_id=dataset_id,
        document_ids=document_filter,
        top_k=10 if request.mode == "all" else 5
    )
    
    # Build prompt based on mode
    if request.mode == "single":
        report = await supabase.get_report(request.document_id) if request.document_id else None
        system_prompt = CHAT_SYSTEM_PROMPTS["single"].format(
            report_title=report.get("title", "Unknown") if report else "Unknown",
            report_source=report.get("source", "Unknown") if report else "Unknown",
            report_year=report.get("year", "Unknown") if report else "Unknown",
            retrieved_context=context,
            question=request.message
        )
    elif request.mode == "all":
        system_prompt = CHAT_SYSTEM_PROMPTS["all"].format(
            retrieved_context=context,
            question=request.message
        )
    else:  # minister mode
        system_prompt = CHAT_SYSTEM_PROMPTS["minister"].format(
            context=context,
            question=request.message
        )
    
    # Generate response
    model_type = "reasoning" if request.mode == "minister" else "chat"
    
    try:
        response = await llm.complete(
            messages=[{"role": "user", "content": request.message}],
            model_type=model_type,
            system_prompt=system_prompt,
            temperature=0.7 if request.mode == "minister" else 0.3
        )
        
        # Format citations
        citations = format_citations(chunks)
        
        # Save assistant response
        await supabase.add_message(
            conversation_id=UUID(conversation_id),
            role="assistant",
            content=response.content,
            citations=[c.model_dump() for c in citations],
            model_used=response.model
        )
        
        return ChatResponse(
            response=response.content,
            citations=citations,
            conversation_id=conversation_id,
            model_used=response.model,
            tokens_used=response.tokens_prompt + response.tokens_completion
        )
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Streaming chat endpoint for real-time response tokens.
    Returns Server-Sent Events (SSE) stream.
    """
    user_id = current_user["id"]
    logger.info(
        "Stream chat request",
        user_id=user_id,
        mode=request.mode
    )
    
    # Validate
    if request.mode == "single" and not request.document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is required for 'single' mode"
        )
    
    supabase = get_supabase_service()
    llm = get_llm_service()
    
    # Get or create conversation
    if request.conversation_id:
        conversation_id = str(request.conversation_id)
    else:
        conv = await supabase.create_conversation(
            user_id=UUID(user_id),
            mode=request.mode,
            report_id=request.document_id,
            title=request.message[:50]
        )
        conversation_id = conv["id"]
    
    # Save user message
    await supabase.add_message(
        conversation_id=UUID(conversation_id),
        role="user",
        content=request.message
    )
    
    # Get context
    dataset_id = await get_dataset_id()
    if not dataset_id:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Knowledge base not available'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    document_filter = None
    if request.mode == "single" and request.document_id:
        report = await supabase.get_report(request.document_id)
        if report and report.get("ragflow_doc_id"):
            document_filter = [report["ragflow_doc_id"]]
    
    context, chunks = await retrieve_context(
        query=request.message,
        dataset_id=dataset_id,
        document_ids=document_filter
    )
    
    # Build prompt
    if request.mode == "single":
        report = await supabase.get_report(request.document_id) if request.document_id else None
        system_prompt = CHAT_SYSTEM_PROMPTS["single"].format(
            report_title=report.get("title", "Unknown") if report else "Unknown",
            report_source=report.get("source", "Unknown") if report else "Unknown",
            report_year=report.get("year", "Unknown") if report else "Unknown",
            retrieved_context=context,
            question=request.message
        )
    elif request.mode == "all":
        system_prompt = CHAT_SYSTEM_PROMPTS["all"].format(
            retrieved_context=context,
            question=request.message
        )
    else:
        system_prompt = CHAT_SYSTEM_PROMPTS["minister"].format(
            context=context,
            question=request.message
        )
    
    model_type = "reasoning" if request.mode == "minister" else "chat"
    citations = format_citations(chunks)
    
    async def generate():
        full_response = ""
        try:
            async for token in llm.stream(
                messages=[{"role": "user", "content": request.message}],
                model_type=model_type,
                system_prompt=system_prompt
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            # Send citations at end
            yield f"data: {json.dumps({'citations': [c.model_dump() for c in citations]})}\n\n"
            yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"
            yield "data: [DONE]\n\n"
            
            # Save response
            await supabase.add_message(
                conversation_id=UUID(conversation_id),
                role="assistant",
                content=full_response,
                citations=[c.model_dump() for c in citations],
                model_used=llm.get_model(model_type)
            )
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_query(
    request: EnhanceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Enhance user query for better RAG results.
    
    Returns the original query, enhanced version, and list of improvements made.
    User can accept, modify, or revert to original.
    """
    logger.info(
        "Enhance query request",
        user_id=current_user["id"],
        query_length=len(request.query)
    )
    
    llm = get_llm_service()
    
    try:
        prompt = ENHANCE_QUERY_PROMPT.format(
            query=request.query,
            context=request.context or "None provided"
        )
        
        response = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            model_type="fast",
            temperature=0.3,
            json_mode=True
        )
        
        # Parse response
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        result = json.loads(text)
        
        return EnhanceResponse(
            original=request.query,
            enhanced=result.get("enhanced", request.query),
            improvements=result.get("improvements", [])
        )
        
    except Exception as e:
        logger.error(f"Query enhancement failed: {e}")
        return EnhanceResponse(
            original=request.query,
            enhanced=request.query,
            improvements=["Enhancement failed, using original query"]
        )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    List user's conversations, most recent first.
    """
    logger.info(
        "List conversations",
        user_id=current_user["id"],
        limit=limit,
        offset=offset
    )
    
    supabase = get_supabase_service()
    
    try:
        conversations = await supabase.get_conversations(
            user_id=UUID(current_user["id"]),
            limit=limit,
            offset=offset
        )
        
        result = []
        for conv in conversations:
            # Count messages
            messages = await supabase.get_messages(UUID(conv["id"]))
            
            result.append(ConversationSummary(
                id=conv["id"],
                mode=conv["mode"],
                title=conv.get("title"),
                report_id=conv.get("report_id"),
                report_title=conv.get("reports", {}).get("title") if conv.get("reports") else None,
                message_count=len(messages),
                created_at=conv["created_at"],
                updated_at=conv.get("updated_at", conv["created_at"])
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full conversation with all messages.
    """
    logger.info(
        "Get conversation",
        user_id=current_user["id"],
        conversation_id=str(conversation_id)
    )
    
    supabase = get_supabase_service()
    
    try:
        conv = await supabase.get_conversation(
            conversation_id,
            UUID(current_user["id"])
        )
        
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Format messages
        messages = []
        for msg in conv.get("messages", []):
            citations = []
            if msg.get("citations"):
                try:
                    cit_data = json.loads(msg["citations"]) if isinstance(msg["citations"], str) else msg["citations"]
                    citations = [Citation(**c) for c in cit_data]
                except:
                    pass
            
            messages.append(Message(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                citations=citations,
                model_used=msg.get("model_used"),
                created_at=msg["created_at"]
            ))
        
        return ConversationDetail(
            id=conv["id"],
            mode=conv["mode"],
            title=conv.get("title"),
            report_id=conv.get("report_id"),
            report_title=conv.get("reports", {}).get("title") if conv.get("reports") else None,
            messages=messages,
            created_at=conv["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a conversation and all its messages.
    """
    logger.info(
        "Delete conversation",
        user_id=current_user["id"],
        conversation_id=str(conversation_id)
    )
    
    supabase = get_supabase_service()
    
    try:
        success = await supabase.delete_conversation(
            conversation_id,
            UUID(current_user["id"])
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"status": "deleted", "id": str(conversation_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
