# DCAI Intelligence Platform - Project Instructions

## Project Overview

**Name:** DCAI Intelligence Platform  
**Domain:** myintel.alfalasi.io  
**Purpose:** AI-powered executive intelligence platform for UAE Minister of AI and DCAI team (~20 users)

**Core Concept:** A "Digital Minister" / "Second Brain" that can:
- Brief the minister in 2 minutes before any meeting/TV interview
- Surface "Aha moments" and contrarian insights for thought leadership
- Apply "So What?" analysis to news (strategic implications, not just summaries)
- Act as a multi-agent consultancy for red-teaming ideas and strategic thinking

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 14 + shadcn/ui + Tailwind | User interface |
| Backend | FastAPI (Python 3.11+) | API layer |
| Database | Supabase (PostgreSQL) | Auth, metadata, structured data |
| Vector DB | RAGFlow | Vectors, GraphRAG, retrieval |
| LLM Gateway | OpenRouter | Multi-model access |
| News | Firecrawl + Tavily | Article scraping + web search |

---

## LLM Strategy

| Use Case | Model | Why |
|----------|-------|-----|
| All Tasks | `google/gemini-3-flash-preview` | 93% JSON validity, native PDF, low hallucinations, fast |

**Single model strategy** - Gemini 3 Flash handles chat, reasoning, and extraction.

**NEVER use DeepSeek** - too slow for production use.

---

## Key Features (Priority Order)

### P0 - Must Have
1. **Chat with ALL reports** - RAG across 405 documents with citations
2. **Chat with SINGLE report** - Smart search selector, not dropdown
3. **Library** - Browse/search/filter by source/year/category
4. **Report Detail** - Comprehensive intelligence brief (not just metadata)
5. **Admin Bulk Upload** - ZIP of MinerU outputs

### P1 - Important
6. **Meeting Prep** - With purpose, context, angle options
7. **Talking Points Generator**
8. **Report Summarizer**
9. **Aha Moments / Insights Extraction**
10. **News "So What?"** - Firecrawl + strategic analysis

### P2 - Nice to Have
11. Cross-report comparison
12. Trend Radar
13. Data Bank (statistics, quotes, findings)
14. Dashboard with insights

### P3 - Future
15. **Digital Minister Chat** - Multi-agent deep reasoning
16. Prompt enhancement button in chat

---

## Data Sources

**Location:** `C:\myprojects\REVIEW\NewHUB\processed_reports_mineru`  
**Count:** 405 MinerU-processed reports

**MinerU Output Structure (per report):**
```
report_name/vlm/
├── report_name.md              # Clean markdown text (PRIMARY)
├── report_name_content_list.json    # Structured content with page numbers
├── report_name_content_list_v2.json # Alternative structure
├── report_name_model.json           # Model metadata
├── report_name_middle.json          # Intermediate data
├── report_name_origin.pdf           # Original PDF
├── report_name_layout.pdf           # Layout analysis
└── images/                          # Extracted figures
```

**Sources include:** BCG, McKinsey, Deloitte, Accenture, KPMG, EY, Capgemini, Google, Dubai-specific (DCAI, DFF), government agencies, think tanks

---

## GraphRAG Configuration

RAGFlow with LightRAG enabled for knowledge graph construction.

**Entity Types:**
- person
- organization
- policy
- initiative
- technology
- country
- statistic
- recommendation
- risk
- opportunity

**Purpose:** Enable multi-hop QA, find connections across reports, power "Aha moments" feature.

---

## Database Schema (Supabase)

### Core Tables

```sql
-- Reports metadata
reports (
    id UUID PRIMARY KEY,
    title TEXT,
    source TEXT,                    -- BCG, McKinsey, DCAI, etc.
    year INTEGER,
    category TEXT,                  -- Consulting, Research, Policy, News
    original_filename TEXT,
    mineru_folder TEXT,
    ragflow_doc_id TEXT,
    executive_summary TEXT,
    key_findings JSONB,
    statistics JSONB,
    quotes JSONB,
    aha_moments JSONB,
    recommendations JSONB,
    created_at TIMESTAMPTZ
)

-- Chat history
conversations (
    id UUID PRIMARY KEY,
    user_id UUID,
    mode TEXT,                      -- 'single', 'all', 'minister'
    report_id UUID,
    created_at TIMESTAMPTZ
)

messages (
    id UUID PRIMARY KEY,
    conversation_id UUID,
    role TEXT,
    content TEXT,
    citations JSONB,
    model_used TEXT,
    created_at TIMESTAMPTZ
)

-- News analysis
news_items (
    id UUID PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    source TEXT,
    published_at TIMESTAMPTZ,
    raw_content TEXT,
    so_what_analysis JSONB,
    created_at TIMESTAMPTZ
)

-- Data Bank
data_bank (
    id UUID PRIMARY KEY,
    report_id UUID,
    type TEXT,                      -- 'statistic', 'quote', 'finding', 'aha_moment'
    content TEXT,
    context TEXT,
    source_page INTEGER,
    tags TEXT[],
    created_at TIMESTAMPTZ
)
```

