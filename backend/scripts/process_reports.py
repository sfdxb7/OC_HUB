#!/usr/bin/env python3
"""
CLI script to batch process MinerU reports.
Run from backend directory: python scripts/process_reports.py
"""
import asyncio
import sys
import logging
import os
from pathlib import Path
from io import StringIO

# Suppress ALL logging before any imports
os.environ["LOG_LEVEL"] = "CRITICAL"
os.environ["DEBUG"] = "false"

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Patch structlog to be silent
import structlog
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
    logger_factory=structlog.PrintLoggerFactory(file=StringIO()),  # Send to null
    cache_logger_on_first_use=False,
)

# Suppress standard logging
logging.disable(logging.WARNING)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Process MinerU reports")
    parser.add_argument("--path", default=r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--concurrent", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--start", type=int, default=0, help="Start from folder index")
    
    args = parser.parse_args()
    base_path = Path(args.path)
    
    if not base_path.exists():
        print(f"ERROR: Path not found: {base_path}")
        sys.exit(1)
    
    # Get folders
    folders = sorted([f for f in base_path.iterdir() if f.is_dir()])
    total_folders = len(folders)
    
    # Apply start offset
    if args.start > 0:
        folders = folders[args.start:]
    
    # Apply limit
    if args.limit:
        folders = folders[:args.limit]
    
    print("=" * 66)
    print(f" DCAI Report Processor")
    print(f" Total: {total_folders} | Processing: {len(folders)} | Workers: {args.concurrent}")
    print("=" * 66)
    
    if args.dry_run:
        print("\n[DRY RUN]")
        for i, f in enumerate(folders[:20], 1):
            print(f"  {i:3}. {f.name[:60]}")
        if len(folders) > 20:
            print(f"  ... +{len(folders) - 20} more")
        return
    
    # Import after arg parsing for speed
    from app.services.processing import get_processing_service
    processor = get_processing_service()
    
    # Results tracking
    stats = {"ok": 0, "skip": 0, "fail": 0}
    errors = []
    
    semaphore = asyncio.Semaphore(args.concurrent)
    lock = asyncio.Lock()
    
    async def process_one(folder: Path, idx: int):
        async with semaphore:
            name = folder.name[:55]
            pct = int((idx / len(folders)) * 100)
            
            try:
                result = await processor.process_mineru_folder(str(folder), force_reprocess=args.force)
                
                async with lock:
                    if result["status"] == "already_exists":
                        stats["skip"] += 1
                        print(f"[{pct:3}%] SKIP  {name}")
                    else:
                        stats["ok"] += 1
                        title = result.get('title', '')[:40]
                        print(f"[{pct:3}%] OK    {name}")
                        
            except Exception as e:
                async with lock:
                    stats["fail"] += 1
                    err_msg = str(e)[:40]
                    errors.append({"name": folder.name, "error": str(e)})
                    print(f"[{pct:3}%] FAIL  {name} | {err_msg}")
    
    print()
    tasks = [process_one(f, i+1) for i, f in enumerate(folders)]
    await asyncio.gather(*tasks)
    
    # Summary
    print()
    print("=" * 66)
    print(f"  OK:      {stats['ok']}")
    print(f"  SKIPPED: {stats['skip']}")
    print(f"  FAILED:  {stats['fail']}")
    print("=" * 66)
    
    if errors:
        print(f"\nFailed reports:")
        for e in errors[:15]:
            print(f"  - {e['name'][:50]}")
            print(f"    {e['error'][:70]}")


if __name__ == "__main__":
    asyncio.run(main())
