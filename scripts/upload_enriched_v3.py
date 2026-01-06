"""
Full Upload Pipeline for DCAI Intelligence Platform

This script:
1. Generates enriched markdown from content_list.json
2. Uploads enriched markdown to RAGFlow
3. Uploads original PDFs to MinIO
4. Tracks progress and handles errors

Usage:
    python upload_enriched_v3.py [--test] [--skip-pdf] [--start-from N]
"""

import json
import os
import re
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional, Tuple
try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print("Warning: minio package not installed. Run: pip install minio")
    print("PDF upload to MinIO will be skipped.")


# ============================================
# Configuration
# ============================================

RAGFLOW_API_URL = "http://localhost:9380/api/v1"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "dcai-pdfs"
MINIO_SECURE = False

SOURCE_DIR = Path(r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru")
PROGRESS_FILE = Path(r"C:\myprojects\OC_HUB\scripts\upload_progress.json")

HEADERS = {
    "Authorization": f"Bearer {RAGFLOW_API_KEY}"
}


# ============================================
# HTML Table Parser (from create_enriched_markdown.py)
# ============================================

class HTMLTableParser(HTMLParser):
    """Parse HTML table to markdown format."""
    
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_cell = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = ""
            
    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            
    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def html_table_to_markdown(html: str) -> str:
    """Convert HTML table to markdown table."""
    if not html or not html.strip():
        return ""
    
    try:
        parser = HTMLTableParser()
        parser.feed(html)
        
        if not parser.rows:
            return ""
        
        lines = []
        header = parser.rows[0]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---" for _ in header]) + "|")
        
        for row in parser.rows[1:]:
            while len(row) < len(header):
                row.append("")
            lines.append("| " + " | ".join(row[:len(header)]) + " |")
        
        return "\n".join(lines)
    except Exception as e:
        return f"[Table - parsing error]\n"


def clean_text(text: str) -> str:
    """Clean text content."""
    if not text:
        return ""
    
    text = re.sub(r'\$(\d+)\\%\$', r'\1%', text)
    text = re.sub(r'\$\\%\$', '%', text)
    text = re.sub(r'\$\^{(\d+)}\$', r'[\1]', text)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def get_heading_prefix(level: int) -> str:
    """Get markdown heading prefix."""
    if level <= 0:
        return ""
    return "#" * min(level, 6) + " "


def generate_enriched_markdown(content_list: List[Dict[str, Any]], title: str) -> str:
    """Generate enriched markdown from content_list."""
    output_lines = [f"# {title}\n"]
    current_page = -1
    skip_types = {'header', 'footer', 'page_number', 'image'}
    
    for item in content_list:
        item_type = item.get('type', '')
        
        if item_type in skip_types:
            continue
        
        page_idx = item.get('page_idx', 0)
        if page_idx != current_page:
            current_page = page_idx
            output_lines.append(f"\n<!-- Page {page_idx + 1} -->\n")
        
        if item_type == 'text':
            text = clean_text(item.get('text', ''))
            if text:
                text_level = item.get('text_level', 0)
                prefix = get_heading_prefix(text_level)
                output_lines.append(f"{prefix}{text}\n")
        
        elif item_type == 'table':
            captions = item.get('table_caption', [])
            if captions:
                caption_text = " ".join(captions)
                output_lines.append(f"\n**{caption_text}**\n")
            
            table_html = item.get('table_body', '')
            if table_html:
                md_table = html_table_to_markdown(table_html)
                output_lines.append(f"\n{md_table}\n")
            
            footnotes = item.get('table_footnote', [])
            if footnotes:
                footnote_text = " ".join(footnotes)
                output_lines.append(f"\n*{footnote_text}*\n")
        
        elif item_type == 'list':
            list_items = item.get('list_items', [])
            for li in list_items:
                cleaned = clean_text(li)
                if cleaned.startswith('$\\bullet$'):
                    cleaned = cleaned.replace('$\\bullet$', '-')
                elif not cleaned.startswith('-') and not cleaned.startswith('*'):
                    cleaned = f"- {cleaned}"
                output_lines.append(f"{cleaned}\n")
        
        elif item_type == 'equation':
            eq_text = item.get('text', '')
            if eq_text:
                output_lines.append(f"\n```\n{eq_text}\n```\n")
        
        elif item_type == 'code':
            code_body = item.get('code_body', '')
            code_caption = item.get('code_caption', [])
            if code_caption:
                output_lines.append(f"\n**{' '.join(code_caption)}**\n")
            if code_body:
                output_lines.append(f"\n```\n{code_body}\n```\n")
    
    return "\n".join(output_lines)


# ============================================
# MinIO Functions
# ============================================

def get_minio_client():
    """Get MinIO client."""
    if not MINIO_AVAILABLE:
        return None
    from minio import Minio as MinioClient
    return MinioClient(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )


def ensure_bucket_exists(client, bucket_name: str):
    """Ensure the bucket exists, create if not."""
    if not MINIO_AVAILABLE:
        return False
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Created MinIO bucket: {bucket_name}")
        return True
    except Exception as e:
        print(f"MinIO error: {e}")
        return False


def upload_pdf_to_minio(client, pdf_path: Path, object_name: str) -> Optional[str]:
    """Upload PDF to MinIO and return the URL."""
    if not MINIO_AVAILABLE:
        return None
    try:
        client.fput_object(
            MINIO_BUCKET,
            object_name,
            str(pdf_path),
            content_type="application/pdf"
        )
        # Return the object URL
        return f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_name}"
    except Exception as e:
        print(f"  Error uploading PDF: {e}")
        return None


# ============================================
# RAGFlow Functions
# ============================================

