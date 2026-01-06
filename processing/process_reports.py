#!/usr/bin/env python3
"""
Process MinerU outputs and ingest into DCAI Intelligence Platform.

This script:
1. Reads MinerU-processed reports from local folder
2. Uploads documents to RAGFlow (with GraphRAG)
3. Runs intelligence extraction prompts
4. Stores metadata and extracted data in Supabase

Usage:
    python process_reports.py [--limit N] [--reprocess]
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
from dotenv import load_dotenv
from tqdm import tqdm
from supabase import create_client
import structlog

# Load environment
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()


class ReportProcessor:
    """Process MinerU reports for DCAI Intelligence Platform."""
    
    def __init__(self):
        # Configuration
        self.mineru_path = Path(os.getenv("MINERU_REPORTS_PATH", ""))
        self.ragflow_url = os.getenv("RAGFLOW_URL", "http://localhost:9380")
        self.ragflow_api_key = os.getenv("RAGFLOW_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL_FAST", "x-ai/grok-3-fast")
        
        # Supabase client
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.supabase = create_client(supabase_url, supabase_key) if supabase_url else None
        
        # HTTP client
        self.http = httpx.AsyncClient(timeout=120)
        
        # Stats
        self.processed = 0
        self.failed = 0
        self.errors = []
    
    async def close(self):
        """Cleanup resources."""
        await self.http.aclose()
    
    def discover_reports(self) -> list[Path]:
        """Find all MinerU report folders."""
        if not self.mineru_path.exists():
            logger.error("MinerU path does not exist", path=str(self.mineru_path))
            return []
        
        reports = []
        for folder in self.mineru_path.iterdir():
            if folder.is_dir():
                # Look for vlm subfolder with .md file
                vlm_path = folder / "vlm"
                if vlm_path.exists():
                    md_files = list(vlm_path.glob("*.md"))
                    if md_files:
                        reports.append(folder)
        
        logger.info("Discovered reports", count=len(reports))
        return reports
    
    def parse_report(self, folder: Path) -> Optional[dict]:
        """Parse MinerU output folder into structured data."""
        vlm_path = folder / "vlm"
        
        # Find main files
        md_files = list(vlm_path.glob("*.md"))
        content_list_files = list(vlm_path.glob("*_content_list.json"))
        
        if not md_files:
            logger.warning("No markdown file found", folder=folder.name)
            return None
        
        md_file = md_files[0]
        
        # Read markdown content
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Failed to read markdown", file=str(md_file), error=str(e))
            return None
        
        # Parse content_list for page numbers
        page_data = []
        if content_list_files:
            try:
                page_data = json.loads(content_list_files[0].read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to parse content_list", error=str(e))
        
        # Extract metadata from filename
        filename = md_file.stem
        parts = filename.split("_")
        
        # Try to detect source from filename
        source = self._detect_source(filename)
        year = self._detect_year(filename, content)
        
        return {
            "title": self._clean_title(filename),
            "source": source,
            "year": year,
            "category": self._detect_category(filename, source),
            "original_filename": filename,
            "mineru_folder": str(folder),
            "content": content,
            "page_data": page_data,
            "page_count": self._count_pages(page_data)
        }
    
    def _detect_source(self, filename: str) -> str:
        """Detect report source from filename."""
        filename_lower = filename.lower()
        sources = {
            "bcg": "BCG",
            "mckinsey": "McKinsey",
            "deloitte": "Deloitte",
            "accenture": "Accenture",
            "kpmg": "KPMG",
            "ey_": "EY",
            "pwc": "PwC",
            "capgemini": "Capgemini",
            "google": "Google",
            "microsoft": "Microsoft",
            "dcai": "DCAI",
            "dff": "DFF",
            "uae": "UAE Government",
            "wto": "WTO",
            "oecd": "OECD",
            "world_economic": "WEF",
            "atlantic": "Atlantic Council",
        }
        
        for key, value in sources.items():
            if key in filename_lower:
                return value
        
        return "Other"
    
    def _detect_year(self, filename: str, content: str) -> Optional[int]:
        """Detect publication year."""
        import re
        
        # Try filename first (e.g., "_2024" or "_2025")
        year_match = re.search(r"[_\-]?(20\d{2})", filename)
        if year_match:
            return int(year_match.group(1))
        
        # Try content (look for copyright or publication year)
        content_match = re.search(r"(?:copyright|published|©)\s*(\d{4})", content[:5000], re.I)
        if content_match:
            return int(content_match.group(1))
        
        return None
    
    def _detect_category(self, filename: str, source: str) -> str:
        """Detect report category."""
        filename_lower = filename.lower()
        
        if source in ["BCG", "McKinsey", "Deloitte", "Accenture", "KPMG", "EY", "PwC", "Capgemini"]:
            return "Consulting"
        
        if any(x in filename_lower for x in ["policy", "regulation", "governance", "law"]):
            return "Policy"
        
        if any(x in filename_lower for x in ["news", "article", "press"]):
            return "News"
        
        if source in ["DCAI", "DFF", "UAE Government"]:
            return "Government"
        
        return "Research"
    
    def _clean_title(self, filename: str) -> str:
        """Clean filename into readable title."""
        # Remove common prefixes/suffixes
        title = filename
        
        # Replace underscores with spaces
        title = title.replace("_", " ")
        
        # Remove date prefixes like "2024-01-15"
        import re
        title = re.sub(r"^\d{4}-\d{2}-\d{2}\s*", "", title)
        
        # Remove UUID-like suffixes
        title = re.sub(r"\s*[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", "", title, flags=re.I)
        
        # Trim and clean
        title = " ".join(title.split())
        
        return title if title else filename
    
    def _count_pages(self, page_data: list) -> int:
        """Count unique pages in content_list."""
        if not page_data:
            return 0
        
        pages = set()
        for item in page_data:
            if "page_idx" in item:
                pages.add(item["page_idx"])
        
        return len(pages) if pages else 0
    
    async def upload_to_ragflow(self, report: dict) -> Optional[str]:
        """Upload document to RAGFlow."""
        # TODO: Implement RAGFlow API upload
        # This is a placeholder - actual implementation depends on RAGFlow API
        
        logger.info("Would upload to RAGFlow", title=report["title"])
        
        # Return placeholder doc ID
        return f"ragflow_{report['original_filename'][:50]}"
    
    async def extract_intelligence(self, report: dict) -> dict:
        """Run extraction prompt on report content."""
        from backend.app.prompts.extraction import EXTRACTION_PROMPT
        
        # Prepare prompt
        prompt = EXTRACTION_PROMPT.format(
            title=report["title"],
            source=report["source"],
            year=report.get("year", "Unknown"),
            filename=report["original_filename"],
            content=report["content"][:50000]  # Limit content length
        )
        
        # Call LLM via OpenRouter
        try:
            response = await self.http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8192,
                    "temperature": 0.3
                }
            )
            
            if response.status_code != 200:
                logger.error("LLM request failed", status=response.status_code)
                return {}
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error("Extraction failed", error=str(e), title=report["title"])
            return {}
    
    async def save_to_supabase(self, report: dict, ragflow_id: str, extracted: dict) -> bool:
        """Save report and extracted data to Supabase."""
        if not self.supabase:
            logger.warning("Supabase not configured, skipping save")
            return False
        
        try:
            # Insert report
            report_data = {
                "title": report["title"],
                "source": report["source"],
                "year": report.get("year"),
                "category": report.get("category"),
                "page_count": report.get("page_count"),
                "original_filename": report["original_filename"],
                "mineru_folder": report["mineru_folder"],
                "ragflow_doc_id": ragflow_id,
                "executive_summary": extracted.get("executive_summary"),
                "key_findings": extracted.get("key_findings", []),
                "statistics": extracted.get("statistics", []),
                "quotes": extracted.get("quotes", []),
                "aha_moments": extracted.get("aha_moments", []),
                "recommendations": extracted.get("recommendations", []),
                "methodology": extracted.get("methodology"),
                "limitations": extracted.get("limitations"),
                "full_text": report["content"][:100000],  # Limit for full-text search
                "processing_status": "completed",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("reports").insert(report_data).execute()
            report_id = result.data[0]["id"]
            
            # Insert data bank items
            data_bank_items = []
            
            for stat in extracted.get("statistics", []):
                data_bank_items.append({
                    "report_id": report_id,
                    "type": "statistic",
                    "content": stat.get("stat", ""),
                    "context": stat.get("context"),
                    "source_page": stat.get("source_page"),
                    "value": stat.get("stat"),
                })
            
            for quote in extracted.get("quotes", []):
                data_bank_items.append({
                    "report_id": report_id,
                    "type": "quote",
                    "content": quote.get("quote", ""),
                    "context": quote.get("context"),
                    "source_page": quote.get("page"),
                    "speaker": quote.get("speaker"),
                })
            
            for aha in extracted.get("aha_moments", []):
                data_bank_items.append({
                    "report_id": report_id,
                    "type": "aha_moment",
                    "content": aha.get("insight", ""),
                    "context": aha.get("implications"),
                })
            
            if data_bank_items:
                self.supabase.table("data_bank").insert(data_bank_items).execute()
            
            logger.info("Saved to Supabase", report_id=report_id, data_bank_items=len(data_bank_items))
            return True
            
        except Exception as e:
            logger.error("Failed to save to Supabase", error=str(e))
            return False
    
    async def process_report(self, folder: Path) -> bool:
        """Process a single report."""
        logger.info("Processing report", folder=folder.name)
        
        # Parse report
        report = self.parse_report(folder)
        if not report:
            return False
        
        # Upload to RAGFlow
        ragflow_id = await self.upload_to_ragflow(report)
        if not ragflow_id:
            logger.error("Failed to upload to RAGFlow", title=report["title"])
            return False
        
        # Extract intelligence
        extracted = await self.extract_intelligence(report)
        
        # Save to Supabase
        success = await self.save_to_supabase(report, ragflow_id, extracted)
        
        return success
    
    async def run(self, limit: Optional[int] = None, reprocess: bool = False):
        """Run the processing pipeline."""
        logger.info("Starting report processing", 
                   mineru_path=str(self.mineru_path),
                   limit=limit)
        
        # Discover reports
        reports = self.discover_reports()
        if limit:
            reports = reports[:limit]
        
        # Process each report
        for folder in tqdm(reports, desc="Processing"):
            try:
                success = await self.process_report(folder)
                if success:
                    self.processed += 1
                else:
                    self.failed += 1
            except Exception as e:
                logger.exception("Error processing report", folder=folder.name)
                self.failed += 1
                self.errors.append({"folder": folder.name, "error": str(e)})
        
        # Summary
        logger.info("Processing complete",
                   processed=self.processed,
                   failed=self.failed,
                   errors=len(self.errors))
        
        if self.errors:
            logger.error("Errors encountered", errors=self.errors)


async def main():
    parser = argparse.ArgumentParser(description="Process MinerU reports")
    parser.add_argument("--limit", type=int, help="Limit number of reports to process")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess existing reports")
    args = parser.parse_args()
    
    processor = ReportProcessor()
    try:
        await processor.run(limit=args.limit, reprocess=args.reprocess)
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())
