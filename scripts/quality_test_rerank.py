"""
Quality Test: Compare retrieval WITH and WITHOUT Cohere rerank-v4.0-pro
"""
import httpx
import json

RAGFLOW_URL = "http://localhost:9380"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"

# Same questions as before
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "What is the One Million Prompters initiative and when was it launched?",
        "expected_doc": "DCAI news article about One Million Prompters",
        "category": "DCAI Specific"
    },
    {
        "id": 2,
        "question": "What are the specific AI use cases Dubai has implemented in healthcare and transportation?",
        "expected_doc": "15_AI_Use_Cases_in_Government_Dubai_2025",
        "category": "Dubai AI Use Cases"
    },
    {
        "id": 3,
        "question": "According to Accenture, what percentage of companies have achieved AI maturity and what distinguishes AI achievers from others?",
        "expected_doc": "Accenture_AI_Maturity or Accenture_Art_of_AI_Maturity",
        "category": "Accenture AI Maturity"
    },
    {
        "id": 4,
        "question": "What is Anthropic's Responsible Scaling Policy and what are the ASL safety levels?",
        "expected_doc": "Anthropic_Responsible_Scaling_Policy or Anthropic_ASL3",
        "category": "Anthropic Safety"
    },
    {
        "id": 5,
        "question": "What is Abu Dhabi's AI sectoral strategy and which industries are prioritized?",
        "expected_doc": "Abu_Dhabi_AI_Sectoral_Report_2024",
        "category": "Abu Dhabi AI"
    },
    {
        "id": 6,
        "question": "How does OpenAI's business model work and what are the revenue streams for generative AI companies?",
        "expected_doc": "AI_Now_Institute_Generative_AI_Business_Models",
        "category": "GenAI Business Models"
    },
    {
        "id": 7,
        "question": "What happened at the AI Retreat 2024 in Dubai and what were the key themes discussed?",
        "expected_doc": "AI Retreat news articles",
        "category": "AI Retreat 2024"
    },
    {
        "id": 8,
        "question": "What is the AGILE index for AI governance and how are countries ranked?",
        "expected_doc": "arXiv_AI_Governance_International_Evaluation_AGILE_Index",
        "category": "AGILE Index"
    },
    {
        "id": 9,
        "question": "What are the key responsibilities of a Chief AI Officer and how should organizations structure AI leadership?",
        "expected_doc": "AI_Journal_Chief_AI_Officer_Role_Whitepaper",
        "category": "Chief AI Officer"
    },
]


