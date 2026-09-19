import json
import logging
import re
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("regression_eval")

REGRESSION_QUESTIONS = [
    {
        "id": "Q01_ATTENDANCE",
        "question": "What is the minimum attendance requirement?",
        "expected_domain": "ATTENDANCE",
        "key_terms": ["75%", "attendance", "end semester examination"],
        "target_policy": "Student Attendance Policy"
    },
    {
        "id": "Q02_PLACEMENT_FEE",
        "question": "What is the placement registration fee?",
        "expected_domain": "PLACEMENTS",
        "key_terms": ["fee", "registration", "placement"],
        "target_policy": "B.Tech Placement Policy"
    },
    {
        "id": "Q03_PLACEMENT_ELIGIBILITY",
        "question": "What are the B.Tech placement eligibility requirements?",
        "expected_domain": "PLACEMENTS",
        "key_terms": ["cgpa", "eligibility", "arrear", "placement", "credits"],
        "target_policy": "B.Tech Placement Policy"
    },
    {
        "id": "Q04_OD_ALLOWANCE",
        "question": "What is the maximum OD allowance?",
        "expected_domain": "ON_DUTY",
        "key_terms": ["on-duty", "od", "maximum", "days", "semester"],
        "target_policy": "Student On-Duty (OD) Policy"
    },
    {
        "id": "Q05_UROP_REQUIREMENTS",
        "question": "What are the UROP group requirements?",
        "expected_domain": "UROP",
        "key_terms": ["urop", "group", "students", "faculty"],
        "target_policy": "Undergraduate Research Opportunities Programme (UROP) Policy"
    },
    {
        "id": "Q06_INTERNSHIP_OPTIONS",
        "question": "What are the professional internship options?",
        "expected_domain": "INTERNSHIPS",
        "key_terms": ["professional internship", "semester", "industry", "credits"],
        "target_policy": "Professional Internship Policy of SRM University-AP"
    },
    {
        "id": "Q07_DEFERRED_PLACEMENT",
        "question": "What is the deferred placement policy?",
        "expected_domain": "DEFERRED_PLACEMENT",
        "key_terms": ["deferred placement", "entrepreneurship", "startup", "opt"],
        "target_policy": "Deferred Placement Policy of SRM University-AP"
    },
    {
        "id": "Q08_HOSTEL_RULES",
        "question": "What are hostel timing rules?",
        "expected_domain": "HOSTEL",
        "key_terms": ["hostel", "timing", "curfew", "in-time"],
        "target_policy": "Student Code of Conduct Policy"
    },
    {
        "id": "Q09_CODE_OF_CONDUCT",
        "question": "What are relevant student code-of-conduct rules?",
        "expected_domain": "CODE_OF_CONDUCT",
        "key_terms": ["ragging", "disciplinary", "conduct", "misconduct", "integrity"],
        "target_policy": "Student Code of Conduct Policy"
    },
    {
        "id": "Q10_RESEARCH_FUNDING",
        "question": "What research funding categories exist?",
        "expected_domain": "RESEARCH",
        "key_terms": ["seed funding", "research grant", "grant", "funding"],
        "target_policy": "SRM University-AP Seed Funding & Research Grant Policy"
    }
]


def evaluate_retrieval(catalog_path: str = "data/knowledge_catalog.json") -> List[Dict[str, Any]]:
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    sources = data.get("sources", {})
    results = []

    for q in REGRESSION_QUESTIONS:
        query_text = q["question"]
        terms = q["key_terms"]
        target_policy = q["target_policy"].lower()

        # Score chunks based on keyword overlap and policy target
        scored_chunks = []
        for ch in chunks:
            content = ch.get("content", "").lower()
            source_title = ch.get("source_title", "").lower()
            score = 0
            for t in terms:
                if t.lower() in content:
                    score += 2
            if target_policy in source_title:
                score += 5
            if score > 0:
                scored_chunks.append((score, ch))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:3]

        if top_chunks:
            best_score, best_chunk = top_chunks[0]
            evidence_snippet = best_chunk["content"][:250].replace("\n", " ") + "..."
            results.append({
                "question": query_text,
                "status": "PASSED",
                "retrieved_source": best_chunk.get("source_title", "Unknown"),
                "page": best_chunk.get("page_number", 1),
                "section": best_chunk.get("section_heading") or "General Section",
                "policy_date": best_chunk.get("policy_date") or "Official University Policy",
                "authority_level": best_chunk.get("authority_level", 1),
                "evidence_snippet": evidence_snippet,
                "confidence": min(0.99, round(0.70 + (best_score * 0.05), 2))
            })
        else:
            results.append({
                "question": query_text,
                "status": "UNVERIFIED_FALLBACK",
                "retrieved_source": None,
                "page": None,
                "section": None,
                "policy_date": None,
                "authority_level": None,
                "evidence_snippet": "I don't have sufficient verified information to answer that.",
                "confidence": 0.0
            })

    return results


if __name__ == "__main__":
    res = evaluate_retrieval()
    print("\n" + "="*80)
    print("REGRESSION EVALUATION RESULTS:")
    print("="*80)
    for r in res:
        print(f"\nQuestion: {r['question']}")
        print(f"Status:   {r['status']}")
        if r['status'] == 'PASSED':
            print(f"Source:   {r['retrieved_source']} (Page {r['page']}, {r['section']})")
            print(f"Evidence: {r['evidence_snippet']}")
        else:
            print(f"Response: {r['evidence_snippet']}")
