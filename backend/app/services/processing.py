"""
Document processing service for ingesting MinerU-processed reports.
Handles extraction, RAGFlow upload, and metadata storage.
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ProcessingError, ExtractionError
from app.services.ragflow import get_ragflow_client
from app.services.llm import get_llm_service
from app.services.supabase import get_supabase_service
from app.prompts.extraction import EXTRACTION_PROMPT

logger = get_logger(__name__)


class ProcessingService:
    """Service for processing and ingesting documents."""
    
    def __init__(self):
        self.ragflow = get_ragflow_client()
        self.llm = get_llm_service()
        self.supabase = get_supabase_service()
        self.dataset_id: Optional[str] = None
    
    async def ensure_dataset(self, name: str = "DCAI Intelligence Hub") -> str:
        """Ensure the main dataset exists, create if needed."""
        if self.dataset_id:
            return self.dataset_id
        
        try:
            datasets = await self.ragflow.list_datasets()
            for ds in datasets:
                if ds.get("name") == name:
                    self.dataset_id = ds["id"]
                    logger.info(f"Using existing dataset: {name} ({self.dataset_id})")
                    return self.dataset_id
            
            # Create new dataset
            result = await self.ragflow.create_dataset(
                name=name,
                description="Intelligence reports for UAE Minister of AI",
                language="English",
                chunk_method="naive"
            )
            self.dataset_id = result["id"]
            logger.info(f"Created dataset: {name} ({self.dataset_id})")
            return self.dataset_id
            
        except Exception as e:
            logger.error(f"Failed to ensure dataset: {e}")
            raise ProcessingError(f"Dataset setup failed: {e}")
    
    async def process_mineru_folder(
        self,
        folder_path: str,
        force_reprocess: bool = False
    ) -> dict:
        """
        Process a single MinerU output folder.
        
        Expected structure:
        folder_name/vlm/
        ├── folder_name.md
        ├── folder_name_content_list.json
        └── folder_name_origin.pdf
        
        Returns:
            Dict with report_id, status, and any errors
        """
        folder = Path(folder_path)
        folder_name = folder.name
        
        # Find the vlm subdirectory
        vlm_path = folder / "vlm"
        if not vlm_path.exists():
            vlm_path = folder  # Some might not have vlm subfolder
        
        # Find the markdown file
        md_files = list(vlm_path.glob("*.md"))
        if not md_files:
            raise ProcessingError(f"No markdown file found in {folder_path}", folder_name)
        
        md_file = md_files[0]
        base_name = md_file.stem
        
        # Read markdown content
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = md_file.read_text(encoding="latin-1")
        
        if not content.strip():
            raise ProcessingError(f"Empty markdown file: {md_file}", folder_name)
        
        # Read content list for page mapping
        content_list_file = vlm_path / f"{base_name}_content_list.json"
        content_list = None
        if content_list_file.exists():
            try:
                content_list = json.loads(content_list_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not read content list: {e}")
        
        # Check if already processed
        existing = await self._find_existing_report(folder_name)
        if existing and not force_reprocess:
            logger.info(f"Report already exists: {folder_name}")
            return {
                "report_id": existing["id"],
                "status": "already_exists",
                "title": existing.get("title", folder_name)
            }
        
        # Parse title and metadata from content
        title = self._extract_title(content, folder_name)
        source, year, category = self._infer_metadata(folder_name, content)
        
        logger.info(f"Processing: {title}")
        
        # Ensure dataset exists
        dataset_id = await self.ensure_dataset()
        
        # Upload to RAGFlow
        ragflow_doc_id = None
        try:
            doc_result = await self.ragflow.upload_document_text(
                dataset_id=dataset_id,
                name=f"{folder_name}.md",
                text=content
            )
            ragflow_doc_id = doc_result.get("id") or doc_result.get("document_id")
        except Exception as e:
            logger.error(f"RAGFlow upload failed: {e}")
        
        # Trigger parsing (separate try block - don't fail if parsing trigger fails)
        # Many RAGFlow versions auto-parse on upload, so this is optional
        if ragflow_doc_id:
            try:
                await self.ragflow.parse_documents(
                    dataset_id=dataset_id,
                    document_ids=[ragflow_doc_id]
                )
            except Exception as e:
                logger.warning(f"RAGFlow parse trigger failed (may auto-parse): {e}")
        
        # Extract intelligence using LLM
        extracted = await self._extract_intelligence(
            content=content,
            title=title,
            source=source,
            year=str(year) if year else "Unknown"
        )
        
        # Create or update report in database
        # Note: DB columns may differ from our schema - mapping both variants
        report_data = {
            "title": title,
            "source": source,
            "source_organization": source,  # DB column name
            "year": year,
            "category": category,
            "filename": folder_name,
            "original_filename": folder_name,
            "mineru_folder": str(folder_path),
            "ragflow_doc_id": ragflow_doc_id,
            "executive_summary": extracted.get("executive_summary", ""),
            "key_findings": json.dumps(extracted.get("key_findings", [])),
            "statistics": json.dumps(extracted.get("statistics", [])),
            "quotes": json.dumps(extracted.get("quotes", [])),
            "aha_moments": json.dumps(extracted.get("aha_moments", [])),
            "recommendations": json.dumps(extracted.get("recommendations", [])),
            "methodology": extracted.get("methodology", ""),
            "limitations": extracted.get("limitations", "")
        }
        
        if existing:
            report = await self.supabase.update_report(UUID(existing["id"]), report_data)
            report_id = existing["id"]
            status = "reprocessed"
        else:
            report = await self.supabase.create_report(report_data)
            report_id = report["id"]
            status = "processed"
        
        # Add items to data bank
        await self._populate_databank(UUID(report_id), extracted)
        
        logger.info(f"Completed processing: {title} ({status})")
        
        return {
            "report_id": report_id,
            "status": status,
            "title": title,
            "ragflow_doc_id": ragflow_doc_id
        }
    
    async def process_all_reports(
        self,
        base_path: Optional[str] = None,
        max_concurrent: int = 5,
        force_reprocess: bool = False
    ) -> dict:
        """
        Process all MinerU report folders.
        
        Returns:
            Summary with counts of processed, skipped, failed
        """
        base = Path(base_path or settings.mineru_reports_path)
        
        if not base.exists():
            raise ProcessingError(f"Reports path does not exist: {base}")
        
        # Find all report folders
        folders = [f for f in base.iterdir() if f.is_dir()]
        total = len(folders)
        
        logger.info(f"Found {total} report folders to process")
        
        results = {
            "total": total,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(folder: Path):
            async with semaphore:
                try:
                    result = await self.process_mineru_folder(
                        str(folder),
                        force_reprocess=force_reprocess
                    )
                    if result["status"] == "already_exists":
                        results["skipped"] += 1
                    else:
                        results["processed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "folder": folder.name,
                        "error": str(e)
                    })
                    logger.error(f"Failed to process {folder.name}: {e}")
        
        # Run all processing tasks
        await asyncio.gather(*[process_one(f) for f in folders])
        
        logger.info(
            f"Processing complete: {results['processed']} processed, "
            f"{results['skipped']} skipped, {results['failed']} failed"
        )
        
        return results
    
    async def _extract_intelligence(
        self,
        content: str,
        title: str,
        source: str = "Unknown",
        year: str = "Unknown"
    ) -> dict:
        """
        Extract intelligence from document content using Gemini 3 Flash.
        
        Uses the optimized EXTRACTION_PROMPT with:
        - Thinking block for document analysis
        - Strict JSON schema
        - UAE ministerial lens
        - Comprehensive extraction (all findings, all stats)
        """
        try:
            # Gemini 3 Flash has 1M context, but we cap for cost/speed
            max_chars = 500000  # ~125K tokens, safe for 1M context
            truncated = False
            if len(content) > max_chars:
                content = content[:max_chars]
                truncated = True
            
            prompt = EXTRACTION_PROMPT.format(
                title=title,
                source=source,
                year=year,
                filename=title,
                content=content
            )
            
            if truncated:
                prompt += "\n\n[NOTE: Document was truncated due to length. Extract from available content.]"
            
            response = await self.llm.complete(
                messages=[{"role": "user", "content": prompt}],
                model_type="fast",  # Now Gemini 3 Flash
                temperature=0.1,  # Low temp for extraction accuracy
                max_tokens=16384,  # Increased for comprehensive extraction
                json_mode=True
            )
            
            # Parse JSON response
            text = response.content.strip()
            
            # Clean markdown wrapper if present
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first and last lines (``` markers)
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                if text.startswith("json"):
                    text = text[4:].strip()
            
            extracted = json.loads(text)
            
            # Handle new prompt structure (executive_summary is now an object)
            if isinstance(extracted.get("executive_summary"), dict):
                # Flatten executive_summary object to string for DB
                es = extracted["executive_summary"]
                extracted["executive_summary"] = (
                    f"{es.get('core_message', '')}\n\n"
                    f"{es.get('key_takeaways', '')}\n\n"
                    f"{es.get('strategic_implications', '')}"
                ).strip()
                
                # Store briefing hook separately if present
                if es.get("briefing_hook"):
                    extracted["briefing_hook"] = es["briefing_hook"]
            
            logger.info(
                f"Extraction complete for {title}",
                findings=len(extracted.get("key_findings", [])),
                statistics=len(extracted.get("statistics", [])),
                quotes=len(extracted.get("quotes", [])),
                model=response.model
            )
            
            return extracted
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}", title=title)
            return self._empty_extraction()
        except Exception as e:
            logger.error(f"Extraction failed: {e}", title=title)
            return self._empty_extraction()
    
    def _empty_extraction(self) -> dict:
        """Return empty extraction structure."""
        return {
            "executive_summary": "",
            "key_findings": [],
            "statistics": [],
            "quotes": [],
            "aha_moments": [],
            "recommendations": []
        }
    
    async def _find_existing_report(self, folder_name: str) -> Optional[dict]:
        """Check if a report already exists for this folder."""
        try:
            # Query directly by filename field (exact match)
            report = await self.supabase.get_report_by_filename(folder_name)
            if report:
                return report
            return None
        except Exception as e:
            logger.warning(f"Error finding existing report: {e}")
            return None
    
    def _extract_title(self, content: str, fallback: str) -> str:
        """Extract title from markdown content."""
        lines = content.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line and not line.startswith("#") and len(line) > 10:
                # First substantial line might be title
                if len(line) < 200:
                    return line
        return fallback.replace("_", " ").replace("-", " ").title()
    
    def _infer_metadata(
        self,
        folder_name: str,
        content: str
    ) -> tuple[str, Optional[int], str]:
        """Infer source, year, and category from folder name and content."""
        import re
        folder_lower = folder_name.lower()
        
        # Check for date-prefixed news articles first (YYYY-MM-DD_...)
        date_prefix_match = re.match(r"^20\d{2}-\d{2}-\d{2}_", folder_name)
        if date_prefix_match:
            # Extract year from date prefix
            year = int(folder_name[:4])
            # Determine source from content keywords
            if "dubai" in folder_lower:
                source = "Dubai News"
            elif "uae" in folder_lower or "emirates" in folder_lower:
                source = "UAE News"
            else:
                source = "News Article"
            return source, year, "News"
        
        # Comprehensive source detection map
        # Order matters - more specific matches first
        source_map = {
            # Major Consulting Firms
            "bcg": "BCG",
            "mckinsey": "McKinsey",
            "deloitte": "Deloitte",
            "accenture": "Accenture",
            "kpmg": "KPMG",
            "ey_": "EY",  # Use ey_ to avoid matching "they", "grey", etc.
            "pwc": "PwC",
            "capgemini": "Capgemini",
            "bain": "Bain & Company",
            "cognizant": "Cognizant",
            "heidrick": "Heidrick & Struggles",
            
            # Tech Companies
            "google": "Google",
            "microsoft": "Microsoft",
            "amazon": "Amazon",
            "aws": "AWS",
            "cisco": "Cisco",
            "anthropic": "Anthropic",
            
            # Think Tanks & Research
            "atlantic": "Atlantic Council",
            "brookings": "Brookings Institution",
            "arxiv": "arXiv",
            "ai_now": "AI Now Institute",
            "future_of_life": "Future of Life Institute",
            "future_of_humanity": "Future of Humanity Institute",
            "eon_institute": "Eon Institute",
            "fii": "Future Investment Initiative",
            "convergence": "Convergence AI",
            
            # International Organizations
            "world_bank": "World Bank",
            "un_": "United Nations",
            "un ": "United Nations",
            "imf": "IMF",
            "wef": "World Economic Forum",
            "oecd": "OECD",
            "g7": "G7",
            "eu_": "European Union",
            "european_parliament": "European Parliament",
            "bmz": "BMZ Germany",
            "bond": "BOND",
            "clad": "CLAD",
            "global_solutions": "Global Solutions Initiative",
            "nato": "NATO",
            "unesco": "UNESCO",
            "who": "WHO",
            "itc": "International Trade Centre",
            
            # UAE/Dubai Entities
            "dcai": "DCAI",
            "dff": "DFF",
            "dubai_future": "Dubai Future Foundation",
            "dubai_health": "Dubai Health Authority",
            "dubai_government": "Dubai Government",
            "dubai_state": "Dubai Government",
            "digital_dubai": "Digital Dubai",
            "mbrsg": "MBRSG",
            "abu_dhabi": "Abu Dhabi Government",
            
            # Regional Organizations
            "dco": "DCO",
            "arab_reform": "Arab Reform Initiative",
            "cipit": "CIPIT",
            "asia_group": "The Asia Group",
            
            # Government Agencies
            "white_house": "US White House",
            "dhs": "US DHS",
            "dia": "US DIA",
            "dod": "US DoD",
            "cisa": "US CISA",
            "california": "State of California",
            "federal": "US Federal Government",
            "japan": "Japan Government",
            "india_": "India Government",
            "house_": "US House of Representatives",
            "omb_": "US OMB",
            "odni_": "US ODNI",
            "qatar": "Qatar Government",
            "new_zealand": "New Zealand Government",
            
            # Standards Bodies
            "iso_": "ISO",
            "itu_": "ITU",
            "iea_": "IEA",
            
            # More Consulting
            "kearney": "Kearney",
            "roland_berger": "Roland Berger",
            "oliver_wyman": "Oliver Wyman",
            
            # Academic/Research Journals
            "jair_": "JAIR",
            "itsa_": "ITSA",
            
            # Research & Industry
            "idc": "IDC",
            "gartner": "Gartner",
            "forrester": "Forrester",
            "aaai": "AAAI",
            "equalai": "EqualAI",
            "appliedai": "AppliedAI",
            "cognitivepath": "CognitivePath",
            "granicus": "Granicus",
            "dentons": "Dentons",
            "nist": "NIST",
            "ieee": "IEEE",
            
            # Academic
            "mit": "MIT",
            "stanford": "Stanford",
            "harvard": "Harvard",
            "oxford": "Oxford",
            "cambridge": "Cambridge",
            
            # More Tech Companies
            "openai": "OpenAI",
            "meta": "Meta",
            "nvidia": "NVIDIA",
            "ibm": "IBM",
            "salesforce": "Salesforce",
            "oracle": "Oracle",
            "adobe": "Adobe",
            "intel": "Intel",
            
            # Fallback UAE mentions
            "uae": "UAE Government",
            "dubai": "Dubai Government",
            "emirates": "UAE Government",
        }
        
        source = "Unknown"
        for key, value in source_map.items():
            if key in folder_lower:
                source = value
                break
        
        # Year detection
        year = None
        year_match = re.search(r"20(1\d|2\d)", folder_name)
        if year_match:
            year = int(year_match.group())
        
        # Category detection - source-based categories take precedence
        category = "Research"
        consulting_firms = ["BCG", "McKinsey", "Deloitte", "Accenture", "KPMG", "EY", "PwC", 
                          "Bain & Company", "Cognizant", "Capgemini", "Heidrick & Struggles"]
        government_sources = ["DCAI", "DFF", "Dubai Government", "UAE Government", "US DHS", 
                            "US DIA", "US DoD", "US CISA", "Abu Dhabi Government", "Dubai Future Foundation",
                            "Dubai Health Authority", "Digital Dubai", "State of California", "US Federal Government"]
        think_tanks = ["Atlantic Council", "Brookings Institution", "AI Now Institute", 
                      "Future of Life Institute", "Future of Humanity Institute", "Eon Institute"]
        news_sources = ["Dubai News", "UAE News", "News Article"]
        
        # Priority 1: Source-specific categories (most reliable)
        if source in consulting_firms:
            category = "Consulting"
        elif source in government_sources:
            category = "Policy"
        elif source in think_tanks:
            category = "Think Tank"
        elif source in news_sources:
            category = "News"
        elif source == "arXiv":
            category = "Academic"
        # Priority 2: Keyword-based (fallback for Unknown sources)
        elif any(x in folder_lower for x in ["policy", "regulation", "act", "law", "governance"]):
            category = "Policy"
        elif any(x in folder_lower for x in ["news", "article", "press"]):
            category = "News"
        
        return source, year, category
    
    async def _populate_databank(
        self,
        report_id: UUID,
        extracted: dict
    ):
        """Add extracted items to the data bank."""
        try:
            # Add statistics
            for stat in extracted.get("statistics", []):
                await self.supabase.add_databank_item(
                    report_id=report_id,
                    item_type="statistic",
                    content=stat.get("value", str(stat)),
                    context=stat.get("context", ""),
                    source_page=stat.get("page"),
                    tags=stat.get("tags", [])
                )
            
            # Add quotes
            for quote in extracted.get("quotes", []):
                await self.supabase.add_databank_item(
                    report_id=report_id,
                    item_type="quote",
                    content=quote.get("text", str(quote)),
                    context=quote.get("attribution", ""),
                    source_page=quote.get("page"),
                    tags=[]
                )
            
            # Add aha moments
            for aha in extracted.get("aha_moments", []):
                await self.supabase.add_databank_item(
                    report_id=report_id,
                    item_type="aha_moment",
                    content=aha.get("insight", str(aha)),
                    context=aha.get("significance", ""),
                    source_page=aha.get("page"),
                    tags=[]
                )
            
            # Add key findings
            for finding in extracted.get("key_findings", []):
                await self.supabase.add_databank_item(
                    report_id=report_id,
                    item_type="finding",
                    content=finding.get("finding", str(finding)),
                    context=finding.get("evidence", ""),
                    source_page=finding.get("page"),
                    tags=[]
                )
                
        except Exception as e:
            logger.warning(f"Failed to populate databank: {e}")


# Singleton
_processing_service: Optional[ProcessingService] = None


def get_processing_service() -> ProcessingService:
    """Get the singleton processing service."""
    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService()
    return _processing_service