---

## API Endpoints

### Chat
```
POST /api/chat
    body: { mode, document_id?, message, conversation_id? }
    returns: { response, citations, model_used }

GET /api/chat/conversations
GET /api/chat/conversations/{id}
```

### Library
```
GET /api/reports
    query: { search?, source?, year?, category?, page?, limit? }

GET /api/reports/{id}
GET /api/reports/{id}/brief
POST /api/reports/search
    body: { query, semantic?: boolean }
```

### Processing
```
POST /api/admin/upload
    body: multipart/form-data (ZIP file)

GET /api/admin/processing/{job_id}
POST /api/admin/reprocess/{report_id}
```

### News
```
GET /api/news
POST /api/news/analyze
    body: { url }
```

### Data Bank
```
GET /api/databank
    query: { type?, search?, report_id? }
```

### Digital Minister
```
POST /api/minister/chat
    body: { message, conversation_id?, enable_web_search?: boolean }
```

---

## Chat Modes

### Mode 1: Single Document
- User selects document via smart search (not dropdown)
- RAG retrieval filtered to that document only
- Citations show page numbers
- Model: Claude Sonnet 4

### Mode 2: All Documents
- RAG across all 405 documents
- Multi-document citations
- Cross-reference capabilities
- Model: Claude Sonnet 4

### Mode 3: Digital Minister
- LangGraph multi-agent system
- Agents: RAG, Framework, RedTeam, WebSearch, Synthesis
- Can access knowledge hub + live web
- Longer timeout (180s)
- Model: Gemini 2.5 Pro for reasoning, Claude for synthesis

---

## Key Prompts

### Report Extraction Prompt
Located at: `backend/app/prompts/extraction.py`

Purpose: Extract ALL intelligence from a report during ingestion:
- Executive summary
- ALL key findings with evidence, significance, page number
- ALL statistics with context
- Recommendations
- Quotable language
- Contrarian insights / Aha moments
- Methodology and limitations

### News "So What?" Prompt
Located at: `backend/app/prompts/so_what.py`

Purpose: Strategic analysis for UAE Minister of AI:
- SO WHAT? (why this matters)
- IMPLICATIONS FOR UAE
- OPPORTUNITIES
- RISKS
- MINISTERIAL TALKING POINT

UAE Priorities: sovereign AI, regional leadership, talent attraction, regulatory positioning, economic diversification

### Digital Minister System Prompts
Located at: `backend/app/prompts/minister.py`

Purpose: Multi-agent prompts for deep reasoning:
- Supervisor: Route queries, synthesize responses
- Framework Worker: Apply McKinsey/BCG frameworks
- RedTeam Worker: Challenge assumptions, find flaws
- Synthesis Worker: Create ministerial-grade output

---

## Development Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# RAGFlow
docker-compose up ragflow -d

# Process reports (local)
cd processing
python process_reports.py

# Run tests
cd backend && pytest
cd frontend && npm test
```

---

## File Structure

```
C:\myprojects\OC_HUB\
├── .env                          # Environment variables
├── .env.example                  # Template
├── CLAUDE.md                     # This file
├── docker-compose.yml            # RAGFlow stack
│
├── backend/                      # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                  # Route handlers
│   │   ├── services/             # Business logic
│   │   ├── models/               # Pydantic schemas
│   │   ├── core/                 # Config, auth, deps
│   │   └── prompts/              # LLM prompt templates
│   └── scripts/                  # CLI utilities
│
├── frontend/                     # Next.js
│   └── src/
│       ├── app/                  # Pages (app router)
│       ├── components/           # React components
│       ├── lib/                  # Utilities
│       └── hooks/                # Custom hooks
│
├── processing/                   # Document processing
│   ├── process_reports.py
│   └── ragflow_uploader.py
│
└── docs/                         # Documentation
    ├── PRD.md
    └── ARCHITECTURE.md
