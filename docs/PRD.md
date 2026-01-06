# Product Requirements Document (PRD)
# DCAI Intelligence Platform

**Version:** 1.0  
**Date:** 2026-01-03  
**Product Owner:** H.E. Omar Al Olama (UAE Minister of AI)  
**Platform:** myintel.alfalasi.io

---

## 1. Executive Summary

### 1.1 Vision
The DCAI Intelligence Platform is an AI-powered executive intelligence system designed to serve as the UAE Minister of AI's "Digital Second Brain." It transforms 405+ strategic reports into actionable intelligence, enabling faster decision-making, deeper insights, and thought leadership positioning.

### 1.2 Problem Statement
Senior executives face information overload:
- Too many reports to read (405+ and growing)
- No time to synthesize across sources
- Miss connections between reports from different consultancies
- Need briefings in minutes, not hours
- Want contrarian insights for thought leadership, not just summaries

### 1.3 Solution
An AI platform that:
1. **Ingests** all reports with deep understanding (GraphRAG)
2. **Retrieves** relevant intelligence with citations
3. **Synthesizes** across multiple sources
4. **Analyzes** news through strategic lens ("So What?")
5. **Reasons** like a consultancy team (Digital Minister)

### 1.4 Success Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to brief | < 2 minutes | From question to comprehensive answer |
| Citation accuracy | 100% | Every claim linked to source + page |
| User satisfaction | > 4.5/5 | Weekly NPS survey |
| Daily active users | 80% of team | 16/20 users active daily |
| Insights per week | 10+ "Aha moments" | Tracked contrarian insights |

---

## 2. Users & Personas

### 2.1 Primary User: UAE Minister of AI
**Name:** H.E. Omar Al Olama  
**Role:** Cabinet Minister, DCAI Board Member  
**Needs:**
- Brief me in 2 minutes before any meeting
- Give me contrarian angles no one else has
- Find the "So What?" in every news story
- Red-team my ideas before I present them
- Make me the most prepared person in any room

**Pain Points:**
- No time to read 100+ page reports
- Consultancies give similar advice - need differentiation
- News is everywhere but strategic implications aren't clear
- Hard to find specific statistics quickly

### 2.2 Secondary Users: DCAI Team (~20 people)

**Analysts:**
- Research specific topics across reports
- Compile briefing materials
- Extract statistics and quotes for presentations

**Executives (CEO, Deputy CEO):**
- Strategic planning support
- Cross-reference consultancy recommendations
- Trend identification

**Consultants:**
- Quick access to prior recommendations
- Avoid duplicate work
- Find supporting evidence

---

## 3. Features Specification

### 3.1 P0 Features (Must Have - MVP)

#### 3.1.1 Chat with All Reports
**Description:** RAG-powered chat across entire knowledge base (405 documents)

**User Story:**
> As the Minister, I want to ask questions across all my reports so that I get comprehensive answers with sources.

**Acceptance Criteria:**
- [ ] User can type natural language questions
- [ ] System retrieves from all 405 documents
- [ ] Response includes inline citations [Report Name, p.X]
- [ ] Citations are clickable, expand to show excerpt
- [ ] Response streams in real-time (not waiting for complete)
- [ ] Conversation history preserved
- [ ] Model used: Claude Sonnet 4

**UI Requirements:**
- Clean chat interface similar to ChatGPT
- Citation cards show report title, source, page
- Copy button for responses
- Export conversation as PDF/DOCX

---

#### 3.1.2 Chat with Single Report
**Description:** Focused chat on one specific document

**User Story:**
> As an analyst, I want to deep-dive into a specific report so that I can extract detailed insights.

**Acceptance Criteria:**
- [ ] Smart search to find document (not dropdown with 405 items)
- [ ] Search by title, source, year, keywords
- [ ] Selected document shown in header
- [ ] RAG retrieval limited to selected document
- [ ] Page numbers accurate to source PDF
- [ ] Can switch documents without losing conversation

**UI Requirements:**
- Document selector with search/filter
- Shows recent documents
- Preview card on hover
- Clear indicator of selected document

---

#### 3.1.3 Library Browser
**Description:** Browse and search all reports with filtering

**User Story:**
> As a team member, I want to browse available reports so that I can find relevant materials.

**Acceptance Criteria:**
- [ ] Grid/list view of all reports
- [ ] Filter by: source, year, category
- [ ] Full-text search across titles and content
- [ ] Sort by: date added, year, relevance
- [ ] Pagination (20 per page)
- [ ] Quick stats: total reports, sources breakdown

**Filters:**
- **Source:** BCG, McKinsey, Deloitte, Accenture, KPMG, EY, Capgemini, Google, DCAI, DFF, Government, Think Tank, Other
- **Year:** 2020-2026
- **Category:** Consulting, Research, Policy, News, Digital Government

**UI Requirements:**
- Card-based grid (3 columns desktop)
- Each card shows: title, source logo, year, category tag
- Hover shows quick summary
- Click opens detail page

---

#### 3.1.4 Report Detail Page
**Description:** Comprehensive intelligence view of a single report

**User Story:**
> As the Minister, I want a one-page brief on any report so that I understand it without reading 100 pages.

