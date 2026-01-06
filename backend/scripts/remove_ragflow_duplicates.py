"""
Remove duplicate documents from RAGFlow.
Keeps originals, removes (1), (2) suffixed copies.
"""
import re
import sys
from collections import defaultdict
from ragflow_sdk import RAGFlow

RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
RAGFLOW_BASE_URL = "http://localhost:9380"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"


def get_base_name(name: str) -> str:
    """Remove (1), (2) etc suffixes from filename."""
    return re.sub(r'\(\d+\)\.md$', '.md', name)


def main():
    print("Connecting to RAGFlow...")
    rag = RAGFlow(api_key=RAGFLOW_API_KEY, base_url=RAGFLOW_BASE_URL)
    
    # Get dataset
    datasets = rag.list_datasets()
    dataset = None
    for ds in datasets:
        if ds.id == DATASET_ID:
            dataset = ds
            break
    
    if not dataset:
        print(f"Dataset {DATASET_ID} not found!")
        sys.exit(1)
    
    # List all documents
    print("Fetching documents...")
    documents = dataset.list_documents(page=1, page_size=1000)
    print(f"Total documents: {len(documents)}")
    
    # Group by base name
    groups = defaultdict(list)
    for doc in documents:
        base = get_base_name(doc.name)
        groups[base].append(doc)
    
    # Find duplicates (groups with more than 1 doc)
    duplicates_to_remove = []
    for base_name, docs in groups.items():
        if len(docs) > 1:
            # Sort: originals first (no suffix), then by name
            docs.sort(key=lambda d: (
                1 if re.search(r'\(\d+\)\.md$', d.name) else 0,
                d.name
            ))
            # Keep first (original), mark rest for removal
            for doc in docs[1:]:
                duplicates_to_remove.append(doc)
    
    print(f"\nDocuments to remove: {len(duplicates_to_remove)}")
    
    if not duplicates_to_remove:
        print("No duplicates found!")
        return
    
    # Show what will be removed
    print("\nWill remove:")
    for doc in duplicates_to_remove[:10]:
        print(f"  - {doc.name[:70]}...")
    if len(duplicates_to_remove) > 10:
        print(f"  ... and {len(duplicates_to_remove) - 10} more")
    
    # Confirm
    response = input("\nProceed with deletion? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    # Delete duplicates
    print("\nDeleting duplicates...")
    deleted = 0
    failed = 0
    
    for doc in duplicates_to_remove:
        try:
            doc.delete()
            deleted += 1
            if deleted % 20 == 0:
                print(f"  Deleted {deleted}/{len(duplicates_to_remove)}...")
        except Exception as e:
            print(f"  Failed to delete {doc.name}: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Deleted: {deleted}")
    print(f"Failed: {failed}")
    print(f"Remaining documents: {len(documents) - deleted}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
