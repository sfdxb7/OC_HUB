"""
Trigger RAGFlow document parsing via SDK.
All 599 documents are in UNSTART state - need to parse them.
"""
import asyncio
import sys
from ragflow_sdk import RAGFlow

# Configuration
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
RAGFLOW_BASE_URL = "http://localhost:9380"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"


def main():
    print("Connecting to RAGFlow...")
    rag = RAGFlow(api_key=RAGFLOW_API_KEY, base_url=RAGFLOW_BASE_URL)
    
    # Get dataset
    print(f"Getting dataset {DATASET_ID}...")
    datasets = rag.list_datasets()
    dataset = None
    for ds in datasets:
        if ds.id == DATASET_ID:
            dataset = ds
            break
    
    if not dataset:
        print(f"Dataset {DATASET_ID} not found!")
        sys.exit(1)
    
    print(f"Found dataset: {dataset.name}")
    print(f"Document count: {dataset.document_count}")
    
    # List documents
    print("\nListing documents...")
    documents = dataset.list_documents(page=1, page_size=1000)
    print(f"Retrieved {len(documents)} documents")
    
    # Filter unparsed
    unparsed = [doc for doc in documents if doc.run == "UNSTART"]
    print(f"Unparsed documents: {len(unparsed)}")
    
    if not unparsed:
        print("All documents already parsed!")
        return
    
    # Trigger parsing in batches
    batch_size = 50
    total = len(unparsed)
    
    print(f"\nTriggering parsing for {total} documents in batches of {batch_size}...")
    
    for i in range(0, total, batch_size):
        batch = unparsed[i:i+batch_size]
        doc_ids = [doc.id for doc in batch]
        
        print(f"\nBatch {i//batch_size + 1}: Processing documents {i+1}-{min(i+batch_size, total)}...")
        
        try:
            # Use async_parse for batch processing
            dataset.async_parse_documents(doc_ids)
            print(f"  Triggered parsing for {len(doc_ids)} documents")
        except Exception as e:
            print(f"  Error: {e}")
            # Try one by one
            for doc in batch:
                try:
                    doc.async_parse()
                    print(f"    Parsed: {doc.name[:50]}...")
                except Exception as e2:
                    print(f"    Failed: {doc.name[:50]}... - {e2}")
    
    print("\n" + "="*60)
    print("Parsing triggered! Documents will be processed in background.")
    print("Check progress with: python check_ragflow_progress.py")
    print("="*60)


if __name__ == "__main__":
    main()