**Sections:**
1. **Header:** Title, source, year, page count, original PDF link
2. **Executive Summary:** 2-3 paragraph synthesis
3. **Key Findings:** All findings with evidence and page references
4. **Statistics:** All numbers with context
5. **Quotable Language:** Memorable phrases for speeches
6. **Aha Moments:** Contrarian or surprising insights
7. **Recommendations:** Action items from the report
8. **Related Reports:** Links via GraphRAG entities

**Acceptance Criteria:**
- [ ] All sections populated from extraction
- [ ] Each finding/stat/quote links to source page
- [ ] Can download as PDF brief
- [ ] Can chat with this specific report
- [ ] Shows knowledge graph connections

---

#### 3.1.5 Admin Bulk Upload
**Description:** Upload ZIP of MinerU-processed reports

**User Story:**
> As an admin, I want to bulk upload new reports so that the knowledge base stays current.

**Acceptance Criteria:**
- [ ] Upload ZIP file via drag-drop or file picker
- [ ] System extracts and validates MinerU structure
- [ ] Progress indicator for each document
- [ ] Errors clearly reported (which files, why)
- [ ] Automatic processing: RAGFlow + intelligence extraction
- [ ] Email notification when complete
- [ ] Appears in library immediately after processing

**Processing Pipeline:**
1. Extract ZIP
2. Validate MinerU folder structure
3. Parse markdown + content_list.json
4. Upload to RAGFlow (with GraphRAG)
5. Run extraction prompt (Grok Fast)
6. Store metadata in Supabase
7. Populate Data Bank

---

### 3.2 P1 Features (Important)

#### 3.2.1 Meeting Prep Wizard
**Description:** Generate tailored briefing for upcoming meetings

