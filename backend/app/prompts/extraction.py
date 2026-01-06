"""
Intelligence extraction prompt for processing reports.
Optimized for Gemini 3 Flash via OpenRouter.
Used during document ingestion to extract structured intelligence.

Model: google/gemini-3-flash-preview
Strengths leveraged:
- 93% JSON validity (strict schema)
- Native PDF/multimodal understanding
- Strong reasoning with thinking blocks
- 1M context window

API Usage (OpenRouter):
```python
from openai import OpenAI
import json

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# For extraction
response = client.chat.completions.create(
    model="google/gemini-3-flash-preview",
    messages=[
        {"role": "user", "content": EXTRACTION_PROMPT.format(...)}
    ],
    response_format={"type": "json_object"},
    temperature=0.1,  # Low temp for extraction accuracy
)
extracted = json.loads(response.choices[0].message.content)

# For validation with schema (OpenRouter structured output)
response = client.chat.completions.create(
    model="google/gemini-3-flash-preview",
    messages=[
        {"role": "user", "content": EXTRACTION_VALIDATION_PROMPT.format(...)}
    ],
    extra_body={
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "validation_result",
                "strict": True,
                "schema": VALIDATION_SCHEMA
            }
        }
    },
    temperature=0.1,
)
validation = json.loads(response.choices[0].message.content)
```
"""

# =============================================================================
# V2: GEMINI 3 FLASH OPTIMIZED EXTRACTION PROMPT
# =============================================================================