```

---

## Infrastructure

### Existing (User's VPS)
- Supabase (PostgreSQL + Auth + REST)
- Dokploy at mydokploy.alfalasi.io

### To Deploy
- RAGFlow (via Docker Compose)
- FastAPI backend
- Next.js frontend

### Domains
- `myintel.alfalasi.io` → Frontend
- `api.myintel.alfalasi.io` → Backend
- (Optional) `ragflow.myintel.alfalasi.io` → RAGFlow UI

---

## Admin User

- **Email:** s.falasi@gmail.com
- **Password:** Bu3askoor@5057
- Pre-create this user during setup

---

## Critical Rules

1. **Never hardcode API keys** - Always use environment variables
2. **Always return citations** - Every RAG response must cite sources with page numbers
3. **Preserve page numbers** - MinerU content_list.json has page_idx, use it
4. **Comprehensive extraction** - Extract ALL data, not limited samples
5. **GraphRAG enabled** - Process with knowledge graph from start
6. **Error handling** - Never silent failures, always log and surface errors
7. **Rate limiting** - Respect OpenRouter limits, implement backoff
8. **Prompt Review Required** - BEFORE running any operation that uses an LLM prompt (extraction, analysis, chat system prompts, etc.), STOP and show Q the prompt for review and approval. This includes:
   - New prompts being created
   - Modifications to existing prompts
   - Batch operations that will use prompts on multiple items
   - Any prompt that will be sent to OpenRouter/LLM APIs
   
   Format: Show the full prompt, explain its purpose, wait for explicit "approved" before proceeding.

---

## OpenCode Configuration

**MCP Config Location:** `C:\Users\sfala\.config\opencode\opencode.json`  
**NOT** the Claude default at `~/.claude/mcp.json`

**Current Plugins:**
- `oh-my-opencode` - Agent orchestration
- `opencode-antigravity-auth@1.2.7` - Auth provider

**Current MCPs:**
- `github` - GitHub integration
- `supabase` - Database (mysupabase.alfalasi.io)
- `tavily` - Web search
- `deepwiki` - Documentation lookup
- `dokploy` - Deployment (mydokploy.alfalasi.io)
- `apple-dev` - Apple developer docs

---

## MANDATORY: Pipeline Validation Rules

**BEFORE running ANY batch process that writes to database/storage:**

### Pre-Flight Checklist (NON-NEGOTIABLE)

```
1. SCHEMA VALIDATION
   [ ] All required tables exist
   [ ] All required columns exist  
   [ ] Test INSERT on each target table with dummy data
   [ ] Test DELETE of dummy data
   
2. SINGLE RECORD TEST
   [ ] Process exactly ONE item through full pipeline
   [ ] Verify ALL expected outputs were created
   [ ] Check counts: if process creates 5 types of records, verify 5 types exist
   [ ] Read back the data and validate structure
   
3. SAMPLE VALIDATION (after 5 items)
   [ ] Counts match expectations (e.g., 5 reports = ~25 data_bank items, not 0)
   [ ] No error patterns in logs
   [ ] Data quality spot-check
   
4. ONLY THEN: Full batch processing
```

### Validation Script Template

For any data pipeline, create a validation script FIRST:

```python
async def validate_pipeline():
    """Run BEFORE any batch processing."""
    
    # 1. Check tables exist
    for table in ['reports', 'data_bank', 'conversations', 'messages']:
        result = await test_table_access(table)
        if not result.success:
            raise PipelineError(f"Table {table} not accessible: {result.error}")
    
    # 2. Test write/read cycle
    test_id = await insert_test_record()
    retrieved = await get_record(test_id)
    await delete_test_record(test_id)
    
    if not retrieved:
        raise PipelineError("Write/read cycle failed")
    
    # 3. Process single item
    result = await process_single_item(sample_item)
    
    # 4. Validate ALL outputs
    expected_outputs = ['report_created', 'databank_items_created', 'ragflow_uploaded']
    for output in expected_outputs:
        if output not in result:
            raise PipelineError(f"Missing expected output: {output}")
    
    print("Pipeline validation PASSED")
    return True
```

### What Happens If You Skip This

- Wasted compute (processing 405 reports that fail silently)
- Wasted time (hours of work producing nothing)
- Data inconsistency (partial data that needs manual cleanup)
- Loss of trust (user doesn't know what state the system is in)

### Recovery Protocol

If a batch process fails partway:

1. **STOP** - Don't retry blindly
2. **ASSESS** - How many succeeded? What failed?
3. **FIX ROOT CAUSE** - Why did it fail?
4. **VALIDATE FIX** - Test single item again
5. **RESUME** - Continue from last successful point, don't restart from zero

---

## Testing Strategy

1. **Unit tests** - Backend services (pytest)
2. **Integration tests** - API endpoints with test database
3. **E2E tests** - Playwright for frontend flows
4. **Manual QA** - Test with real reports before production

---

## Deployment Checklist

- [ ] All .env variables filled
- [ ] RAGFlow running and accessible
- [ ] Supabase migrations applied
- [ ] Admin user created
- [ ] All 405 reports processed
- [ ] SSL certificates configured
- [ ] DNS pointing correctly
- [ ] Smoke test all features
- [ ] Backup configured

---

## Continuation Prompt

If starting a new session, use this prompt:

```
Continue building DCAI Intelligence Platform (myintel.alfalasi.io).

Read CLAUDE.md for full context. Current status: [describe where you left off]

Key facts:
- 405 MinerU-processed reports at C:\myprojects\REVIEW\NewHUB\processed_reports_mineru
- Supabase already running on user's VPS
- Tech: RAGFlow + FastAPI + Next.js + OpenRouter
- LLMs: Claude Sonnet 4 (chat), Gemini 2.5 Pro (reasoning), Gemini 3 Flash (extraction)
```
