"""
DCAI Intelligence Platform - Full Reprocessing Script

Clears all existing data and reprocesses 405 reports using:
- Gemini 3 Flash via OpenRouter
- Optimized extraction prompt with UAE ministerial lens
- Validation with contextual integrity checks

Usage:
    python scripts/reprocess_all.py [--dry-run] [--skip-cleanup] [--sample N]
    
Options:
    --dry-run       Show what would be done without making changes
    --skip-cleanup  Skip clearing existing data (for resuming)
    --sample N      Only process N reports (for testing)
    --validate      Run validation on each extraction
"""

import os
import sys
import asyncio
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import requests
from dotenv import load_dotenv

# Load environment (priority: .env.local > .env > .env.example)
base_path = Path(__file__).parent.parent
load_dotenv(base_path / ".env.local", override=True)
load_dotenv(base_path / ".env", override=False)
load_dotenv(base_path / ".env.example", override=False)
load_dotenv(base_path / "backend" / ".env.local", override=True)
load_dotenv(base_path / "backend" / ".env", override=False)


# Configuration
RAGFLOW_API_URL = os.getenv("RAGFLOW_URL", "http://localhost:9380") + "/api/v1"
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM")
RAGFLOW_DATASET_ID = os.getenv("RAGFLOW_DATASET_ID", "eceb7b32e83111f080689a6078826a72")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

MINERU_REPORTS_PATH = os.getenv(
    "MINERU_REPORTS_PATH",
    r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru"
)

RAGFLOW_HEADERS = {
    "Authorization": f"Bearer {RAGFLOW_API_KEY}",
    "Content-Type": "application/json"
}


class ReprocessingStats:
    """Track processing statistics."""
    
    def __init__(self):
        self.started_at = datetime.now()
        self.total = 0
        self.processed = 0
        self.skipped = 0
        self.failed = 0
        self.errors = []
        
        # Extraction quality
        self.total_findings = 0
        self.total_statistics = 0
        self.total_quotes = 0
        self.total_aha_moments = 0
    
    def add_extraction(self, extracted: dict):
        """Add extraction results to stats."""
        self.total_findings += len(extracted.get("key_findings", []))
        self.total_statistics += len(extracted.get("statistics", []))
        self.total_quotes += len(extracted.get("quotes", []))
        self.total_aha_moments += len(extracted.get("aha_moments", []))
    
    def summary(self) -> str:
        """Generate summary report."""
        elapsed = (datetime.now() - self.started_at).total_seconds()
        rate = self.processed / elapsed * 60 if elapsed > 0 else 0
        
        return f"""
================================================================================
REPROCESSING COMPLETE
================================================================================
Duration: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)
Rate: {rate:.1f} reports/minute

REPORTS:
  Total:     {self.total}
  Processed: {self.processed}
  Skipped:   {self.skipped}
  Failed:    {self.failed}

EXTRACTED INTELLIGENCE:
  Key Findings:  {self.total_findings:,}
  Statistics:    {self.total_statistics:,}
  Quotes:        {self.total_quotes:,}
  Aha Moments:   {self.total_aha_moments:,}

AVERAGES PER REPORT:
  Findings:   {self.total_findings / max(self.processed, 1):.1f}
  Statistics: {self.total_statistics / max(self.processed, 1):.1f}
  Quotes:     {self.total_quotes / max(self.processed, 1):.1f}

ERRORS: {len(self.errors)}
"""


def cleanup_ragflow(dry_run: bool = False) -> int:
    """Delete all documents from RAGFlow dataset."""
    print("\n[1/3] Cleaning up RAGFlow documents...")
    
    # Get all documents
    documents = []
    page = 1
    while True:
        url = f"{RAGFLOW_API_URL}/datasets/{RAGFLOW_DATASET_ID}/documents"
        response = requests.get(
            url,
            headers=RAGFLOW_HEADERS,
            params={"page": page, "page_size": 100}
        )
        
        if response.status_code != 200:
            print(f"  Error fetching documents: {response.status_code}")
            break
        
        data = response.json()
        if data.get("code") != 0:
            print(f"  API error: {data.get('message')}")
            break
        
        docs = data.get("data", {}).get("docs", [])
        if not docs:
            break
        
        documents.extend(docs)
        total = data.get("data", {}).get("total", 0)
        if len(documents) >= total:
            break
        page += 1
    
    print(f"  Found {len(documents)} documents")
    
    if not documents:
        print("  No documents to delete")
        return 0
    
    if dry_run:
        print(f"  DRY RUN: Would delete {len(documents)} documents")
        return len(documents)
    
    # Delete in batches
    deleted = 0
    batch_size = 20
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        doc_ids = [d["id"] for d in batch]
        
        url = f"{RAGFLOW_API_URL}/datasets/{RAGFLOW_DATASET_ID}/documents"
        response = requests.delete(url, headers=RAGFLOW_HEADERS, json={"ids": doc_ids})
        
        if response.status_code == 200 and response.json().get("code") == 0:
            deleted += len(batch)
            print(f"  Deleted {deleted}/{len(documents)} documents", end="\r")
        else:
            print(f"\n  Error deleting batch: {response.text[:100]}")
        
        time.sleep(0.1)  # Rate limiting
    
    print(f"\n  Deleted {deleted} documents from RAGFlow")
    return deleted