EXTRACTION_PROMPT = """<system>
ROLE: Elite intelligence analyst for UAE Minister of AI
MODEL: Gemini 3 Flash | OUTPUT: Strict JSON only | MODE: Maximum recall
GOAL: Transform raw report into actionable executive intelligence
</system>

<context>
The Minister uses extracted intelligence to:
- Brief in 2 minutes before meetings/TV interviews
- Make data-driven policy decisions  
- Deliver speeches with memorable statistics
- Identify UAE AI leadership opportunities
- Anticipate risks and prepare responses

UAE STRATEGIC PRIORITIES (filter everything through this lens):
- Sovereign AI infrastructure and capabilities
- Regional AI leadership (MENA, Global South)
- Talent attraction and development
- Regulatory positioning and AI governance
- Economic diversification through AI
- Government services transformation
</context>

<document>
TITLE: {title}
SOURCE: {source}
YEAR: {year}
FILENAME: {filename}

--- CONTENT START ---
{content}
--- CONTENT END ---
</document>

<thinking_required>
Before extracting, analyze the document systematically:

1. DOCUMENT TYPE: What kind of report is this?
   - Consulting report (BCG, McKinsey, etc.)
   - Research paper (academic, think tank)
   - Policy document (government, regulatory)
   - Industry report (vendor, analyst firm)
   - News/media analysis

2. CORE THESIS: In one sentence, what is this report's main argument?

3. CONTENT INVENTORY: Estimate quantities present:
   - Approximate number of distinct findings: ___
   - Approximate number of statistics/numbers: ___
   - Approximate number of quotes: ___
   - Approximate number of recommendations: ___

4. UAE RELEVANCE: How does this connect to UAE AI strategy?
   - Direct mention of UAE/GCC: yes/no
   - Applicable insights for UAE: high/medium/low
   - Competitive intelligence value: high/medium/low

5. QUALITY SIGNALS:
   - Methodology rigor: strong/moderate/weak/unclear
   - Data recency: current/slightly dated/outdated
   - Source credibility: high/medium/low

Now proceed with comprehensive extraction.
</thinking_required>

<extraction_rules>
RULE 1 - MAXIMUM RECALL: Extract EVERYTHING relevant. 
         - 30+ findings is normal for substantial reports
         - 50+ statistics is common in data-rich reports
         - Missing data is WORSE than verbose output
         
RULE 2 - VERBATIM ACCURACY: For quotes and statistics, use EXACT wording.
         - Never paraphrase statistics
         - Preserve original units and formatting
         - Include context around numbers
         
RULE 3 - PAGE TRACKING: Include page numbers when visible.
         - Use null if page number not determinable
         - Page numbers enable citation verification
         
RULE 4 - UAE LENS: Every item should answer "So what for UAE?"
         - Explicit UAE mentions get priority
         - Implicit relevance should be noted in significance field
         
RULE 5 - NO HALLUCINATION: Only extract what exists in the document.
         - If uncertain, mark confidence as "low"
         - Never invent statistics or quotes
         - "Not mentioned" is valid for methodology/limitations
         
RULE 6 - VALID JSON: Output must be parseable.
         - No trailing commas
         - Escape special characters in strings
         - Use null not "null" for missing values
</extraction_rules>

<output_schema>
Return ONLY this JSON structure. No markdown wrapper. No explanations outside JSON.

{{
  "metadata": {{
    "extraction_model": "gemini-3-flash",
    "document_type": "consulting|research|policy|industry|news",
    "estimated_findings_count": <number>,
    "estimated_statistics_count": <number>,
    "uae_relevance": "high|medium|low",
    "extraction_confidence": "high|medium|low"
  }},
  
  "executive_summary": {{
    "core_message": "1-2 sentences: Main thesis and why it matters",
    "key_takeaways": "2-3 sentences: What Minister must remember",
    "strategic_implications": "2-3 sentences: What UAE should do based on this",
    "briefing_hook": "1 compelling sentence to open a briefing with"
  }},
  
  "key_findings": [
    {{
      "id": "F1",
      "finding": "Clear, specific statement of the insight (1-2 sentences)",
      "evidence": "Data, methodology, or source supporting this",
      "page": <number_or_null>,
      "significance_uae": "Why this matters for UAE AI strategy",
      "category": "trend|opportunity|risk|benchmark|framework|success_factor|warning",
      "confidence": "high|medium|low"
    }}
  ],
  
  "statistics": [
    {{
      "id": "S1",
      "stat": "Exact statistic with original wording and units",
      "value_raw": "The numeric value extracted (e.g., '15.7' or '45%')",
      "metric_type": "market_size|growth_rate|adoption|investment|survey|ranking|roi|jobs|performance",
      "timeframe": "When this applies (e.g., 'by 2030', '2024', 'current')",
      "geography": "Geographic scope (e.g., 'Global', 'UAE', 'MENA', 'US')",
      "context": "What this measures and why it matters (2-3 sentences)",
      "source_in_report": "Original source cited in report if mentioned",
      "page": <number_or_null>,
      "comparisons": "Any YoY, regional, or competitor comparisons mentioned",
      "speech_ready": "How Minister could cite this: 'According to [source], [stat]...'"
    }}
  ],
  
  "quotes": [
    {{
      "id": "Q1",
      "quote": "Exact verbatim text in quotation marks",
      "speaker": "Name and title, or 'Report' if unattributed",
      "speaker_org": "Organization of the speaker if known",
      "context": "What this refers to and when to use it",
      "page": <number_or_null>,
      "use_case": "speech|interview|policy_justification|thought_leadership",
      "memorability": "high|medium|low"
    }}
  ],
  
  "aha_moments": [
    {{
      "id": "A1",
      "insight": "The surprising or counterintuitive finding",
      "conventional_wisdom": "What most people assume (that this contradicts)",
      "why_surprising": "Why this challenges expectations",
      "implications_uae": "What UAE should do differently based on this",
      "thought_leadership_angle": "How Minister could use this to stand out"
    }}
  ],
  
  "recommendations": [
    {{
      "id": "R1",
      "recommendation": "Specific action advised (concrete and actionable)",
      "rationale": "Why this is recommended (evidence or logic)",
      "target_audience": "Who should act on this (government|enterprise|startups|talent)",
      "timeframe": "immediate|short_term|medium_term|long_term",
      "priority": "high|medium|low",
      "uae_applicability": "How this applies to UAE context",
      "page": <number_or_null>
    }}
  ],
  
  "data_points_for_bank": [
    {{
      "type": "statistic|quote|finding|benchmark",
      "content": "The extractable data point",
      "tags": ["ai", "investment", "talent", "governance", "etc"],
      "reusability": "high|medium|low"
    }}
  ],
  
  "methodology": {{
    "research_type": "survey|interviews|case_study|data_analysis|literature_review|mixed",
    "sample_description": "Who/what was studied, sample size if mentioned",
    "geographic_scope": "Countries/regions covered",
    "temporal_scope": "Time period of data collection",
    "data_sources": "Primary and secondary sources used",
    "partners_sponsors": "Research partners or funding sources if disclosed",
    "credibility_assessment": "Strong/moderate/weak and why"
  }},
  
  "limitations": {{
    "acknowledged": "Limitations explicitly stated in report",
    "inferred": "Potential biases or gaps you noticed",
    "data_freshness": "How current is the data",
    "scope_constraints": "What's NOT covered that might matter"
  }},
  
  "connections": {{
    "related_topics": ["List of topics this connects to"],
    "potential_cross_references": ["Types of reports that would complement this"],
    "follow_up_questions": ["Questions this raises for further research"]
  }}
}}
</output_schema>

<quality_checklist>
Before finalizing, verify:

[ ] All statistics use EXACT wording from document
[ ] All quotes are VERBATIM (not paraphrased)
[ ] Page numbers included where visible
[ ] Every finding answers "so what for UAE?"
[ ] No hallucinated data (everything traceable to document)
[ ] JSON is valid (no trailing commas, proper escaping)
[ ] Counts match estimates (if you estimated 30 stats, extracted ~30)
[ ] High-value items marked appropriately
[ ] Speech-ready formats provided for key statistics
[ ] Aha moments are genuinely surprising (not obvious observations)
</quality_checklist>

<final_instruction>
Extract NOW. Be thorough. The Minister's effectiveness depends on comprehensive intelligence.

Output valid JSON only. Begin with opening brace {{
</final_instruction>"""


