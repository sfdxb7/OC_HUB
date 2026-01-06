"""
Upload MinerU-processed reports to RAGFlow - Version 2
Enriches markdown with page numbers from content_list.json for better citations.
"""
import os
import sys
import json
import time
import httpx
import re
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
UPLOAD_DELAY = 1.0
BATCH_SIZE = 10
BATCH_PAUSE = 5.0


def get_headers():
    return {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}


def extract_page_mappings(content_list_path: Path) -> dict:
    """
    Extract text-to-page mappings from content_list.json.
    Returns dict: {text_snippet: page_number}
    """
    if not content_list_path.exists():
        return {}
    
    try:
        with open(content_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mappings = {}
        for item in data:
            page_idx = item.get('page_idx', -1)
            if page_idx < 0:
                continue
            
            # Get text content
            text = item.get('text', '')
            if not text:
                # Try list items
                list_items = item.get('list_items', [])
                if list_items:
                    text = ' '.join(list_items)
            
            if text and len(text) > 10:
                # Store first 50 chars as key, page as value
                key = text[:50].strip()
                if key:
                    mappings[key] = page_idx + 1  # Convert to 1-indexed
        
        return mappings
    except Exception as e:
        print(f"  Warning: Could not parse content_list.json: {e}")
        return {}


def get_page_breaks(content_list_path: Path) -> list:
    """
    Get list of (page_number, first_text_on_page) tuples for adding page markers.
    """
    if not content_list_path.exists():
        return []
    
    try:
        with open(content_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        page_breaks = {}
        for item in data:
            page_idx = item.get('page_idx', -1)
            if page_idx < 0:
                continue
            
            text = item.get('text', '')
            if not text:
                list_items = item.get('list_items', [])
                if list_items:
                    text = ' '.join(list_items)
            
            if text and len(text) > 5 and page_idx not in page_breaks:
                # First significant text on this page
                page_breaks[page_idx] = text[:100].strip()
        
        return [(p + 1, t) for p, t in sorted(page_breaks.items())]
    except Exception as e:
        return []


def enrich_markdown_with_pages(md_content: str, page_breaks: list) -> str:
    """
    Add page markers to markdown content.
    Format: [Page N] before first content on each page.
    """
    if not page_breaks:
        return md_content
    
    enriched = md_content
    markers_added = 0
    
    for page_num, first_text in page_breaks:
        # Find the first occurrence of this text
        # Clean the text for matching
        search_text = first_text[:50]
        
        # Try to find and insert page marker
        if search_text in enriched:
            # Insert page marker before the text
            marker = f"\n\n[Page {page_num}]\n\n"
            
            # Find position and insert
            pos = enriched.find(search_text)
            if pos > 0:
                # Don't add if already has a page marker nearby
                prev_text = enriched[max(0, pos-30):pos]
                if '[Page' not in prev_text:
                    enriched = enriched[:pos] + marker + enriched[pos:]
                    markers_added += 1
    
    return enriched


def extract_metadata(folder: Path) -> dict:
    """Extract metadata from folder name and files."""
    name = folder.name
    
    # Try to extract year from name
    year_match = re.search(r'20\d{2}', name)
    year = int(year_match.group()) if year_match else None
    
    # Try to extract source
    sources = ['Accenture', 'McKinsey', 'BCG', 'Deloitte', 'KPMG', 'EY', 
               'Capgemini', 'Google', 'Microsoft', 'AI_Now', 'Anthropic',
               'DCAI', 'Dubai', 'UAE', 'Abu_Dhabi', 'arXiv', 'AAAI']
    source = None
    for s in sources:
        if s.lower() in name.lower():
            source = s.replace('_', ' ')
            break
    
    return {
        'year': year,
        'source': source,
        'original_filename': name
    }


def create_document_header(folder_name: str, metadata: dict, total_pages: int) -> str:
    """Create a metadata header for the document."""
    header = f"""---
Title: {folder_name.replace('_', ' ')}
Source: {metadata.get('source', 'Unknown')}
Year: {metadata.get('year', 'Unknown')}
Pages: {total_pages}
---

"""
    return header


def upload_document(client: httpx.Client, name: str, content: str) -> Optional[dict]:
    """Upload a text document to RAGFlow."""
    try:
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


def trigger_parse(client: httpx.Client, doc_id: str) -> bool:
    """Trigger parsing for uploaded document."""
    try:
        response = client.post(
            f"{RAGFLOW_URL}/api/v1/datasets/{DATASET_ID}/chunks",
            headers={**get_headers(), "Content-Type": "application/json"},
            json={"document_ids": [doc_id]},
            timeout=30.0
        )
        return response.status_code == 200
    except:
        return False


def find_files(folder: Path) -> tuple:
    """Find markdown and content_list.json in a MinerU folder."""
    vlm_path = folder / "vlm"
    search_path = vlm_path if vlm_path.exists() else folder
    
    md_file = None
    content_list = None
    
    for f in search_path.glob("*.md"):
        md_file = f
        break
    
    for f in search_path.glob("*_content_list.json"):
        content_list = f
        break
    
    return md_file, content_list


def process_folder(client: httpx.Client, folder: Path, enrich: bool = True) -> Optional[str]:
    """Process a single MinerU folder with enrichment."""
    md_file, content_list_file = find_files(folder)
    
    if not md_file:
        return None
    
    # Read markdown
    try:
        content = md_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = md_file.read_text(encoding="latin-1")
        except:
            return None
    
    if not content.strip():
        return None
    
    # Enrich with page numbers if available
    page_breaks = []
    if enrich and content_list_file:
        page_breaks = get_page_breaks(content_list_file)
        if page_breaks:
            content = enrich_markdown_with_pages(content, page_breaks)
    
    # Add metadata header
    metadata = extract_metadata(folder)
    total_pages = len(page_breaks) if page_breaks else 0
    if total_pages > 0:
        header = create_document_header(folder.name, metadata, total_pages)
        content = header + content
    
    # Upload
    doc_name = f"{folder.name}.md"
    result = upload_document(client, doc_name, content)
    
    if result:
        doc_id = result.get("id") if isinstance(result, dict) else None
        
        # Trigger parsing
        if AUTO_PARSE and doc_id:
            trigger_parse(client, doc_id)
        
        pages_info = f", {total_pages} pages" if total_pages else ""
        return doc_id or "uploaded"
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Upload MinerU reports to RAGFlow (v2 with enrichment)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N documents")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload")
    parser.add_argument("--no-enrich", action="store_true", help="Skip page enrichment")
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
    
    enrich = not args.no_enrich
    print(f"Page enrichment: {'ENABLED' if enrich else 'DISABLED'}")
    
    if args.dry_run:
        print("\nDRY RUN - checking files:")
        for i, folder in enumerate(folders, 1):
            md_file, content_list = find_files(folder)
            md_status = "MD:OK" if md_file else "MD:NO"
            cl_status = "CL:OK" if content_list else "CL:NO"
            print(f"  [{i}/{len(folders)}] {folder.name}: {md_status} {cl_status}")
        return
    
    # Upload
    uploaded = []
    failed = []
    
    with httpx.Client() as client:
        for i, folder in enumerate(folders, 1):
            print(f"[{i}/{len(folders)}] {folder.name}...", end=" ")
            
            doc_id = process_folder(client, folder, enrich=enrich)
            if doc_id:
                print(f"OK ({doc_id[:8] if len(doc_id) > 8 else doc_id})")
                uploaded.append(doc_id)
            else:
                print("FAILED")
                failed.append(folder.name)
            
            time.sleep(UPLOAD_DELAY)
            
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


if __name__ == "__main__":
    main()
