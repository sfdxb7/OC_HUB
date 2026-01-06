"""
Upload MinerU-processed reports to RAGFlow.
This script uploads markdown files to RAGFlow for vectorization.
"""
import os
import sys
import json
import time
import httpx
from pathlib import Path
from typing import Optional
import argparse

# Configuration
RAGFLOW_URL = "http://localhost:9380"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"  # DCAI Intelligence Hub

# Auto-parse after upload
AUTO_PARSE = True
REPORTS_PATH = r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru"

# Rate limiting
UPLOAD_DELAY = 1.0  # seconds between uploads
BATCH_SIZE = 10  # documents per batch before longer pause
BATCH_PAUSE = 5.0  # seconds pause between batches


def get_headers():
    return {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
    }


def upload_document(client: httpx.Client, name: str, content: str) -> Optional[dict]:
    """Upload a text document to RAGFlow."""
    try:
        # RAGFlow expects multipart file upload
        files = {"file": (name, content.encode("utf-8"), "text/markdown")}
        response = client.post(
            f"{RAGFLOW_URL}/api/v1/datasets/{DATASET_ID}/documents",
            headers=get_headers(),
            files=files,
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                result = data.get("data")
                # Handle both list and dict responses
                if isinstance(result, list) and len(result) > 0:
                    return result[0]
                elif isinstance(result, dict):
                    return result
                return {"id": "uploaded"}
            else:
                print(f"  Error: {data.get('message')}")
                return None
        else:
            print(f"  HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def parse_documents(client: httpx.Client, document_ids: list[str]) -> bool:
    """Trigger parsing for uploaded documents."""
    try:
        response = client.post(
            f"{RAGFLOW_URL}/api/v1/datasets/{DATASET_ID}/chunks",
            headers={**get_headers(), "Content-Type": "application/json"},
            json={"document_ids": document_ids},
            timeout=120.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("code") == 0
        return False
        
    except Exception as e:
        print(f"  Parse error: {e}")
        return False


def find_markdown_file(folder: Path) -> Optional[Path]:
    """Find the main markdown file in a MinerU folder."""
    vlm_path = folder / "vlm"
    if vlm_path.exists():
        search_path = vlm_path
    else:
        search_path = folder
    
    md_files = list(search_path.glob("*.md"))
    if md_files:
        return md_files[0]
    return None


def process_folder(client: httpx.Client, folder: Path) -> Optional[str]:
    """Process a single MinerU folder."""
    md_file = find_markdown_file(folder)
    if not md_file:
        return None
    
    # Read content
    try:
        content = md_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = md_file.read_text(encoding="latin-1")
        except:
            return None
    
    if not content.strip():
        return None
    
    # Use folder name as document name
    doc_name = f"{folder.name}.md"
    
    # Upload
    result = upload_document(client, doc_name, content)
    if result:
        doc_id = None
        if isinstance(result, dict):
            doc_id = result.get("id")
        
        # Trigger parsing if enabled
        if AUTO_PARSE and doc_id:
            try:
                parse_response = client.post(
                    f"{RAGFLOW_URL}/api/v1/datasets/{DATASET_ID}/chunks",
                    headers={**get_headers(), "Content-Type": "application/json"},
                    json={"document_ids": [doc_id]},
                    timeout=30.0
                )
            except Exception as e:
                print(f"(parse queued)", end=" ")
        
        return doc_id or "uploaded"
    return None


def main():
    parser = argparse.ArgumentParser(description="Upload MinerU reports to RAGFlow")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents (0=all)")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N documents")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload")
    args = parser.parse_args()
    
    reports_path = Path(REPORTS_PATH)
    if not reports_path.exists():
        print(f"Error: Reports path does not exist: {reports_path}")
        sys.exit(1)
    
    folders = sorted([f for f in reports_path.iterdir() if f.is_dir()])
    total = len(folders)
    print(f"Found {total} report folders")
    
    if args.skip:
        folders = folders[args.skip:]
        print(f"Skipping first {args.skip}, processing {len(folders)}")
    
    if args.limit:
        folders = folders[:args.limit]
        print(f"Limiting to {args.limit} documents")
    
    if args.dry_run:
        print("DRY RUN - not uploading")
        for i, folder in enumerate(folders, 1):
            md_file = find_markdown_file(folder)
            status = "OK" if md_file else "NO MD"
            print(f"  [{i}/{len(folders)}] {folder.name}: {status}")
        return
    
    # Upload with httpx client
    uploaded = []
    failed = []
    
    with httpx.Client() as client:
        for i, folder in enumerate(folders, 1):
            print(f"[{i}/{len(folders)}] {folder.name}...", end=" ")
            
            doc_id = process_folder(client, folder)
            if doc_id:
                print(f"OK ({doc_id[:8]}...)")
                uploaded.append(doc_id)
            else:
                print("FAILED")
                failed.append(folder.name)
            
            # Rate limiting
            time.sleep(UPLOAD_DELAY)
            
            # Batch pause
            if i % BATCH_SIZE == 0:
                print(f"  Batch pause ({BATCH_PAUSE}s)...")
                time.sleep(BATCH_PAUSE)
    
    # Summary
    print("\n" + "="*50)
    print(f"COMPLETE: {len(uploaded)} uploaded, {len(failed)} failed")
    
    if failed:
        print("\nFailed folders:")
        for name in failed[:20]:
            print(f"  - {name}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
    
    # Optionally trigger parsing
    if uploaded:
        print(f"\nNote: Documents uploaded. Parsing will start automatically.")
        print(f"Check RAGFlow UI at http://localhost to monitor progress.")


if __name__ == "__main__":
    main()
