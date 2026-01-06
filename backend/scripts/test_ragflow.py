#!/usr/bin/env python3
"""
Test connection to RAGFlow API.

Usage:
    python scripts/test_ragflow.py
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()


def test_ragflow_connection():
    """Test RAGFlow API connectivity."""
    
    ragflow_url = os.getenv("RAGFLOW_URL", "http://localhost:9380")
    ragflow_api_key = os.getenv("RAGFLOW_API_KEY", "")
    
    print(f"Testing RAGFlow connection at: {ragflow_url}")
    
    # Headers
    headers = {}
    if ragflow_api_key:
        headers["Authorization"] = f"Bearer {ragflow_api_key}"
    
    try:
        # Test basic connectivity
        response = httpx.get(f"{ragflow_url}/api/v1/health", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: RAGFlow is healthy")
            print(f"Response: {response.json()}")
        else:
            print(f"WARNING: RAGFlow returned status {response.status_code}")
            print(f"Response: {response.text}")
            
    except httpx.ConnectError as e:
        print(f"ERROR: Cannot connect to RAGFlow at {ragflow_url}")
        print(f"Details: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure RAGFlow is running: docker-compose up ragflow -d")
        print("2. Check if port 9380 is accessible")
        print("3. Verify RAGFLOW_URL in .env")
        sys.exit(1)
        
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)
    
    # Test list datasets (requires API key)
    if ragflow_api_key:
        try:
            response = httpx.get(
                f"{ragflow_url}/api/v1/datasets",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                datasets = response.json().get("data", [])
                print(f"\nFound {len(datasets)} datasets")
                for ds in datasets[:5]:  # Show first 5
                    print(f"  - {ds.get('name', 'Unknown')}: {ds.get('document_count', 0)} docs")
            else:
                print(f"\nCould not list datasets: {response.status_code}")
                
        except Exception as e:
            print(f"\nCould not list datasets: {e}")
    else:
        print("\nSkipping dataset check (no API key configured)")
        print("Get your API key from RAGFlow UI after first login")


if __name__ == "__main__":
    test_ragflow_connection()
