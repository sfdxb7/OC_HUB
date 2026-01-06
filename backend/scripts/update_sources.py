#!/usr/bin/env python3
"""
Script to update source field for existing reports using the expanded source detection map.
Run this after expanding the source_map in processing.py

Usage:
    python scripts/update_sources.py           # Dry run
    python scripts/update_sources.py --apply   # Actually update
"""
import os
import sys
import re
import asyncio
import argparse
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv('.env.local')
load_dotenv('.env')

import requests


def infer_metadata(folder_name: str) -> tuple[str, Optional[int], str]:
    """
    Infer source, year, and category from folder name.
    This is a copy of the logic from processing.py for standalone use.
    """
    folder_lower = folder_name.lower()
    
    # Check for date-prefixed news articles first (YYYY-MM-DD_...)
    date_prefix_match = re.match(r"^20\d{2}-\d{2}-\d{2}_", folder_name)
    if date_prefix_match:
        year = int(folder_name[:4])
        if "dubai" in folder_lower:
            source = "Dubai News"
        elif "uae" in folder_lower or "emirates" in folder_lower:
            source = "UAE News"
        else:
            source = "News Article"
        return source, year, "News"
    
    # Comprehensive source detection map
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
        
        # Standards Bodies
        "iso_": "ISO",
        "itu_": "ITU",
        "iea_": "IEA",
        
        # More Consulting
        "kearney": "Kearney",
        "roland_berger": "Roland Berger",
        "oliver_wyman": "Oliver Wyman",
        
        # US Government Branches
        "house_": "US House of Representatives",
        "omb_": "US OMB",
        "odni_": "US ODNI",
        
        # Other Governments
        "qatar": "Qatar Government",
        "new_zealand": "New Zealand Government",
        
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
                         "Dubai Health Authority", "Digital Dubai", "State of California", "US Federal Government",
                         "NIST", "NATO"]
    think_tanks = ["Atlantic Council", "Brookings Institution", "AI Now Institute", 
                  "Future of Life Institute", "Future of Humanity Institute", "Eon Institute"]
    international_orgs = ["World Bank", "United Nations", "IMF", "OECD", "World Economic Forum",
                         "UNESCO", "WHO", "European Union", "G7", "International Trade Centre"]
    academic_sources = ["arXiv", "MIT", "Stanford", "Harvard", "Oxford", "Cambridge", "IEEE"]
    tech_companies = ["Google", "Microsoft", "Amazon", "AWS", "Cisco", "Anthropic", "OpenAI",
                     "Meta", "NVIDIA", "IBM", "Salesforce", "Oracle", "Adobe", "Intel"]
    news_sources = ["Dubai News", "UAE News", "News Article"]
    
    # Priority 1: Source-specific categories (most reliable)
    if source in consulting_firms:
        category = "Consulting"
    elif source in government_sources:
        category = "Policy"
    elif source in think_tanks:
        category = "Think Tank"
    elif source in international_orgs:
        category = "International"
    elif source in academic_sources:
        category = "Academic"
    elif source in tech_companies:
        category = "Industry"
    elif source in news_sources:
        category = "News"
    # Priority 2: Keyword-based (fallback for Unknown sources)
    elif any(x in folder_lower for x in ["policy", "regulation", "act", "law", "governance"]):
        category = "Policy"
    elif any(x in folder_lower for x in ["news", "article", "press"]):
        category = "News"
    
    return source, year, category


def main():
    parser = argparse.ArgumentParser(description='Update report sources with expanded detection')
    parser.add_argument('--apply', action='store_true', help='Actually apply updates (default is dry run)')
    args = parser.parse_args()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        sys.exit(1)
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # Get all reports
    r = requests.get(
        f'{url}/rest/v1/reports?select=id,original_filename,source,category',
        headers={**headers, 'Prefer': ''}
    )
    reports = r.json()
    
    print(f"Found {len(reports)} total reports")
    print("=" * 60)
    
    updates = []
    still_unknown = []
    
    for report in reports:
        filename = report.get('original_filename', '')
        current_source = report.get('source', 'Unknown')
        current_category = report.get('category', 'Research')
        
        new_source, new_year, new_category = infer_metadata(filename)
        
        if new_source != current_source or new_category != current_category:
            updates.append({
                'id': report['id'],
                'filename': filename[:50],
                'old_source': current_source,
                'new_source': new_source,
                'old_category': current_category,
                'new_category': new_category
            })
        
        if new_source == "Unknown":
            still_unknown.append(filename)
    
    print(f"\nWill update {len(updates)} reports:")
    print("-" * 60)
    
    for u in updates[:30]:  # Show first 30
        print(f"  {u['filename'][:40]}...")
        print(f"    Source: {u['old_source']} -> {u['new_source']}")
        if u['old_category'] != u['new_category']:
            print(f"    Category: {u['old_category']} -> {u['new_category']}")
    
    if len(updates) > 30:
        print(f"  ... and {len(updates) - 30} more")
    
    print(f"\nStill Unknown after update: {len(still_unknown)}")
    if still_unknown:
        print("  Examples:")
        for fn in still_unknown[:10]:
            print(f"    - {fn[:60]}")
    
    if args.apply:
        print("\n" + "=" * 60)
        print("APPLYING UPDATES...")
        print("=" * 60)
        
        success = 0
        failed = 0
        
        for u in updates:
            try:
                update_data = {
                    'source': u['new_source'],
                    'category': u['new_category']
                }
                r = requests.patch(
                    f"{url}/rest/v1/reports?id=eq.{u['id']}",
                    headers=headers,
                    json=update_data
                )
                if r.status_code in [200, 204]:
                    success += 1
                else:
                    failed += 1
                    print(f"  Failed: {u['id']} - {r.status_code}: {r.text[:100]}")
            except Exception as e:
                failed += 1
                print(f"  Error: {u['id']} - {e}")
        
        print(f"\nDone! Updated {success}, Failed {failed}")
    else:
        print("\n[DRY RUN] Use --apply to actually update the database")


if __name__ == "__main__":
    main()
