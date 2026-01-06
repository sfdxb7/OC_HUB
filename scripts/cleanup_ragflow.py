"""
RAGFlow Cleanup Script for DCAI Intelligence Platform

Deletes all documents from the specified dataset to start fresh.

Usage:
    python cleanup_ragflow.py [--dry-run]
"""

import requests
import argparse
import time

# Configuration
RAGFLOW_API_URL = "http://localhost:9380/api/v1"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"

HEADERS = {
    "Authorization": f"Bearer {RAGFLOW_API_KEY}",
    "Content-Type": "application/json"
}


def get_all_documents():
    """Get all documents in the dataset."""
    documents = []
    page = 1
    page_size = 100
    
    while True:
        url = f"{RAGFLOW_API_URL}/datasets/{DATASET_ID}/documents"
        params = {"page": page, "page_size": page_size}
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching documents: {response.status_code}")
            print(response.text)
            break
        
        data = response.json()
        
        if data.get("code") != 0:
            print(f"API error: {data.get('message')}")
            break
        
        docs = data.get("data", {}).get("docs", [])
        if not docs:
            break
        
        documents.extend(docs)
        
        total = data.get("data", {}).get("total", 0)
        if len(documents) >= total:
            break
        
        page += 1
    
    return documents


def delete_document(doc_id: str, doc_name: str) -> bool:
    """Delete a single document."""
    url = f"{RAGFLOW_API_URL}/datasets/{DATASET_ID}/documents"
    
    # RAGFlow API expects document IDs in the body
    payload = {"ids": [doc_id]}
    
    response = requests.delete(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            return True
        else:
            print(f"  Error deleting {doc_name}: {data.get('message')}")
            return False
    else:
        print(f"  HTTP error deleting {doc_name}: {response.status_code}")
        return False


def delete_all_documents(documents: list, dry_run: bool = False) -> tuple:
    """Delete all documents from the dataset."""
    success = 0
    failed = 0
    
    for i, doc in enumerate(documents, 1):
        doc_id = doc.get("id")
        doc_name = doc.get("name", "unknown")
        
        print(f"[{i}/{len(documents)}] Deleting: {doc_name[:50]}...")
        
        if dry_run:
            print("  -> DRY RUN: Would delete")
            success += 1
        else:
            if delete_document(doc_id, doc_name):
                print("  -> Deleted")
                success += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(0.1)
    
    return success, failed


def update_dataset_config():
    """Update dataset configuration with full GraphRAG and new entity types."""
    url = f"{RAGFLOW_API_URL}/datasets/{DATASET_ID}"
    
    payload = {
        "parser_config": {
            "graphrag": {
                "use_graphrag": True,
                "method": "general",
                "entity_types": [
                    "organization",
                    "person",
                    "geo",
                    "event",
                    "category",
                    "policy",
                    "initiative",
                    "statistic",
                    "technology",
                    "recommendation"
                ]
            }
        }
    }
    
    response = requests.put(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            print("Dataset GraphRAG config updated to 'full' method")
            return True
        else:
            print(f"Error updating config: {data.get('message')}")
            return False
    else:
        print(f"HTTP error updating config: {response.status_code}")
        print(response.text)
        return False


def main():
    parser = argparse.ArgumentParser(description='Cleanup RAGFlow dataset')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    parser.add_argument('--update-config', action='store_true', help='Also update GraphRAG config')
    args = parser.parse_args()
    
    print("=" * 60)
    print("RAGFlow Dataset Cleanup")
    print("=" * 60)
    print(f"Dataset ID: {DATASET_ID}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    # Get all documents
    print("Fetching documents...")
    documents = get_all_documents()
    print(f"Found {len(documents)} documents")
    print()
    
    if not documents:
        print("No documents to delete. Dataset is already empty.")
    else:
        # Confirm deletion
        if not args.dry_run:
            confirm = input(f"Delete all {len(documents)} documents? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                return
        
        print()
        print("Deleting documents...")
        success, failed = delete_all_documents(documents, args.dry_run)
        
        print()
        print("-" * 60)
        print(f"Complete! Deleted: {success}, Failed: {failed}")
    
    # Update config if requested
    if args.update_config:
        print()
        print("Updating GraphRAG configuration...")
        update_dataset_config()
    
    print()
    print("Done!")


if __name__ == "__main__":
    main()
