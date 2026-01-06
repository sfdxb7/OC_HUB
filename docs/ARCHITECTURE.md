# Technical Architecture Document
# DCAI Intelligence Platform

**Version:** 1.0  
**Date:** 2026-01-03  
**Author:** AI Engineering Team

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    CLIENTS                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │   Web Browser   │  │   Mobile Web    │  │   API Client    │                     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                     │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────────────┘
            │                     │                     │
            └──────────────────┬──┴─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Nginx (SSL/LB)    │
                    │ myintel.alfalasi.io │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│    Frontend       │ │    Backend      │ │    RAGFlow      │
│    (Next.js)      │ │    (FastAPI)    │ │    (UI)         │
│    Port 3000      │ │    Port 8000    │ │    Port 9380    │
└─────────┬─────────┘ └────────┬────────┘ └────────┬────────┘
          │                    │                    │
          │           ┌────────┴────────┐           │
          │           │                 │           │
          │    ┌──────▼──────┐  ┌───────▼───────┐   │
          │    │  Supabase   │  │   RAGFlow     │   │
          │    │  (VPS)      │  │   Services    │   │
          │    │             │  │               │   │
          │    │ - Auth      │  │ - Vectors     │   │
          │    │ - Postgres  │  │ - GraphRAG    │   │
          │    │ - REST API  │  │ - Retrieval   │   │
          │    └─────────────┘  └───────┬───────┘   │
          │                             │           │
          │                    ┌────────┴────────┐  │
          │                    │  Elasticsearch  │  │
          │                    │  MySQL, MinIO   │  │
          │                    │  Redis          │  │
          │                    └─────────────────┘  │
          │                                         │
          └────────────────────┬────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    OpenRouter       │
                    │    (LLM Gateway)    │
                    │                     │
                    │ - Claude Sonnet 4   │
                    │ - Gemini 2.5 Pro    │
                    │ - Grok 3 Fast       │
                    └─────────────────────┘
```

### 1.2 Component Summary

| Component | Technology | Purpose | Location |
|-----------|------------|---------|----------|
| Frontend | Next.js 14 + shadcn/ui | User interface | Dokploy |
| Backend | FastAPI (Python 3.11+) | API layer | Dokploy |
| Database | Supabase PostgreSQL | Auth, metadata, history | Existing VPS |
| Vector Store | RAGFlow (Elasticsearch) | Document vectors | Dokploy |
| Knowledge Graph | RAGFlow LightRAG | Entity relationships | Dokploy |
| LLM Gateway | OpenRouter | Multi-model access | External |
| News Scraping | Firecrawl | Article extraction | External |
| Web Search | Tavily | Real-time search | External |

---

## 2. Backend Architecture

### 2.1 Directory Structure

```
backend/
├── Dockerfile
├── Dockerfile.dev
├── requirements.txt
├── pytest.ini
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   │
│   ├── core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Settings from environment
│   │   ├── auth.py                # Supabase auth integration
│   │   ├── deps.py                # Dependency injection
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Logging configuration
│   │
│   ├── api/                       # Route handlers
│   │   ├── __init__.py
│   │   ├── router.py              # Main router aggregation
│   │   ├── chat.py                # Chat endpoints (3 modes)
│   │   ├── library.py             # Reports CRUD, search
│   │   ├── processing.py          # Upload, extraction pipeline
│   │   ├── news.py                # Firecrawl + So What analysis
│   │   ├── agents.py              # Digital Minister endpoints
│   │   ├── databank.py            # Statistics, quotes API
│   │   └── admin.py               # Admin operations
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── ragflow.py             # RAGFlow API client
│   │   ├── llm.py                 # OpenRouter multi-model client
│   │   ├── extraction.py          # Intelligence extraction service
│   │   ├── deep_agents.py         # LangGraph multi-agent system
│   │   ├── news_analyzer.py       # News processing service
│   │   ├── supabase.py            # Supabase client wrapper
│   │   └── processing.py          # Document processing service
│   │
│   ├── models/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── chat.py                # Chat request/response models
│   │   ├── report.py              # Report models
│   │   ├── news.py                # News models
│   │   ├── user.py                # User models
│   │   └── common.py              # Shared models
│   │
│   └── prompts/                   # LLM prompt templates
│       ├── __init__.py
│       ├── extraction.py          # Report intelligence extraction
│       ├── so_what.py             # News analysis prompt
│       ├── chat.py                # Chat system prompts
│       ├── minister.py            # Digital Minister agent prompts
│       └── enhance.py             # Query enhancement prompt
│
├── scripts/                       # CLI utilities
│   ├── bulk_import.py             # Import MinerU reports
│   ├── create_admin.py            # Create first admin user
│   ├── test_ragflow.py            # RAGFlow connection test
│   ├── migrate_db.py              # Run database migrations
│   └── export_data.py             # Export for backup
│
├── migrations/                    # Database migrations
│   ├── 001_initial_schema.sql
│   ├── 002_add_databank.sql
│   └── 003_add_news.sql
│
└── tests/                         # Test files
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures
    ├── test_chat.py
    ├── test_library.py
    ├── test_processing.py
    └── test_ragflow.py