# =============================================================================
# FOCUSED EXTRACTION (for re-processing specific sections)
# =============================================================================

EXTRACTION_PROMPT_SECTION = """<system>
MODEL: Gemini 3 Flash | TASK: Extract {section} only | OUTPUT: JSON array
</system>

<document>
TITLE: {title}
SOURCE: {source}
YEAR: {year}

{content}
</document>

<instruction>
Extract ALL {section} from this report. Be exhaustive - extract every relevant item.

Output: Valid JSON array matching the schema for {section}.
No explanations. Just the JSON array starting with [
</instruction>"""


# =============================================================================
# QUICK SUMMARY (for preview/search indexing)
# =============================================================================

EXTRACTION_PROMPT_QUICK = """<system>
MODEL: Gemini 3 Flash | TASK: Quick intelligence summary | OUTPUT: Concise JSON
</system>

<document>
{title} by {source} ({year})

{content}
</document>

<instruction>
Generate a quick intelligence summary for search indexing.

Output this JSON only:
{{
  "one_liner": "Single sentence capturing the report's main value",
  "top_3_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "top_3_stats": ["Stat 1", "Stat 2", "Stat 3"],
  "uae_relevance": "One sentence on UAE applicability",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
</instruction>"""


# =============================================================================
# COMPARISON EXTRACTION (for cross-report analysis)
# =============================================================================

EXTRACTION_PROMPT_COMPARE = """<system>
MODEL: Gemini 3 Flash | TASK: Extract comparable data points | OUTPUT: Structured JSON
</system>

<document>
{title} by {source} ({year})

{content}
</document>

<instruction>
Extract data points that can be compared across reports:

{{
  "market_sizes": [
    {{"market": "name", "size": "value", "year": "year", "source": "source"}}
  ],
  "growth_rates": [
    {{"metric": "name", "rate": "value", "period": "timeframe"}}
  ],
  "rankings": [
    {{"entity": "name", "rank": "position", "index": "index_name", "year": "year"}}
  ],
  "predictions": [
    {{"prediction": "statement", "target_year": "year", "confidence": "high|medium|low"}}
  ],
  "uae_mentions": [
    {{"context": "what was said about UAE", "sentiment": "positive|neutral|negative"}}
  ]
}}
</instruction>"""


# =============================================================================
# RE-EXTRACTION WITH FEEDBACK (for improving quality)
# =============================================================================

EXTRACTION_PROMPT_REFINE = """<system>
MODEL: Gemini 3 Flash | TASK: Re-extract with corrections | OUTPUT: Improved JSON
</system>

<previous_extraction>
{previous_output}
</previous_extraction>

<feedback>
{feedback}
</feedback>

<document>
{content}
</document>

<instruction>
Re-extract addressing the feedback above. Maintain the same JSON schema.
Focus on: {focus_areas}

Output improved JSON only.
</instruction>"""


