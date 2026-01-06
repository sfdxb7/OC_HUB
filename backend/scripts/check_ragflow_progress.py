"""
Check RAGFlow document parsing progress.
"""
import sys
from ragflow_sdk import RAGFlow

RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
RAGFLOW_BASE_URL = "http://localhost:9380"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"


def main():
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
    
    # List documents
    documents = dataset.list_documents(page=1, page_size=1000)
    
    # Count by status
    status_counts = {}
    total_chunks = 0
    total_tokens = 0
    
    for doc in documents:
        status = doc.run
        status_counts[status] = status_counts.get(status, 0) + 1
        total_chunks += doc.chunk_count or 0
        total_tokens += doc.token_count or 0
    
    print("="*60)
    print("RAGFlow Parsing Progress")
    print("="*60)
    print(f"\nDataset: {dataset.name}")
    print(f"Total Documents: {len(documents)}")
    print(f"\nStatus breakdown:")
    for status, count in sorted(status_counts.items()):
        pct = count / len(documents) * 100
        print(f"  {status}: {count} ({pct:.1f}%)")
    
    print(f"\nTotal chunks created: {total_chunks:,}")
    print(f"Total tokens: {total_tokens:,}")
    
    # Show samples of each status
    print("\n" + "-"*60)
    for status in sorted(status_counts.keys()):
        samples = [d for d in documents if d.run == status][:3]
        print(f"\nSample {status} documents:")
        for doc in samples:
            print(f"  - {doc.name[:60]}... (chunks: {doc.chunk_count}, progress: {doc.progress})")
    
    # Calculate estimated time if processing
    running_count = status_counts.get("RUNNING", 0)
    done_count = status_counts.get("DONE", 0) + status_counts.get("FINISH", 0)
    
    if done_count > 0 and running_count > 0:
        remaining = len(documents) - done_count
        print(f"\n{done_count} done, {remaining} remaining")


if __name__ == "__main__":
    main()
