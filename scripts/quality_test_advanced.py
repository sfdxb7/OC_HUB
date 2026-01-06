"""
Advanced Quality Test - Multi-hop and Cross-Document Questions
"""
import httpx
import json

RAGFLOW_URL = "http://localhost:9380"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"

# Advanced multi-hop questions that require cross-document reasoning
ADVANCED_QUESTIONS = [
    {
        "question": "Compare Accenture's AI maturity framework with McKinsey's perspective on AI adoption stages. What are the common themes and where do they differ?",
        "type": "Cross-document comparison"
    },
    {
        "question": "What specific AI initiatives has Dubai launched under DCAI, and how do they align with the recommendations from global consulting firms like BCG and McKinsey?",
        "type": "UAE + Global synthesis"
    },
    {
        "question": "Based on multiple reports, what percentage of organizations are using generative AI, and what ROI improvements have been documented?",
        "type": "Statistical synthesis"
    },
    {
        "question": "What are the contrarian views or risks of AI that the reports highlight, particularly around job displacement, concentration of power, and existential risks?",
        "type": "Contrarian/risk focus"
    },
    {
        "question": "How does the EU AI Act classify different AI systems, and what compliance requirements apply to high-risk AI applications in government?",
        "type": "Deep regulatory dive"
    },
]


def retrieve_chunks(client: httpx.Client, question: str, top_k: int = 8) -> list:
    """Retrieve relevant chunks."""
    try:
        response = client.post(
            f"{RAGFLOW_URL}/api/v1/retrieval",
            headers={
                "Authorization": f"Bearer {RAGFLOW_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "question": question,
                "dataset_ids": [DATASET_ID],
                "top_k": top_k,
                "similarity_threshold": 0.1
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("chunks", [])
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def run_advanced_test():
    print("=" * 80)
    print("ADVANCED MULTI-HOP QUESTION TEST")
    print("=" * 80)
    
    with httpx.Client() as client:
        for i, test in enumerate(ADVANCED_QUESTIONS, 1):
            question = test["question"]
            qtype = test["type"]
            
            print(f"\n{'='*80}")
            print(f"[{i}/{len(ADVANCED_QUESTIONS)}] {qtype}")
            print(f"Q: {question}")
            print("-" * 80)
            
            chunks = retrieve_chunks(client, question)
            
            if not chunks:
                print("  NO RESULTS")
                continue
            
            # Analyze document diversity
            docs = {}
            for c in chunks:
                doc = c.get("document_keyword", "unknown")
                if doc not in docs:
                    docs[doc] = []
                docs[doc].append(c.get("similarity", 0))
            
            print(f"\nRetrieved {len(chunks)} chunks from {len(docs)} unique documents:")
            print()
            
            for doc, sims in sorted(docs.items(), key=lambda x: -max(x[1]))[:5]:
                avg_sim = sum(sims) / len(sims)
                print(f"  [{avg_sim:.3f}] {doc[:60]}")
            
            # Show best snippets from each document
            print("\nTop excerpts:")
            shown_docs = set()
            for c in chunks[:5]:
                doc = c.get("document_keyword", "unknown")
                if doc in shown_docs:
                    continue
                shown_docs.add(doc)
                
                content = c.get("content", "")[:300].replace("\n", " ")
                sim = c.get("similarity", 0)
                print(f"\n  [{sim:.3f}] {doc[:50]}...")
                print(f"  \"{content}...\"")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_advanced_test()