```

### 2.2 Core Services

#### 2.2.1 RAGFlow Service (`services/ragflow.py`)

```python
class RAGFlowService:
    """
    Client for RAGFlow API operations.
    Handles: document upload, chat, retrieval, knowledge graph.
    """
    
    async def create_dataset(self, name: str, description: str) -> str:
        """Create a new dataset (knowledge base) in RAGFlow."""
        
    async def upload_document(
        self, 
        dataset_id: str, 
        content: str, 
        metadata: dict,
        enable_graph: bool = True
    ) -> str:
        """Upload document to RAGFlow with optional GraphRAG."""
        
    async def chat(
        self,
        dataset_id: str,
        query: str,
        document_ids: list[str] | None = None,  # Filter to specific docs
        top_k: int = 5,
        include_graph: bool = True
    ) -> ChatResponse:
        """
        Execute RAG query.
        Returns: response text, citations with page numbers.
        """
        
    async def get_related_entities(
        self,
        document_id: str
    ) -> list[Entity]:
        """Get knowledge graph entities for a document."""
        
    async def search_entities(
        self,
        query: str,
        entity_types: list[str] | None = None
    ) -> list[Entity]:
        """Search knowledge graph by entity."""
```

#### 2.2.2 LLM Service (`services/llm.py`)

```python
class LLMService:
    """
    Multi-model LLM client via OpenRouter.
    Handles: model selection, streaming, error handling.
    """
    
    MODELS = {
        "chat": "anthropic/claude-sonnet-4",
        "reasoning": "google/gemini-2.5-pro-preview",
        "fast": "x-ai/grok-3-fast",
        "fallback": "anthropic/claude-3.5-sonnet"
    }
    
    async def complete(
        self,
        messages: list[Message],
        model_type: Literal["chat", "reasoning", "fast"] = "chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate completion from appropriate model.
        Falls back to fallback model on failure.
        """
        
    async def extract_intelligence(
        self,
        document_content: str,
        document_metadata: dict
    ) -> ExtractedIntelligence:
        """
        Run comprehensive extraction prompt.
        Uses: fast model for cost efficiency.
        Returns: structured intelligence data.
        """
```

#### 2.2.3 Deep Agents Service (`services/deep_agents.py`)

```python
from langgraph.graph import StateGraph, END

class DigitalMinisterService:
    """
    Multi-agent system for deep reasoning.
    Uses LangGraph for orchestration.
    """
    
    def __init__(self):
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """
        Build agent workflow graph.
        
        Supervisor → Routes to workers
        Workers: RAG, Framework, RedTeam, WebSearch, Synthesis
        """
        
    async def reason(
        self,
        query: str,
        context: dict | None = None,
        enable_web_search: bool = True
    ) -> MinisterResponse:
        """
        Execute multi-agent reasoning.
        Returns: synthesized response with agent contributions.
        """

class RAGWorker:
    """Searches knowledge hub for relevant information."""
    
class FrameworkWorker:
    """Applies consulting frameworks (McKinsey, BCG, Porter's)."""
    
class RedTeamWorker:
    """Challenges assumptions, finds flaws, contrarian angles."""
    
class WebSearchWorker:
    """Searches web for real-time information via Tavily."""
    
class SynthesisWorker:
    """Combines all inputs into ministerial-grade response."""
```

### 2.3 API Endpoints

#### 2.3.1 Chat API (`api/chat.py`)

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint supporting 3 modes:
    - single: Chat with one document
    - all: Chat across all documents
    - minister: Digital Minister deep reasoning
    """

@router.post("/chat/enhance")
async def enhance_query(
    request: EnhanceRequest,
    current_user: User = Depends(get_current_user)
) -> EnhanceResponse:
    """Enhance user query for better results."""

@router.get("/chat/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
) -> list[Conversation]:
    """List user's conversations."""

@router.get("/chat/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user)
) -> ConversationDetail:
    """Get full conversation with messages."""
```

#### 2.3.2 Library API (`api/library.py`)

```python
@router.get("/reports")
async def list_reports(
    search: str | None = None,
    source: str | None = None,
    year: int | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 20
) -> PaginatedResponse[ReportSummary]:
    """List reports with filtering and pagination."""

@router.get("/reports/{report_id}")
async def get_report(report_id: UUID) -> ReportDetail:
    """Get full report detail with extracted intelligence."""

@router.get("/reports/{report_id}/brief")
async def get_report_brief(report_id: UUID) -> ReportBrief:
    """Get condensed 1-page brief."""

@router.post("/reports/search")
async def search_reports(request: SearchRequest) -> list[SearchResult]:
    """Semantic search across reports."""

@router.get("/reports/{report_id}/related")
async def get_related_reports(report_id: UUID) -> list[RelatedReport]:
    """Get related reports via GraphRAG entities."""
```

#### 2.3.3 Processing API (`api/processing.py`)

```python
@router.post("/admin/upload")
async def upload_reports(
    file: UploadFile,
    current_user: User = Depends(get_admin_user)
) -> ProcessingJob:
    """
    Upload ZIP of MinerU outputs.
    Returns job ID for status tracking.
    """

@router.get("/admin/processing/{job_id}")
async def get_processing_status(
    job_id: UUID,
    current_user: User = Depends(get_admin_user)
) -> ProcessingStatus:
    """Get status of processing job."""

@router.post("/admin/reprocess/{report_id}")
async def reprocess_report(
    report_id: UUID,
    current_user: User = Depends(get_admin_user)
) -> ProcessingJob:
    """Reprocess a specific report."""
```

---

## 3. Frontend Architecture

### 3.1 Directory Structure

```
frontend/
├── Dockerfile
├── Dockerfile.dev
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── components.json              # shadcn/ui config
│
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Dashboard (home)
│   │   ├── globals.css
│   │   │
│   │   ├── (auth)/              # Auth group (no layout)
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── logout/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (dashboard)/         # Main app group
│   │   │   ├── layout.tsx       # Dashboard layout with sidebar
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   └── page.tsx     # Chat interface
│   │   │   │
│   │   │   ├── library/
│   │   │   │   ├── page.tsx     # Library browser
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # Report detail
│   │   │   │
│   │   │   ├── news/
│   │   │   │   └── page.tsx     # News So What
│   │   │   │
│   │   │   ├── meeting-prep/
│   │   │   │   └── page.tsx     # Meeting prep wizard
│   │   │   │
│   │   │   ├── databank/
│   │   │   │   └── page.tsx     # Data bank search
│   │   │   │
│   │   │   └── admin/
│   │   │       ├── page.tsx     # Admin dashboard
│   │   │       └── upload/
│   │   │           └── page.tsx # Bulk upload
│   │   │
│   │   └── api/                 # API routes (if needed)
│   │       └── auth/
│   │           └── callback/
│   │               └── route.ts
│   │
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ModeSelector.tsx
│   │   │   ├── DocumentSelector.tsx
│   │   │   ├── CitationCard.tsx
│   │   │   ├── CitationPopover.tsx
│   │   │   └── PromptEnhancer.tsx
│   │   │
│   │   ├── library/
│   │   │   ├── ReportCard.tsx
│   │   │   ├── ReportGrid.tsx
│   │   │   ├── FilterSidebar.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── ReportDetail/
│   │   │       ├── index.tsx
│   │   │       ├── SummarySection.tsx
│   │   │       ├── FindingsSection.tsx
│   │   │       ├── StatisticsSection.tsx
│   │   │       ├── QuotesSection.tsx
│   │   │       ├── AhaMomentsSection.tsx
│   │   │       └── RelatedReports.tsx
│   │   │
│   │   ├── news/
│   │   │   ├── NewsFeed.tsx
│   │   │   ├── NewsCard.tsx
│   │   │   ├── SoWhatAnalysis.tsx
│   │   │   └── UrlSubmitter.tsx
│   │   │
│   │   ├── databank/
│   │   │   ├── DataBankSearch.tsx
│   │   │   ├── StatisticCard.tsx
│   │   │   ├── QuoteCard.tsx
│   │   │   └── FindingCard.tsx
│   │   │
│   │   ├── admin/
│   │   │   ├── BulkUploader.tsx
│   │   │   ├── ProcessingStatus.tsx
│   │   │   └── UserManagement.tsx
│   │   │
│   │   └── shared/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       ├── LoadingState.tsx
│   │       ├── EmptyState.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ThemeToggle.tsx
│   │
│   ├── lib/
│   │   ├── supabase/
│   │   │   ├── client.ts        # Browser client
│   │   │   ├── server.ts        # Server client
│   │   │   └── middleware.ts    # Auth middleware
│   │   ├── api.ts               # Backend API client
│   │   ├── utils.ts             # Utility functions
│   │   └── constants.ts         # App constants
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useChat.ts
│   │   ├── useLibrary.ts
│   │   ├── useNews.ts
│   │   ├── useDataBank.ts
│   │   └── useProcessing.ts
│   │
│   ├── types/
│   │   ├── chat.ts
│   │   ├── report.ts
│   │   ├── news.ts
│   │   └── common.ts
│   │
│   └── styles/
│       └── globals.css
│
└── public/
    ├── favicon.ico
    ├── logo.svg
    └── source-logos/            # Logos for BCG, McKinsey, etc.
```

### 3.2 Key Components

#### 3.2.1 Chat Interface

```typescript
// components/chat/ChatInterface.tsx
interface ChatInterfaceProps {
  mode: 'single' | 'all' | 'minister';
  documentId?: string;
}

export function ChatInterface({ mode, documentId }: ChatInterfaceProps) {
  // Manages conversation state
  // Handles streaming responses
  // Renders messages with citations
  // Integrates prompt enhancement
}
```

#### 3.2.2 Mode Selector

```typescript
// components/chat/ModeSelector.tsx
interface ModeSelectorProps {
  value: 'single' | 'all' | 'minister';
  onChange: (mode: 'single' | 'all' | 'minister') => void;
}

// Three tabs:
// - "Single Report" - with document selector
// - "All Reports" - full knowledge base
// - "Digital Minister" - deep reasoning (highlighted as premium)
```

#### 3.2.3 Citation Card

```typescript
// components/chat/CitationCard.tsx
interface Citation {
  reportId: string;
  reportTitle: string;
  source: string;
  page: number;
  excerpt: string;
}

interface CitationCardProps {
  citation: Citation;
  onViewReport: () => void;
}

// Renders inline [1] reference
// Popover shows excerpt on hover
// Click opens report at page
```

---

## 4. Database Schema

### 4.1 Full Schema (Supabase PostgreSQL)

```sql
-- ============================================
-- DCAI Intelligence Platform Database Schema
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- ============================================
-- REPORTS
-- ============================================
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic metadata
    title TEXT NOT NULL,
    source TEXT NOT NULL,                    -- BCG, McKinsey, DCAI, etc.
    year INTEGER,
    category TEXT,                           -- Consulting, Research, Policy, News
    page_count INTEGER,
    
    -- File references
    original_filename TEXT,
    mineru_folder TEXT,                      -- Path to MinerU output
    ragflow_doc_id TEXT,                     -- Reference in RAGFlow
    pdf_storage_path TEXT,                   -- Supabase storage path
    
    -- Extracted intelligence (JSONB for flexibility)
    executive_summary TEXT,
    key_findings JSONB DEFAULT '[]',         -- [{finding, evidence, page, significance}]
    statistics JSONB DEFAULT '[]',           -- [{stat, context, source_page}]
    quotes JSONB DEFAULT '[]',               -- [{quote, speaker, context, page}]
    aha_moments JSONB DEFAULT '[]',          -- [{insight, why_contrarian, implications}]
    recommendations JSONB DEFAULT '[]',      -- [{recommendation, rationale, page}]
    methodology TEXT,
    limitations TEXT,
    
    -- Full text for search
    full_text TEXT,
    
    -- Processing status
    processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    processed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for search and filtering
CREATE INDEX idx_reports_source ON reports(source);
CREATE INDEX idx_reports_year ON reports(year);
CREATE INDEX idx_reports_category ON reports(category);
CREATE INDEX idx_reports_ragflow ON reports(ragflow_doc_id);
CREATE INDEX idx_reports_status ON reports(processing_status);
CREATE INDEX idx_reports_fulltext ON reports USING gin(to_tsvector('english', full_text));
CREATE INDEX idx_reports_title_trgm ON reports USING gin(title gin_trgm_ops);

-- ============================================
-- CONVERSATIONS
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Conversation context
    mode TEXT NOT NULL,                      -- 'single', 'all', 'minister'
    report_id UUID REFERENCES reports(id),   -- Only for 'single' mode
    title TEXT,                              -- Auto-generated from first message
    
    -- Settings
    settings JSONB DEFAULT '{}',             -- Model preferences, etc.
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_mode ON conversations(mode);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- ============================================
-- MESSAGES
-- ============================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message content
    role TEXT NOT NULL,                      -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- For assistant messages
    citations JSONB DEFAULT '[]',            -- [{report_id, page, excerpt}]
    model_used TEXT,
    tokens_used INTEGER,
    
    -- For enhanced queries
    original_content TEXT,                   -- Before enhancement
    was_enhanced BOOLEAN DEFAULT FALSE,
    
    -- For Digital Minister
    agent_contributions JSONB DEFAULT '[]',  -- [{agent, contribution}]
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- ============================================
-- NEWS ITEMS
-- ============================================
CREATE TABLE news_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Article info
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    source TEXT,                             -- Publication name
    author TEXT,
    published_at TIMESTAMPTZ,
    
    -- Content
    raw_content TEXT,
    
    -- Analysis
    so_what_analysis JSONB,                  -- {summary, so_what, implications, opportunities, risks, talking_point}
    analyzed_at TIMESTAMPTZ,
    analysis_model TEXT,
    
    -- User who submitted
    submitted_by UUID REFERENCES auth.users(id),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_url ON news_items(url);
CREATE INDEX idx_news_published ON news_items(published_at DESC);
CREATE INDEX idx_news_created ON news_items(created_at DESC);

-- ============================================
-- DATA BANK
-- ============================================
CREATE TABLE data_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    
    -- Item details
    type TEXT NOT NULL,                      -- 'statistic', 'quote', 'finding', 'aha_moment', 'recommendation'
    content TEXT NOT NULL,
    context TEXT,                            -- Surrounding context
    source_page INTEGER,
    
    -- Categorization
    tags TEXT[] DEFAULT '{}',
    topic TEXT,
    
    -- For quotes
    speaker TEXT,
    
    -- For statistics
    value TEXT,                              -- The actual number
    unit TEXT,                               -- %, $, etc.
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_databank_report ON data_bank(report_id);
CREATE INDEX idx_databank_type ON data_bank(type);
CREATE INDEX idx_databank_tags ON data_bank USING gin(tags);
CREATE INDEX idx_databank_content ON data_bank USING gin(to_tsvector('english', content));

-- ============================================
-- PROCESSING JOBS
-- ============================================
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job info
    type TEXT NOT NULL,                      -- 'bulk_upload', 'single_reprocess'
    status TEXT DEFAULT 'pending',           -- 'pending', 'running', 'completed', 'failed'
    
    -- Progress
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    
    -- Details
    items JSONB DEFAULT '[]',                -- [{filename, status, error?}]
    error TEXT,
    
    -- User
    created_by UUID REFERENCES auth.users(id),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_created ON processing_jobs(created_at DESC);

-- ============================================
-- USER PREFERENCES
-- ============================================
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- UI preferences
    theme TEXT DEFAULT 'dark',               -- 'dark', 'light', 'system'
    default_chat_mode TEXT DEFAULT 'all',    -- 'single', 'all', 'minister'
    
    -- Feature preferences
    auto_enhance_queries BOOLEAN DEFAULT FALSE,
    show_agent_contributions BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- AUDIT LOG
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    
    -- Action details
    action TEXT NOT NULL,                    -- 'chat', 'search', 'view_report', 'upload', etc.
    resource_type TEXT,                      -- 'report', 'conversation', etc.
    resource_id UUID,
    
    -- Context
    metadata JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_bank ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Reports: All authenticated users can read
CREATE POLICY "Reports are viewable by authenticated users"
    ON reports FOR SELECT
    TO authenticated
    USING (true);

-- Conversations: Users can only see their own
CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations"
    ON conversations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON conversations FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON conversations FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Messages: Based on conversation ownership
CREATE POLICY "Users can view messages in own conversations"
    ON messages FOR SELECT
    TO authenticated
    USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own conversations"
    ON messages FOR INSERT
    TO authenticated
    WITH CHECK (
        conversation_id IN (
            SELECT id FROM conversations WHERE user_id = auth.uid()
        )
    );

-- News items: All authenticated users can read, only submitter can modify
CREATE POLICY "News items are viewable by authenticated users"
    ON news_items FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can submit news items"
    ON news_items FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = submitted_by);

-- Data bank: All authenticated users can read
CREATE POLICY "Data bank is viewable by authenticated users"
    ON data_bank FOR SELECT
    TO authenticated
    USING (true);

-- User preferences: Users can only access their own
CREATE POLICY "Users can view own preferences"
    ON user_preferences FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON user_preferences FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-generate conversation title from first message
CREATE OR REPLACE FUNCTION set_conversation_title()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.role = 'user' THEN
        UPDATE conversations
        SET title = LEFT(NEW.content, 100)
        WHERE id = NEW.conversation_id AND title IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_conversation_title
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION set_conversation_title();
```

---

## 5. Processing Pipeline

### 5.1 Document Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Document Processing Pipeline                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │ 1. Upload ZIP   │  Admin uploads ZIP of MinerU outputs                  │
│  │    Validation   │  - Validate ZIP structure                              │
│  │                 │  - Check for required files (.md, content_list.json)   │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ 2. Extract &    │  For each report folder:                              │
│  │    Parse        │  - Read {name}.md for full text                       │
│  │                 │  - Parse {name}_content_list.json for page numbers     │
│  │                 │  - Extract metadata (title from filename/content)      │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ 3. Upload to    │  POST to RAGFlow API:                                 │
│  │    RAGFlow      │  - Create/select dataset                              │
│  │                 │  - Upload document with metadata                       │
│  │                 │  - Enable GraphRAG entity extraction                   │
│  │                 │  - Store ragflow_doc_id                               │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ 4. Intelligence │  Run extraction prompt (Grok Fast):                   │
│  │    Extraction   │  - Executive summary                                   │
│  │                 │  - All key findings with evidence                      │
│  │                 │  - All statistics with context                         │
│  │                 │  - Quotable language                                   │
│  │                 │  - Aha moments / contrarian insights                   │
│  │                 │  - Recommendations                                     │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ 5. Store in     │  Save to Supabase:                                    │
│  │    Database     │  - reports table: all metadata + extracted intel      │
│  │                 │  - data_bank table: individual stats, quotes, etc.    │
│  │                 │  - Update processing_jobs status                      │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ 6. Notify       │  Send notification:                                   │
│  │                 │  - Update job status to 'completed'                   │
│  │                 │  - Log success/failures                               │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Extraction Prompt

```python
EXTRACTION_PROMPT = """
You are an expert intelligence analyst extracting insights from strategic reports for the UAE Minister of AI.

REPORT METADATA:
- Title: {title}
- Source: {source}
- Year: {year}

REPORT CONTENT:
{content}

---

Extract the following. Be COMPREHENSIVE - extract ALL instances, not just 3-5 examples.
For each item, include the exact page number from the source.

## EXECUTIVE SUMMARY
Write a 2-3 paragraph executive summary capturing the essence of this report.
Focus on: main thesis, key conclusions, unique contributions.

## KEY FINDINGS
Extract ALL significant findings. For each:
- finding: The core insight
- evidence: Supporting data or argument
- page: Source page number
- significance: Why this matters (1 sentence)

## STATISTICS
Extract ALL statistics, numbers, and quantitative claims. For each:
- stat: The exact statistic (preserve original wording)
- context: What this number represents
- source_page: Page number
- comparisons: Any comparisons made (YoY, vs competitors, etc.)

## QUOTABLE LANGUAGE
Extract memorable phrases suitable for speeches or presentations. For each:
- quote: The exact wording
- speaker: Who said it (if attributed)
- context: What it refers to
- page: Source page

## AHA MOMENTS
Identify contrarian, surprising, or non-obvious insights. For each:
- insight: The surprising finding
- why_contrarian: Why this challenges conventional wisdom
- implications: What this means strategically

## RECOMMENDATIONS
Extract all recommendations or action items. For each:
- recommendation: What is advised
- rationale: Why it's recommended
- page: Source page
- priority: Implied urgency (high/medium/low)

## METHODOLOGY
Describe the research methodology used (survey size, data sources, timeframe).

## LIMITATIONS
Note any limitations, caveats, or biases acknowledged or apparent.

---

Output as valid JSON with this structure:
{
  "executive_summary": "...",
  "key_findings": [...],
  "statistics": [...],
  "quotes": [...],
  "aha_moments": [...],
  "recommendations": [...],
  "methodology": "...",
  "limitations": "..."
}
"""
```

---

## 6. Digital Minister Architecture

### 6.1 Multi-Agent System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Digital Minister - LangGraph Architecture               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User Query: "Red team my proposal for a $1B sovereign AI fund"            │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SUPERVISOR AGENT                             │   │
│  │                      (Claude Sonnet 4)                              │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  - Analyze query intent                                             │   │
│  │  - Route to appropriate workers                                      │   │
│  │  - Determine worker sequence                                         │   │
│  │  - Synthesize final response                                        │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│         ┌────────────────────────┼────────────────────────┐                │
│         │                        │                        │                │
│         ▼                        ▼                        ▼                │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │ RAG Worker  │          │ Framework   │          │ RedTeam     │        │
│  │             │          │ Worker      │          │ Worker      │        │
│  │ Claude      │          │ Gemini 2.5  │          │ Gemini 2.5  │        │
│  │ Sonnet 4    │          │ Pro         │          │ Pro         │        │
│  │             │          │             │          │             │        │
│  │ Search      │          │ Apply       │          │ Challenge   │        │
│  │ knowledge   │          │ McKinsey/   │          │ assumptions │        │
│  │ hub         │          │ BCG/Porter  │          │ find flaws  │        │
│  │             │          │ frameworks  │          │ identify    │        │
│  │             │          │             │          │ risks       │        │
│  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘        │
│         │                        │                        │                │
│         │         ┌──────────────┼──────────────┐         │                │
│         │         │              │              │         │                │
│         │         ▼              ▼              ▼         │                │
│         │  ┌─────────────┐                ┌─────────────┐ │                │
│         │  │ WebSearch   │                │ Synthesis   │ │                │
│         │  │ Worker      │                │ Worker      │ │                │
│         │  │             │                │             │ │                │
│         │  │ Grok Fast   │                │ Claude      │ │                │
│         │  │             │                │ Sonnet 4    │ │                │
│         │  │ Real-time   │                │             │ │                │
│         │  │ web search  │                │ Combine     │ │                │
│         │  │ via Tavily  │                │ all inputs  │ │                │
│         │  │             │                │ into        │ │                │
│         │  │             │                │ ministerial │ │                │
│         │  │             │                │ brief       │ │                │
│         │  └──────┬──────┘                └──────┬──────┘ │                │
│         │         │                              │        │                │
│         └─────────┴──────────────┬───────────────┴────────┘                │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FINAL RESPONSE                               │   │
│  │                                                                      │   │
│  │  Structured ministerial brief with:                                 │   │
│  │  - Executive summary                                                 │   │
│  │  - Analysis from each agent                                         │   │
│  │  - Key risks and mitigations                                        │   │
│  │  - Recommended actions                                              │   │
│  │  - Agent contribution labels                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Agent Prompts

```python
# prompts/minister.py

SUPERVISOR_PROMPT = """
You are the supervisor of a strategic advisory team for the UAE Minister of AI.
Your role is to:
1. Analyze the user's query to understand their intent
2. Route the query to appropriate worker agents
3. Synthesize their contributions into a cohesive response

Available workers:
- RAG: Search the knowledge hub (405 strategic reports)
- Framework: Apply consulting frameworks (McKinsey 7S, Porter's 5 Forces, etc.)
- RedTeam: Challenge assumptions, find flaws, identify risks
- WebSearch: Get real-time information from the web

For this query: {query}

Determine:
1. Which workers to invoke (can be multiple)
2. In what order
3. What specific instructions for each

Output as JSON:
{
  "analysis": "Brief analysis of query intent",
  "workers": [
    {"name": "RAG", "instruction": "..."},
    {"name": "Framework", "instruction": "..."},
    ...
  ]
}
"""

FRAMEWORK_WORKER_PROMPT = """
You are a strategic consultant with deep expertise in:
- McKinsey 7S Framework
- Porter's Five Forces
- BCG Growth-Share Matrix
- Blue Ocean Strategy
- SWOT Analysis
- PESTLE Analysis
- Value Chain Analysis

Apply the most relevant framework(s) to analyze: {query}

Context from knowledge hub: {rag_context}

Provide structured analysis using the framework, with specific insights relevant to UAE and AI strategy.
"""

REDTEAM_WORKER_PROMPT = """
You are a red team analyst. Your job is to:
1. Challenge every assumption
2. Find weaknesses and risks
3. Identify what could go wrong
4. Surface contrarian viewpoints
5. Stress-test proposals

For this proposal/idea: {query}

Context: {context}

Provide:
1. Key assumptions being made
2. Potential failure modes
3. Risks not being considered
4. Contrarian perspectives
5. Questions that should be asked

Be rigorous but constructive. The goal is to strengthen the proposal, not dismiss it.
"""

SYNTHESIS_WORKER_PROMPT = """
You are synthesizing insights from multiple sources into a ministerial brief.

Original query: {query}

Inputs from agents:
{agent_contributions}

Create a cohesive response that:
1. Directly answers the question
2. Integrates insights from all sources
3. Highlights key risks and opportunities
4. Provides actionable recommendations
5. Is suitable for a cabinet minister

Structure:
- Executive Summary (2-3 sentences)
- Analysis (organized by theme, not by agent)
- Key Risks
- Recommendations
- Sources/Citations
"""
```

---

## 7. Deployment Architecture

### 7.1 Dokploy Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Dokploy Server                                    │
│                    (8 vCPU, 32GB RAM, 400GB NVMe)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Traefik                                    │   │
│  │                      (Reverse Proxy + SSL)                          │   │
│  │                                                                      │   │
│  │  myintel.alfalasi.io      → frontend:3000                          │   │
│  │  api.myintel.alfalasi.io  → backend:8000                           │   │
│  │  ragflow.myintel.alfalasi.io → ragflow:9380 (optional)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │    Frontend      │  │    Backend       │  │    RAGFlow       │         │
│  │    (Next.js)     │  │    (FastAPI)     │  │    (RAG Engine)  │         │
│  │    Port 3000     │  │    Port 8000     │  │    Port 9380     │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │  Elasticsearch   │  │      MySQL       │  │      MinIO       │         │
│  │  (Vectors)       │  │  (RAGFlow Meta)  │  │  (Object Store)  │         │
│  │  Port 9200       │  │  Port 3306       │  │  Port 9000       │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │      Redis       │                                                       │
│  │  (Cache/Queue)   │                                                       │
│  │  Port 6379       │                                                       │
│  └──────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
           ┌────────▼────────┐             ┌───────▼───────┐
           │    Supabase     │             │   External    │
           │    (Your VPS)   │             │   Services    │
           │                 │             │               │
           │ - PostgreSQL    │             │ - OpenRouter  │
           │ - Auth          │             │ - Firecrawl   │
           │ - Storage       │             │ - Tavily      │
           └─────────────────┘             └───────────────┘
```

### 7.2 Resource Allocation

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| RAGFlow | 2 cores | 8GB | 50GB |
| Elasticsearch | 2 cores | 8GB | 100GB |
| MySQL | 0.5 cores | 1GB | 10GB |
| MinIO | 0.5 cores | 1GB | 100GB |
| Redis | 0.25 cores | 512MB | 1GB |
| Backend | 1 core | 2GB | 5GB |
| Frontend | 0.5 cores | 1GB | 2GB |
| **Total** | **6.75 cores** | **21.5GB** | **268GB** |

Leaves headroom: 1.25 cores, 10.5GB RAM, 132GB storage

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Authentication Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User visits myintel.alfalasi.io                                        │
│       │                                                                     │
│       ▼                                                                     │
│  2. Frontend checks Supabase session                                       │
│       │                                                                     │
│       ├── Session valid → Show dashboard                                   │
│       │                                                                     │
│       └── No session → Redirect to /login                                  │
│             │                                                               │
│             ▼                                                               │
│  3. User enters credentials                                                │
│       │                                                                     │
│       ▼                                                                     │
│  4. Supabase Auth validates                                                │
│       │                                                                     │
│       ▼                                                                     │
│  5. JWT issued → Stored in httpOnly cookie                                 │
│       │                                                                     │
│       ▼                                                                     │
│  6. Frontend includes JWT in API requests                                  │
│       │                                                                     │
│       ▼                                                                     │
│  7. Backend validates JWT with Supabase                                    │
│       │                                                                     │
│       ▼                                                                     │
│  8. Request processed with user context                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Security Measures

| Layer | Measure |
|-------|---------|
| Transport | TLS 1.3 (Let's Encrypt) |
| Authentication | Supabase Auth (JWT) |
| Authorization | Row Level Security (RLS) |
| API | Rate limiting, CORS |
| Data | Encrypted at rest (PostgreSQL) |
| Secrets | Environment variables, never in code |
| Audit | All actions logged with user ID |

---

## 9. Monitoring & Observability

### 9.1 Logging Strategy

```python
# Structured logging format
{
    "timestamp": "2026-01-03T10:00:00Z",
    "level": "INFO",
    "service": "backend",
    "trace_id": "abc123",
    "user_id": "uuid",
    "action": "chat_request",
    "mode": "all",
    "tokens_used": 1500,
    "latency_ms": 2340,
    "model": "claude-sonnet-4"
}
```

### 9.2 Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Response time (p95) | < 3s | > 5s |
| Error rate | < 1% | > 5% |
| RAGFlow latency | < 500ms | > 1s |
| LLM latency | < 2s | > 5s |
| Database connections | < 80% | > 90% |
| Memory usage | < 80% | > 90% |

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

| Component | Backup Frequency | Retention | Method |
|-----------|-----------------|-----------|--------|
| Supabase (PostgreSQL) | Daily | 30 days | Supabase automated |
| RAGFlow Elasticsearch | Weekly | 4 weeks | Snapshot to MinIO |
| RAGFlow MySQL | Daily | 7 days | mysqldump |
| MinIO objects | Weekly | 4 weeks | Sync to S3 |

### 10.2 Recovery Procedures

1. **Database failure:** Restore from Supabase backup (< 1 hour)
2. **RAGFlow failure:** Redeploy container, restore from snapshots (< 2 hours)
3. **Complete server failure:** Redeploy via Dokploy, restore backups (< 4 hours)

---

## Appendix A: API Reference

See `docs/API.md` for full API documentation with request/response examples.

## Appendix B: Environment Variables

See `.env.example` for all required environment variables.

## Appendix C: Database Migrations

See `backend/migrations/` for SQL migration files.