**Input Fields:**
- Meeting type: TV Interview, Bilateral, Conference, Internal Briefing
- Topic/Theme
- Attendees (who you're meeting)
- Duration
- Angle: Supportive, Critical, Balanced, Exploratory

**Output:**
- Relevant background from reports
- Key talking points (3-5)
- Statistics to cite
- Potential questions they might ask
- Suggested framing

---

#### 3.2.2 Talking Points Generator
**Description:** Generate talking points on any topic from knowledge base

**Input:** Topic + Context + Tone
**Output:** 5-7 talking points with supporting evidence

---

#### 3.2.3 News "So What?" Analysis
**Description:** Analyze news articles through UAE AI strategy lens

**User Story:**
> As the Minister, I want to understand what news means for UAE so that I can respond strategically.

**Input:** News article URL or text

**Output:**
1. **Summary:** What happened (2 sentences)
2. **So What?:** Why this matters strategically
3. **UAE Implications:** Specific impact on UAE AI goals
4. **Opportunities:** What UAE could do
5. **Risks:** What to watch out for
6. **Talking Point:** Quotable response if asked

**UAE Strategic Priorities (for analysis):**
- Sovereign AI development
- Regional technology leadership
- Global talent attraction
- Regulatory positioning
- Economic diversification
- Government efficiency

---

#### 3.2.4 Aha Moments Extraction
**Description:** Surface contrarian/surprising insights across all reports

**Automatic extraction during ingestion of:**
- Findings that contradict conventional wisdom
- Unexpected statistics
- Minority viewpoints
- Cross-report contradictions
- Emerging risks/opportunities others miss

---

### 3.3 P2 Features (Nice to Have)

#### 3.3.1 Data Bank
**Description:** Searchable database of extracted intelligence

**Content Types:**
- Statistics (with context)
- Quotes (with speaker, source)
- Key Findings
- Recommendations
- Aha Moments

**Features:**
- Full-text search
- Filter by type, source, topic
- Export selection
- Embed in reports

---

#### 3.3.2 Dashboard
**Description:** At-a-glance intelligence summary

**Widgets:**
- Total reports by source/year
- Recent insights
- Trending topics (from GraphRAG)
- News highlights
- Team activity

---

#### 3.3.3 Cross-Report Comparison
**Description:** Compare recommendations across consultancies

**Example:** "What do BCG, McKinsey, and Deloitte each say about AI governance?"

---

### 3.4 P3 Features (Future)

#### 3.4.1 Digital Minister (Multi-Agent Deep Reasoning)
**Description:** AI consultancy team for complex strategic questions

**Agents:**
1. **RAG Agent:** Searches knowledge hub
2. **Framework Agent:** Applies McKinsey/BCG frameworks
3. **Red Team Agent:** Challenges assumptions
4. **Web Search Agent:** Gets real-time information
5. **Synthesis Agent:** Combines into ministerial brief

**Use Cases:**
- "Red team my proposal for sovereign AI investment"
- "Apply McKinsey 7S framework to our CAIO program"
- "What are the risks of our current AI strategy?"

---

#### 3.4.2 Prompt Enhancement
**Description:** "Enhance" button to improve user queries before sending

**Flow:**
1. User types question
2. Clicks "Enhance"
3. System rewrites for better results
4. User can accept, edit, or revert
5. Send enhanced query

---

## 4. Technical Requirements

### 4.1 Performance
| Metric | Requirement |
|--------|-------------|
| Chat response time | < 3s to first token |
| Search results | < 1s |
| Page load | < 2s |
| Document processing | < 5 min per report |
| Concurrent users | 20 |

### 4.2 Security
- All data encrypted at rest and in transit
- Role-based access control
- Audit logging for all actions
- No data sent to external services except LLM calls
- LLM calls via OpenRouter (privacy-compliant)

### 4.3 Availability
- 99.9% uptime target
- Daily backups
- Disaster recovery plan

### 4.4 Scalability
- Handle 1000+ documents in future
- Support additional team members
- Add new data sources

---

## 5. User Interface Guidelines

### 5.1 Design Principles
1. **Speed:** Every interaction feels instant
2. **Clarity:** No ambiguity, clear feedback
3. **Focus:** One task at a time, no clutter
4. **Trust:** Always show sources, never hallucinate

### 5.2 Visual Design
- **Style:** Modern, professional, minimal
- **Colors:** Dark mode default, light mode option
- **Typography:** Clean sans-serif (Inter or similar)
- **Icons:** Lucide icon set
- **Components:** shadcn/ui library

### 5.3 Key UI Patterns
- **Citations:** Inline [1] with hover preview
- **Loading:** Skeleton states, not spinners
- **Errors:** Toast notifications, not alerts
- **Empty states:** Helpful suggestions

---

## 6. Data Requirements

### 6.1 Initial Data Load
- 405 MinerU-processed reports
- Sources: BCG, McKinsey, Deloitte, Accenture, KPMG, EY, Capgemini, Google, DCAI, DFF, governments, think tanks

### 6.2 Data Quality
- All reports have clean markdown extraction
- Page numbers preserved via content_list.json
- Images extracted but not indexed (future)

### 6.3 Ongoing Data
- New reports added monthly (~10-20)
- News articles added daily
- User conversations stored for context

---

## 7. Integration Requirements

### 7.1 External Services
| Service | Purpose | Integration |
|---------|---------|-------------|
| OpenRouter | LLM access | REST API |
| Firecrawl | News scraping | REST API |
| Tavily | Web search | REST API |

### 7.2 Internal Systems
| System | Purpose | Integration |
|--------|---------|-------------|
| RAGFlow | Vector DB + GraphRAG | REST API |
| Supabase | Auth + Database | SDK |

---

## 8. Launch Plan

### 8.1 Phase 1: MVP (Week 1-2)
- P0 features complete
- 405 reports processed
- Internal team testing

### 8.2 Phase 2: Enhanced (Week 3)
- P1 features added
- Minister demo
- Feedback collection

### 8.3 Phase 3: Production (Week 4)
- Bug fixes from feedback
- Performance optimization
- Full team rollout

### 8.4 Phase 4: Advanced (Month 2+)
- P2/P3 features
- Digital Minister agent
- Mobile optimization

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM hallucinations | High | Medium | Always require citations, validate sources |
| GraphRAG resource usage | Medium | Medium | Process overnight, optimize batch size |
| API rate limits | Medium | Low | Implement backoff, queue system |
| Data quality issues | High | Low | Validation during ingestion |
| User adoption | High | Medium | Training sessions, quick wins |

---

## 10. Success Criteria

### 10.1 Launch Criteria
- [ ] All P0 features functional
- [ ] 405 reports searchable with citations
- [ ] Admin can upload new reports
- [ ] Response time < 3s
- [ ] Zero critical bugs

### 10.2 30-Day Success
- [ ] Minister uses daily
- [ ] 80% team adoption
- [ ] 10+ "Aha moments" surfaced
- [ ] Positive qualitative feedback

### 10.3 90-Day Success
- [ ] Integrated into daily workflow
- [ ] Measurably faster briefing prep
- [ ] Feature requests indicate engagement
- [ ] External interest from other ministries

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| RAG | Retrieval-Augmented Generation - combining search with LLM |
| GraphRAG | RAG enhanced with knowledge graph for entity relationships |
| MinerU | Document processing tool that extracts structured content from PDFs |
| DCAI | Dubai Centre for Artificial Intelligence |
| LLM | Large Language Model |
| Citation | Reference to source document with page number |

---

## Appendix B: User Flows

### B.1 Chat Flow
```
1. User opens /chat
2. Selects mode: Single Doc / All Docs / Digital Minister
3. If Single Doc → Search and select document
4. Types question
5. (Optional) Clicks "Enhance" to improve query
6. Sends message
7. Sees streaming response with citations
8. Clicks citation to see source excerpt
9. Continues conversation or starts new
```

### B.2 Library Flow
```
1. User opens /library
2. Sees grid of all reports
3. Applies filters (source, year, category)
4. Searches by keyword
5. Clicks report card
6. Opens report detail page
7. Reviews sections (summary, findings, stats)
8. Clicks "Chat with this report"
9. Continues in single-doc chat mode
```

### B.3 News Analysis Flow
```
1. User opens /news
2. Sees feed of analyzed articles
3. OR pastes new URL
4. System scrapes article (Firecrawl)
5. Runs "So What?" analysis
6. Displays structured analysis
7. User can save or share
```
