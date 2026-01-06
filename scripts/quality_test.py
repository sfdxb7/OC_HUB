"""
Quality Test Script for RAGFlow Retrieval
Tests complex questions against the indexed documents.
"""
import httpx
import json
from typing import Optional

# Configuration
RAGFLOW_URL = "http://localhost:9380"
RAGFLOW_API_KEY = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
DATASET_ID = "eceb7b32e83111f080689a6078826a72"

# Complex test questions covering different aspects
TEST_QUESTIONS = [
    # Strategic/Policy Questions
    {
        "question": "What are the key differences between the EU AI Act and US approaches to AI regulation, and what implications does this have for global AI governance?",
        "category": "Policy & Regulation",
        "expected_topics": ["EU AI Act", "regulation", "governance", "compliance"]
    },
    {
        "question": "How are leading organizations measuring ROI and business value from their generative AI investments, and what metrics are most commonly used?",
        "category": "Business Value",
        "expected_topics": ["ROI", "value", "metrics", "investment", "generative AI"]
    },
    {
        "question": "What are the critical success factors for scaling AI from pilot projects to enterprise-wide deployment, and what are the most common failure modes?",
        "category": "AI Scaling",
        "expected_topics": ["scaling", "enterprise", "deployment", "pilot", "transformation"]
    },
    # Technical Questions
    {
        "question": "What are the emerging best practices for responsible AI development, including bias mitigation, transparency, and accountability frameworks?",
        "category": "Responsible AI",
        "expected_topics": ["responsible", "bias", "transparency", "ethics", "accountability"]
    },
    {
        "question": "How are governments leveraging AI for public sector transformation, and what are specific use cases in citizen services?",
        "category": "Government AI",
        "expected_topics": ["government", "public sector", "citizen", "services", "transformation"]
    },
    # Regional/Strategic Questions
    {
        "question": "What strategies are countries using to develop sovereign AI capabilities and reduce dependence on foreign AI providers?",
        "category": "Sovereign AI",
        "expected_topics": ["sovereign", "national", "independence", "capability", "strategy"]
    },
    {
        "question": "What workforce and talent strategies are organizations adopting to address the AI skills gap, including upskilling and reskilling programs?",
        "category": "AI Talent",
        "expected_topics": ["talent", "skills", "workforce", "training", "upskilling"]
    },
    # Cross-cutting Questions
    {
        "question": "What are the projected economic impacts of AI adoption across different industries by 2030, and which sectors will see the highest productivity gains?",
        "category": "Economic Impact",
        "expected_topics": ["economic", "productivity", "impact", "2030", "industry"]
    },
    {
        "question": "How are organizations building AI governance structures, including AI ethics boards, risk frameworks, and oversight mechanisms?",
        "category": "AI Governance",
        "expected_topics": ["governance", "ethics", "risk", "oversight", "framework"]
    },
    {
        "question": "What are the key findings on AI maturity levels across organizations, and what distinguishes AI leaders from laggards?",
        "category": "AI Maturity",
        "expected_topics": ["maturity", "leaders", "adoption", "capabilities", "performance"]
    },
]


def retrieve_chunks(client: httpx.Client, question: str, top_k: int = 5) -> list:
    """Retrieve relevant chunks for a question."""
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


def calculate_relevance_score(chunks: list, expected_topics: list) -> tuple:
    """Calculate how many expected topics appear in retrieved chunks."""
    if not chunks:
        return 0, []
    
    all_content = " ".join([c.get("content", "").lower() for c in chunks])
    found_topics = []
    
    for topic in expected_topics:
        if topic.lower() in all_content:
            found_topics.append(topic)
    
    score = len(found_topics) / len(expected_topics) if expected_topics else 0
    return score, found_topics


def run_quality_test():
    """Run all test questions and evaluate results."""
    print("=" * 80)
    print("RAGFLOW RETRIEVAL QUALITY TEST")
    print("=" * 80)
    print()
    
    results = []
    
    with httpx.Client() as client:
        for i, test in enumerate(TEST_QUESTIONS, 1):
            question = test["question"]
            category = test["category"]
            expected = test["expected_topics"]
            
            print(f"\n[{i}/{len(TEST_QUESTIONS)}] {category}")
            print(f"Q: {question[:100]}...")
            print("-" * 60)
            
            # Retrieve chunks
            chunks = retrieve_chunks(client, question)
            
            if not chunks:
                print("  NO RESULTS FOUND")
                results.append({
                    "category": category,
                    "chunks": 0,
                    "relevance": 0,
                    "avg_similarity": 0,
                    "sources": []
                })
                continue
            
            # Calculate metrics
            relevance, found = calculate_relevance_score(chunks, expected)
            similarities = [c.get("similarity", 0) for c in chunks]
            avg_sim = sum(similarities) / len(similarities) if similarities else 0
            
            # Get unique sources
            sources = list(set([c.get("document_keyword", c.get("document_name", "unknown"))[:40] for c in chunks]))
            
            print(f"  Retrieved: {len(chunks)} chunks")
            print(f"  Avg Similarity: {avg_sim:.3f}")
            print(f"  Topic Coverage: {relevance:.0%} ({len(found)}/{len(expected)})")
            print(f"  Found Topics: {', '.join(found) if found else 'None'}")
            print(f"  Sources: {', '.join(sources[:3])}")
            
            # Show top chunk preview
            if chunks:
                top_chunk = chunks[0]
                preview = top_chunk.get("content", "")[:200].replace("\n", " ")
                print(f"  Top Result: \"{preview}...\"")
            
            results.append({
                "category": category,
                "chunks": len(chunks),
                "relevance": relevance,
                "avg_similarity": avg_sim,
                "sources": sources
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_questions = len(results)
    questions_with_results = sum(1 for r in results if r["chunks"] > 0)
    avg_relevance = sum(r["relevance"] for r in results) / total_questions if total_questions else 0
    avg_similarity = sum(r["avg_similarity"] for r in results if r["avg_similarity"] > 0)
    avg_similarity = avg_similarity / questions_with_results if questions_with_results else 0
    
    print(f"\nQuestions Tested: {total_questions}")
    print(f"Questions with Results: {questions_with_results}/{total_questions} ({questions_with_results/total_questions:.0%})")
    print(f"Average Topic Coverage: {avg_relevance:.0%}")
    print(f"Average Similarity Score: {avg_similarity:.3f}")
    
    # Quality grade
    if avg_relevance >= 0.7 and avg_similarity >= 0.3:
        grade = "EXCELLENT"
    elif avg_relevance >= 0.5 and avg_similarity >= 0.25:
        grade = "GOOD"
    elif avg_relevance >= 0.3 and avg_similarity >= 0.2:
        grade = "ACCEPTABLE"
    else:
        grade = "NEEDS IMPROVEMENT"
    
    print(f"\nOverall Quality: {grade}")
    
    # Detailed breakdown
    print("\n" + "-" * 40)
    print("BY CATEGORY:")
    for r in results:
        status = "OK" if r["chunks"] > 0 and r["relevance"] >= 0.5 else "LOW" if r["chunks"] > 0 else "FAIL"
        print(f"  [{status}] {r['category']}: {r['relevance']:.0%} coverage, {r['avg_similarity']:.3f} similarity")
    
    return results


if __name__ == "__main__":
    run_quality_test()