def upload_to_ragflow(content: str, filename: str) -> Optional[str]:
    """Upload markdown content to RAGFlow."""
    url = f"{RAGFLOW_API_URL}/datasets/{DATASET_ID}/documents"
    
    # Create a file-like object from the content
    files = {
        'file': (filename, content.encode('utf-8'), 'text/markdown')
    }
    
    response = requests.post(url, headers=HEADERS, files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            docs = data.get("data", [])
            if docs:
                return docs[0].get("id")
        else:
            print(f"  RAGFlow error: {data.get('message')}")
    else:
        print(f"  HTTP error: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
    
    return None


def trigger_parsing(doc_id: str) -> bool:
    """Trigger document parsing in RAGFlow."""
    url = f"{RAGFLOW_API_URL}/datasets/{DATASET_ID}/chunks"
    
    payload = {"document_ids": [doc_id]}
    headers = {**HEADERS, "Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("code") == 0
    return False


# ============================================
# Progress Tracking
# ============================================

def load_progress() -> Dict:
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_index": 0}


def save_progress(progress: Dict):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


# ============================================
# Main Processing
# ============================================

def process_report(report_path: Path, minio_client, skip_pdf: bool) -> Tuple[bool, str]:
    """Process a single report: generate markdown, upload to RAGFlow, upload PDF."""
    report_name = report_path.name
    
    # Find content_list.json
    vlm_folder = report_path / "vlm"
    content_list_path = None
    pdf_path = None
    
    if vlm_folder.exists():
        candidates = list(vlm_folder.glob("*_content_list.json"))
        if candidates:
            content_list_path = candidates[0]
        
        pdf_candidates = list(vlm_folder.glob("*_origin.pdf"))
        if pdf_candidates:
            pdf_path = pdf_candidates[0]
    
    if not content_list_path or not content_list_path.exists():
        return False, "No content_list.json found"
    
    # Load and process content
    try:
        with open(content_list_path, 'r', encoding='utf-8') as f:
            content_list = json.load(f)
    except Exception as e:
        return False, f"Error reading content_list.json: {e}"
    
    # Generate enriched markdown
    title = report_name.replace('_', ' ')
    enriched_md = generate_enriched_markdown(content_list, title)
    
    if not enriched_md or len(enriched_md) < 100:
        return False, "Generated markdown too short"
    
    # Upload to RAGFlow
    filename = f"{report_name}_enriched.md"
    doc_id = upload_to_ragflow(enriched_md, filename)
    
    if not doc_id:
        return False, "Failed to upload to RAGFlow"
    
    # Upload PDF to MinIO (if not skipped)
    pdf_url = None
    if not skip_pdf and minio_client and pdf_path and pdf_path.exists():
        object_name = f"pdfs/{report_name}.pdf"
        pdf_url = upload_pdf_to_minio(minio_client, pdf_path, object_name)
    
    return True, f"doc_id={doc_id}, pdf_url={pdf_url}"


def main():
    parser = argparse.ArgumentParser(description='Upload enriched documents to RAGFlow')
    parser.add_argument('--test', action='store_true', help='Process only 5 sample reports')
    parser.add_argument('--skip-pdf', action='store_true', help='Skip PDF upload to MinIO')
    parser.add_argument('--start-from', type=int, default=0, help='Start from report index')
    parser.add_argument('--resume', action='store_true', help='Resume from last progress')
    args = parser.parse_args()
    
    print("=" * 60)
    print("DCAI Intelligence Platform - Document Upload Pipeline")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # Initialize MinIO client
    minio_client = None
    if not args.skip_pdf:
        try:
            minio_client = get_minio_client()
            ensure_bucket_exists(minio_client, MINIO_BUCKET)
            print(f"MinIO connected: {MINIO_ENDPOINT}")
        except Exception as e:
            print(f"Warning: MinIO connection failed: {e}")
            print("Continuing without PDF upload...")
    
    # Get report folders
    report_folders = sorted([f for f in SOURCE_DIR.iterdir() if f.is_dir()])
    total_reports = len(report_folders)
    
    print(f"Found {total_reports} reports in source directory")
    
    # Load progress if resuming
    progress = {"completed": [], "failed": [], "last_index": 0}
    if args.resume:
        progress = load_progress()
        args.start_from = progress.get("last_index", 0)
        print(f"Resuming from index {args.start_from}")
    
    # Apply filters
    if args.start_from > 0:
        report_folders = report_folders[args.start_from:]
        print(f"Starting from index {args.start_from}")
    
    if args.test:
        report_folders = report_folders[:5]
        print("TEST MODE: Processing only 5 reports")
    
    print()
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, report_path in enumerate(report_folders, 1):
        actual_index = args.start_from + i
        report_name = report_path.name
        
        # Skip if already completed
        if report_name in progress.get("completed", []):
            print(f"[{actual_index}/{total_reports}] SKIP (already done): {report_name[:40]}")
            continue
        
        print(f"[{actual_index}/{total_reports}] Processing: {report_name[:40]}...")
        
        success, message = process_report(report_path, minio_client, args.skip_pdf)
        
        if success:
            print(f"  -> SUCCESS: {message}")
            success_count += 1
            progress["completed"].append(report_name)
        else:
            print(f"  -> ERROR: {message}")
            error_count += 1
            progress["failed"].append({"name": report_name, "error": message})
        
        # Save progress periodically
        progress["last_index"] = actual_index
        if i % 10 == 0:
            save_progress(progress)
        
        # Rate limiting
        time.sleep(0.5)
    
    # Final save
    save_progress(progress)
    
    print()
    print("=" * 60)
    print("Upload Complete!")
    print("=" * 60)
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Completed: {datetime.now().isoformat()}")
    print(f"Progress saved to: {PROGRESS_FILE}")


if __name__ == "__main__":
    main()