def retrieve_chunks(client: httpx.Client, question: str, rerank_model: str = None, top_k: int = 5) -> list:
    """Retrieve chunks with optional reranking."""
    payload = {
        "question": question,
        "dataset_ids": [DATASET_ID],
        "top_k": top_k,
        "similarity_threshold": 0.1
    }
    if rerank_model:
        payload["rerank_model"] = rerank_model
    
    try:
        response = client.post(
            f"{RAGFLOW_URL}/api/v1/retrieval",
            headers={
                "Authorization": f"Bearer {RAGFLOW_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("chunks", [])
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def evaluate_result(chunks: list, expected_keywords: list) -> dict:
    """Evaluate if results match expected documents."""
    if not chunks:
        return {"found": False, "top_doc": None, "similarity": 0, "rank": -1}
    
    top_doc = chunks[0].get("document_keyword", "")
    top_sim = chunks[0].get("similarity", 0)
    
    # Check if expected doc is in results
    for i, chunk in enumerate(chunks):
        doc_name = chunk.get("document_keyword", "").lower()
        for keyword in expected_keywords:
            if keyword.lower() in doc_name:
                return {
                    "found": True,
                    "top_doc": top_doc,
                    "similarity": top_sim,
                    "rank": i + 1,
                    "matched_doc": chunk.get("document_keyword", "")
                }
    
    return {"found": False, "top_doc": top_doc, "similarity": top_sim, "rank": -1}


def run_comparison_test():
    print("=" * 90)
    print("RETRIEVAL QUALITY TEST: No Reranker vs Cohere rerank-v4.0-pro")
    print("=" * 90)
    print()
    
    # Expected document keywords for each question
    expected_docs = [
        ["prompter", "million"],  # Q1
        ["15_ai_use_cases", "dubai"],  # Q2
        ["accenture", "maturity"],  # Q3
        ["anthropic", "rsp", "asl"],  # Q4
        ["abu_dhabi", "sectoral"],  # Q5
        ["generative_ai_business", "ai_now"],  # Q6
        ["ai_retreat", "2024"],  # Q7
        ["agile", "governance"],  # Q8
        ["chief_ai_officer", "ai_journal"],  # Q9
    ]
    
    results_baseline = []
    results_rerank = []
    
    with httpx.Client() as client:
        for i, test in enumerate(TEST_QUESTIONS):
            q = test["question"]
            cat = test["category"]
            expected = expected_docs[i]
            
            print(f"\n[{test['id']}/9] {cat}")
            print(f"Q: {q[:80]}...")
            print("-" * 70)
            
            # Test WITHOUT reranker
            chunks_base = retrieve_chunks(client, q, rerank_model=None)
            eval_base = evaluate_result(chunks_base, expected)
            
            # Test WITH reranker
            chunks_rerank = retrieve_chunks(client, q, rerank_model="rerank-v4.0-pro")
            eval_rerank = evaluate_result(chunks_rerank, expected)
            
            results_baseline.append(eval_base)
            results_rerank.append(eval_rerank)
            
            # Display comparison
            base_status = f"Rank #{eval_base['rank']}" if eval_base['found'] else "NOT FOUND"
            rerank_status = f"Rank #{eval_rerank['rank']}" if eval_rerank['found'] else "NOT FOUND"
            
            print(f"  WITHOUT Rerank: {base_status} | Top: {eval_base['top_doc'][:45]}... (sim: {eval_base['similarity']:.3f})")
            print(f"  WITH Rerank:    {rerank_status} | Top: {eval_rerank['top_doc'][:45]}... (sim: {eval_rerank['similarity']:.3f})")
            
            # Show improvement
            if eval_rerank['found'] and not eval_base['found']:
                print(f"  >>> IMPROVEMENT: Found with reranker!")
            elif eval_rerank['found'] and eval_base['found'] and eval_rerank['rank'] < eval_base['rank']:
                print(f"  >>> IMPROVEMENT: Rank improved from #{eval_base['rank']} to #{eval_rerank['rank']}")
            elif eval_base['found'] and not eval_rerank['found']:
                print(f"  >>> REGRESSION: Lost with reranker!")
    
    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    
    found_base = sum(1 for r in results_baseline if r['found'])
    found_rerank = sum(1 for r in results_rerank if r['found'])
    
    avg_rank_base = sum(r['rank'] for r in results_baseline if r['found']) / found_base if found_base else 0
    avg_rank_rerank = sum(r['rank'] for r in results_rerank if r['found']) / found_rerank if found_rerank else 0
    
    print(f"\n{'Metric':<30} {'No Rerank':<20} {'With rerank-v4.0-pro':<20}")
    print("-" * 70)
    print(f"{'Expected docs found:':<30} {found_base}/9{'':<17} {found_rerank}/9")
    print(f"{'Avg rank when found:':<30} {avg_rank_base:.1f}{'':<19} {avg_rank_rerank:.1f}")
    
    # Count improvements
    improvements = 0
    regressions = 0
    for i in range(len(results_baseline)):
        if results_rerank[i]['found'] and not results_baseline[i]['found']:
            improvements += 1
        elif results_rerank[i]['found'] and results_baseline[i]['found']:
            if results_rerank[i]['rank'] < results_baseline[i]['rank']:
                improvements += 1
        elif results_baseline[i]['found'] and not results_rerank[i]['found']:
            regressions += 1
    
    print(f"\nImprovements: {improvements}")
    print(f"Regressions: {regressions}")
    
    if found_rerank > found_base or avg_rank_rerank < avg_rank_base:
        print("\n>>> VERDICT: Reranker IMPROVES retrieval quality!")
    elif found_rerank == found_base and avg_rank_rerank == avg_rank_base:
        print("\n>>> VERDICT: No significant difference")
    else:
        print("\n>>> VERDICT: Reranker may not help for this dataset")


if __name__ == "__main__":
    run_comparison_test()