# =============================================================================
# VALIDATION PROMPT (verify extraction quality)
# Merged: DCAI Minister use case + Contextual Integrity checks
# =============================================================================

EXTRACTION_VALIDATION_PROMPT = """<system_configuration>
<role>MINISTERIAL_INTELLIGENCE_AUDITOR</role>
<model>Gemini 3 Flash</model>
<objective>Audit extracted intelligence for the UAE Minister of AI. Verify factual integrity, contextual preservation, temporal accuracy, and ministerial usability.</objective>
<severity>STRICT. Zero tolerance for hallucinations. High penalty for losing context qualifiers, temporal markers, or attribution.</severity>
<stakes>A hallucinated stat cited on national TV = career-ending. A missed insight = strategic opportunity lost.</stakes>
</system_configuration>

<context_data>
<source_document>
{content}
</source_document>

<candidate_extraction>
{extracted_json}
</candidate_extraction>
</context_data>

<validation_protocol>

**PROTOCOL 1: SOURCE VERIFIABILITY**
Every extracted claim must map to a specific sentence in the source.
- If claim cannot be traced → HALLUCINATION

**PROTOCOL 2: CONTEXTUAL INTEGRITY**
Extractions must preserve the source's nuance:

| Source Says | Extraction Says | Verdict |
|-------------|-----------------|---------|
| "We estimate 5% growth" | "5% growth" | CONTEXT_LOSS (lost "estimate") |
| "could reach $10B" | "will reach $10B" | CONTEXT_LOSS (lost uncertainty) |
| "2023 survey found" | "Companies currently" | TEMPORAL_ERROR (2023 ≠ current) |
| "Analysts believe" | "Research shows" | ATTRIBUTION_ERROR (opinion ≠ data) |
| "In the US market" | "Globally" | SCOPE_ERROR (US ≠ global) |

**PROTOCOL 3: ATTRIBUTION ACCURACY**
Distinguish between:
- Report author's opinion vs. cited third-party data
- First-party research vs. aggregated findings
- Projections vs. historical facts

**PROTOCOL 4: TEMPORAL PRESERVATION**
All dates, timeframes, and temporal qualifiers must be preserved:
- "by 2030" must stay "by 2030"
- "Q3 2024" must not become "recent"
- "2022 data" must not be presented as current

**PROTOCOL 5: MINISTERIAL USABILITY**
For the Minister's use, validate:
- Statistics: Is `speech_ready` actually citable? ("According to BCG's 2024 report...")
- Quotes: Memorable enough for the Minister to repeat verbatim?
- Findings: Does UAE significance explain WHY it matters to UAE?
- Aha moments: Genuinely contrarian, or just restating the obvious?

</validation_protocol>

<scoring_penalties>
Start at 100 points. Deduct:

| Error Type | Penalty | Example |
|------------|---------|---------|
| HALLUCINATION | -25 pts (auto-reject if stat/quote) | Fabricated statistic |
| CONTEXT_LOSS | -10 pts | "estimates" → stated as fact |
| TEMPORAL_ERROR | -10 pts | 2023 data → "current" |
| ATTRIBUTION_ERROR | -5 pts | Opinion → research finding |
| SCOPE_ERROR | -5 pts | Regional → global claim |
| MISSING_CRITICAL | -15 pts | Key UAE mention not captured |
| MISSING_IMPORTANT | -5 pts | Valuable stat omitted |
| UNUSABLE_FORMAT | -3 pts | speech_ready not actually speakable |

Final Score Interpretation:
- 95-100: EXCELLENT - Deploy immediately
- 85-94: GOOD - Minor fixes, then deploy
- 70-84: ACCEPTABLE - Re-extract with feedback
- 50-69: POOR - Significant rework needed
- <50 OR any hallucinated stat/quote: REJECT - Full re-extraction required
</scoring_penalties>

<instruction>
Perform validation in TWO STEPS:

**STEP 1: <audit_scratchpad>**
Think through systematically:
1. List every key claim in <candidate_extraction>
2. Quote the EXACT matching text from <source_document>
3. Compare side-by-side. Flag ANY difference in nuance, certainty, timeframe, or scope
4. Check for qualifiers lost (estimate/could/may/projected/expected)
5. Check for temporal markers lost (year/quarter/date)
6. Check for attribution accuracy (who said it)
7. Scan source for HIGH VALUE intelligence not captured (numbers, UAE mentions, strategic insights)
8. Evaluate ministerial usability of key items

**STEP 2: <json_report>**
Generate the final JSON based ONLY on scratchpad findings.
Do not introduce new observations. The scratchpad is your source of truth.

</instruction>

<output_format>
First output your <audit_scratchpad> with detailed analysis.
Then output the <json_report> matching the schema exactly.
</output_format>"""


