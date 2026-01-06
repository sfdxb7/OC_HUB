"""
Enriched Markdown Generator for DCAI Intelligence Platform

Converts MinerU content_list.json to enriched markdown with:
- Page markers for citations
- Tables converted from HTML to markdown
- Proper heading hierarchy
- Filtered headers/footers/page_numbers

Usage:
    python create_enriched_markdown.py [--test] [--report NAME]
"""

import json
import re
import os
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional
import argparse


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
        
        # Build markdown table
        lines = []
        
        # Header row
        header = parser.rows[0]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---" for _ in header]) + "|")
        
        # Data rows
        for row in parser.rows[1:]:
            # Ensure row has same number of columns as header
            while len(row) < len(header):
                row.append("")
            lines.append("| " + " | ".join(row[:len(header)]) + " |")
        
        return "\n".join(lines)
    except Exception as e:
        # Fallback: return raw HTML if parsing fails
        return f"[Table - parsing error: {e}]\n{html}"


def clean_text(text: str) -> str:
    """Clean text content - remove excessive whitespace, fix latex."""
    if not text:
        return ""
    
    # Clean up latex-style percentages
    text = re.sub(r'\$(\d+)\\%\$', r'\1%', text)
    text = re.sub(r'\$\\%\$', '%', text)
    
    # Clean up other latex artifacts
    text = re.sub(r'\$\^{(\d+)}\$', r'[\1]', text)  # Superscript references
    text = re.sub(r'\$([^$]+)\$', r'\1', text)  # Remove remaining $ wrappers
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def get_heading_prefix(level: int) -> str:
    """Get markdown heading prefix for text level."""
    if level <= 0:
        return ""
    return "#" * min(level, 6) + " "


def process_content_list(content_list: List[Dict[str, Any]]) -> str:
    """Process content_list.json and generate enriched markdown."""
    
    output_lines = []
    current_page = -1
    
    # Types to skip
    skip_types = {'header', 'footer', 'page_number', 'image'}
    
    for item in content_list:
        item_type = item.get('type', '')
        
        # Skip unwanted types
        if item_type in skip_types:
            continue
        
        # Add page marker when page changes
        page_idx = item.get('page_idx', 0)
        if page_idx != current_page:
            current_page = page_idx
            output_lines.append(f"\n<!-- Page {page_idx + 1} -->\n")
        
        # Process by type
        if item_type == 'text':
            text = clean_text(item.get('text', ''))
            if text:
                text_level = item.get('text_level', 0)
                prefix = get_heading_prefix(text_level)
                output_lines.append(f"{prefix}{text}\n")
        
        elif item_type == 'table':
            # Table caption
            captions = item.get('table_caption', [])
            if captions:
                caption_text = " ".join(captions)
                output_lines.append(f"\n**{caption_text}**\n")
            
            # Table body (convert HTML to markdown)
            table_html = item.get('table_body', '')
            if table_html:
                md_table = html_table_to_markdown(table_html)
                output_lines.append(f"\n{md_table}\n")
            
            # Table footnote
            footnotes = item.get('table_footnote', [])
            if footnotes:
                footnote_text = " ".join(footnotes)
                output_lines.append(f"\n*{footnote_text}*\n")
        
        elif item_type == 'list':
            list_items = item.get('list_items', [])
            for li in list_items:
                cleaned = clean_text(li)
                # Normalize bullet points
                if cleaned.startswith('$\\bullet$'):
                    cleaned = cleaned.replace('$\\bullet$', '-')
                elif not cleaned.startswith('-') and not cleaned.startswith('*'):
                    cleaned = f"- {cleaned}"
                output_lines.append(f"{cleaned}\n")
        
        elif item_type == 'equation':
            # Include equations as code blocks
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


def process_report(report_path: Path) -> Optional[str]:
    """Process a single report folder and return enriched markdown."""
    
    # Find content_list.json (check vlm folder first)
    vlm_folder = report_path / "vlm"
    
    content_list_path = None
    if vlm_folder.exists():
        # Look for content_list.json in vlm folder
        candidates = list(vlm_folder.glob("*_content_list.json"))
        if candidates:
            content_list_path = candidates[0]
    
    if not content_list_path or not content_list_path.exists():
        print(f"  Warning: No content_list.json found in {report_path}")
        return None
    
    try:
        with open(content_list_path, 'r', encoding='utf-8') as f:
            content_list = json.load(f)
        
        enriched_md = process_content_list(content_list)
        return enriched_md
    
    except Exception as e:
        print(f"  Error processing {content_list_path}: {e}")
        return None


def get_report_title(report_path: Path) -> str:
    """Extract report title from folder name."""
    name = report_path.name
    # Clean up the name
    name = name.replace('_', ' ')
    return name


def main():
    parser = argparse.ArgumentParser(description='Generate enriched markdown from MinerU output')
    parser.add_argument('--test', action='store_true', help='Process only 5 sample reports')
    parser.add_argument('--report', type=str, help='Process specific report by name')
    parser.add_argument('--output-dir', type=str, default='enriched_reports', 
                        help='Output directory for enriched markdown files')
    args = parser.parse_args()
    
    # Paths
    source_dir = Path(r"C:\myprojects\REVIEW\NewHUB\processed_reports_mineru")
    output_dir = Path(r"C:\myprojects\OC_HUB") / args.output_dir
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get report folders
    report_folders = [f for f in source_dir.iterdir() if f.is_dir()]
    
    if args.report:
        # Filter to specific report
        report_folders = [f for f in report_folders if args.report.lower() in f.name.lower()]
        if not report_folders:
            print(f"No reports found matching: {args.report}")
            return
    
    if args.test:
        report_folders = report_folders[:5]
        print(f"TEST MODE: Processing {len(report_folders)} sample reports")
    
    print(f"Processing {len(report_folders)} reports...")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, report_path in enumerate(report_folders, 1):
        report_name = report_path.name
        print(f"[{i}/{len(report_folders)}] {report_name[:50]}...")
        
        enriched_md = process_report(report_path)
        
        if enriched_md:
            # Add title at the top
            title = get_report_title(report_path)
            full_content = f"# {title}\n\n{enriched_md}"
            
            # Write to output file
            output_file = output_dir / f"{report_name}_enriched.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            success_count += 1
            print(f"  -> Created: {output_file.name}")
        else:
            error_count += 1
    
    print("-" * 60)
    print(f"Complete! Success: {success_count}, Errors: {error_count}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