def cleanup_supabase(dry_run: bool = False) -> tuple[int, int]:
    """Delete all reports and data_bank entries from Supabase."""
    print("\n[2/3] Cleaning up Supabase tables...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("  ERROR: Supabase credentials not configured")
        print("  Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.local")
        return 0, 0
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Count existing records
    count_headers = {**headers, "Prefer": "count=exact"}
    
    reports_count = 0
    databank_count = 0
    
    try:
        # Count reports
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/reports?select=id",
            headers=count_headers
        )
        if r.status_code == 200:
            reports_count = int(r.headers.get("content-range", "0/0").split("/")[1])
        
        # Count data_bank
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/data_bank?select=id",
            headers=count_headers
        )
        if r.status_code == 200:
            databank_count = int(r.headers.get("content-range", "0/0").split("/")[1])
    except Exception as e:
        print(f"  Error counting records: {e}")
    
    print(f"  Found {reports_count} reports, {databank_count} data_bank items")
    
    if dry_run:
        print(f"  DRY RUN: Would delete all records")
        return reports_count, databank_count
    
    # Delete data_bank first (has FK to reports)
    if databank_count > 0:
        r = requests.delete(
            f"{SUPABASE_URL}/rest/v1/data_bank?id=gte.00000000-0000-0000-0000-000000000000",
            headers=headers
        )
        if r.status_code in [200, 204]:
            print(f"  Deleted {databank_count} data_bank items")
        else:
            print(f"  Error deleting data_bank: {r.status_code} - {r.text[:100]}")
    
    # Delete reports
    if reports_count > 0:
        r = requests.delete(
            f"{SUPABASE_URL}/rest/v1/reports?id=gte.00000000-0000-0000-0000-000000000000",
            headers=headers
        )
        if r.status_code in [200, 204]:
            print(f"  Deleted {reports_count} reports")
        else:
            print(f"  Error deleting reports: {r.status_code} - {r.text[:100]}")
    
    return reports_count, databank_count


async def process_reports(
    sample: Optional[int] = None,
    dry_run: bool = False,
    validate: bool = False
) -> ReprocessingStats:
    """Process all reports with new extraction prompt."""
    print("\n[3/3] Processing reports with Gemini 3 Flash...")
    
    # Import processing service
    from app.services.processing import get_processing_service
    from app.services.llm import get_llm_service
    
    stats = ReprocessingStats()
    
    # Find all report folders
    reports_path = Path(MINERU_REPORTS_PATH)
    if not reports_path.exists():
        print(f"  ERROR: Reports path does not exist: {reports_path}")
        return stats
    
    folders = sorted([f for f in reports_path.iterdir() if f.is_dir()])
    
    if sample:
        folders = folders[:sample]
    
    stats.total = len(folders)
    print(f"  Found {stats.total} reports to process")
    
    if dry_run:
        print("  DRY RUN: Would process all reports")
        for f in folders[:5]:
            print(f"    - {f.name}")
        if len(folders) > 5:
            print(f"    ... and {len(folders) - 5} more")
        return stats
    
    # Initialize services
    processing = get_processing_service()
    
    # Process each folder
    for i, folder in enumerate(folders, 1):
        try:
            print(f"\n  [{i}/{stats.total}] {folder.name[:60]}...")
            
            result = await processing.process_mineru_folder(
                str(folder),
                force_reprocess=True  # Always reprocess
            )
            
            if result["status"] in ["processed", "reprocessed"]:
                stats.processed += 1
                # Get extraction stats from DB
                # (simplified - actual counts come from extraction)
            else:
                stats.skipped += 1
            
            print(f"    -> {result['status']}: {result.get('title', 'Unknown')[:50]}")
            
        except Exception as e:
            stats.failed += 1
            stats.errors.append({
                "folder": folder.name,
                "error": str(e)
            })
            print(f"    -> FAILED: {str(e)[:80]}")
        
        # Progress
        if i % 10 == 0:
            elapsed = (datetime.now() - stats.started_at).total_seconds()
            rate = i / elapsed * 60 if elapsed > 0 else 0
            remaining = (stats.total - i) / rate if rate > 0 else 0
            print(f"\n  === Progress: {i}/{stats.total} ({i/stats.total*100:.1f}%) | "
                  f"Rate: {rate:.1f}/min | ETA: {remaining:.0f} min ===\n")
    
    return stats


async def main():
    parser = argparse.ArgumentParser(
        description='Reprocess all DCAI reports with Gemini 3 Flash'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip clearing existing data'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Only process N reports (for testing)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation on each extraction'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Auto-confirm deletion (skip prompt)'
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print("DCAI Intelligence Platform - Full Reprocessing")
    print("=" * 80)
    print(f"Model: google/gemini-3-flash-preview")
    print(f"Reports path: {MINERU_REPORTS_PATH}")
    print(f"RAGFlow: {RAGFLOW_API_URL}")
    print(f"Dry run: {args.dry_run}")
    print(f"Sample: {args.sample or 'ALL'}")
    print()
    
    if not args.dry_run and not args.yes:
        confirm = input("This will DELETE all existing data. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    # Step 1: Cleanup RAGFlow
    if not args.skip_cleanup:
        cleanup_ragflow(args.dry_run)
    
    # Step 2: Cleanup Supabase
    if not args.skip_cleanup:
        cleanup_supabase(args.dry_run)
    
    # Step 3: Process reports
    stats = await process_reports(
        sample=args.sample,
        dry_run=args.dry_run,
        validate=args.validate
    )
    
    # Print summary
    print(stats.summary())
    
    # Write error log
    if stats.errors:
        error_log = Path(__file__).parent / "reprocess_errors.json"
        error_log.write_text(json.dumps(stats.errors, indent=2))
        print(f"Error log written to: {error_log}")


if __name__ == "__main__":
    asyncio.run(main())