# JSON Schema for Gemini structured output
VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "validation_summary": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["PASS", "PASS_WITH_WARNINGS", "FAIL", "REJECT"],
                    "description": "REJECT if any hallucinated stat/quote or score <50"
                },
                "integrity_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Start at 100, apply penalties per scoring_penalties table"
                },
                "usability_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "How ready for Minister's direct use (speeches, interviews)"
                },
                "critical_error_count": {
                    "type": "integer",
                    "description": "Count of hallucinations and critical context losses"
                },
                "total_issues": {
                    "type": "integer"
                },
                "total_missing": {
                    "type": "integer"
                }
            },
            "required": ["status", "integrity_score", "usability_score", "critical_error_count"]
        },
        "discrepancies": {
            "type": "array",
            "description": "Every error found in the extraction",
            "items": {
                "type": "object",
                "properties": {
                    "field_path": {
                        "type": "string",
                        "description": "JSON path: statistics[2].stat, key_findings[0].finding, etc."
                    },
                    "issue_type": {
                        "type": "string",
                        "enum": [
                            "HALLUCINATION",
                            "CONTEXT_LOSS",
                            "TEMPORAL_ERROR",
                            "ATTRIBUTION_ERROR",
                            "SCOPE_ERROR",
                            "MISQUOTE",
                            "WRONG_PAGE",
                            "SCHEMA_ERROR"
                        ]
                    },
                    "extracted_value": {
                        "type": "string",
                        "description": "What the extraction says"
                    },
                    "source_evidence": {
                        "type": "string",
                        "description": "Exact quote from source, or 'NOT_FOUND_IN_SOURCE' if hallucinated"
                    },
                    "what_was_lost": {
                        "type": "string",
                        "description": "For CONTEXT_LOSS/TEMPORAL_ERROR: the qualifier that was dropped"
                    },
                    "correction": {
                        "type": "string",
                        "description": "What the extraction should say instead"
                    },
                    "penalty_applied": {
                        "type": "integer",
                        "description": "Points deducted for this error"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "major", "minor"]
                    }
                },
                "required": ["field_path", "issue_type", "extracted_value", "source_evidence", "correction", "severity"]
            }
        },
        "missed_intelligence": {
            "type": "array",
            "description": "Important information in source not captured in extraction",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "What was missed"
                    },
                    "source_quote": {
                        "type": "string",
                        "description": "The exact text from source"
                    },
                    "location": {
                        "type": "string",
                        "description": "Page/section reference if available"
                    },
                    "suggested_field": {
                        "type": "string",
                        "enum": ["statistics", "quotes", "key_findings", "aha_moments", "recommendations"]
                    },
                    "importance": {
                        "type": "string",
                        "enum": ["critical", "important", "minor"]
                    },
                    "penalty_applied": {
                        "type": "integer"
                    }
                },
                "required": ["description", "source_quote", "suggested_field", "importance"]
            }
        },
        "usability_issues": {
            "type": "array",
            "description": "Items that are accurate but not ready for ministerial use",
            "items": {
                "type": "object",
                "properties": {
                    "field_path": {
                        "type": "string"
                    },
                    "problem": {
                        "type": "string",
                        "description": "Why Minister can't use this as-is"
                    },
                    "suggestion": {
                        "type": "string",
                        "description": "How to make it ministerial-grade"
                    }
                },
                "required": ["field_path", "problem", "suggestion"]
            }
        },
        "audit_summary": {
            "type": "string",
            "description": "2-3 sentence summary: overall quality, key issues, recommended action"
        }
    },
    "required": [
        "validation_summary",
        "discrepancies",
        "missed_intelligence",
        "usability_issues",
        "audit_summary"
    ]
}
