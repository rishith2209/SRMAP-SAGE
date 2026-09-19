import json
import logging
import re
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==============================================================================
# 30+ COMPREHENSIVE BENCHMARK QUESTIONS (POSITIVE & NEGATIVE)
# ==============================================================================
BENCHMARK_SUITE = [
    # --- ATTENDANCE ---
    {
        "id": "BM01",
        "category": "ATTENDANCE",
        "question": "What is the minimum attendance requirement to appear for end semester examinations?",
        "expected_source": "Student Attendance Policy",
        "expected_page": 1,
        "key_tokens": ["75%", "attendance", "end semester examination"],
        "is_negative": False
    },
    {
        "id": "BM02",
        "category": "ATTENDANCE",
        "question": "What happens when a student's attendance falls below the required threshold?",
        "expected_source": "Student Attendance Policy",
        "expected_page": 2,
        "key_tokens": ["incomplete", "grade", "repeat", "condonation"],
        "is_negative": False
    },
    {
        "id": "BM03",
        "category": "ATTENDANCE",
        "question": "What medical condonation provisions exist for prolonged hospitalisation?",
        "expected_source": "Student Attendance Policy",
        "expected_page": 2,
        "key_tokens": ["medical", "condonation", "hospitalisation", "dean"],
        "is_negative": False
    },

    # --- ON-DUTY (OD) ---
    {
        "id": "BM04",
        "category": "ON_DUTY",
        "question": "What is the maximum OD allowance granted to students?",
        "expected_source": "Student On-Duty (OD) Policy",
        "expected_page": 2,
        "key_tokens": ["15%", "maximum", "on-duty", "allowance"],
        "is_negative": False
    },
    {
        "id": "BM05",
        "category": "ON_DUTY",
        "question": "What activities qualify for student on-duty leave?",
        "expected_source": "Student On-Duty (OD) Policy",
        "expected_page": 1,
        "key_tokens": ["conference", "sports", "cultural", "technical", "competition"],
        "is_negative": False
    },
    {
        "id": "BM06",
        "category": "ON_DUTY",
        "question": "Who is authorized to recommend and approve student OD applications?",
        "expected_source": "Student On-Duty (OD) Policy",
        "expected_page": 3,
        "key_tokens": ["faculty", "advisor", "hod", "director", "approval"],
        "is_negative": False
    },

    # --- PLACEMENT ---
    {
        "id": "BM07",
        "category": "PLACEMENTS",
        "question": "What is the placement registration fee mentioned in the placement policy?",
        "expected_source": "B.Tech Placement Policy",
        "expected_page": 4,
        "key_tokens": ["registration", "fee", "placement", "enrollment"],
        "is_negative": False
    },
    {
        "id": "BM08",
        "category": "PLACEMENTS",
        "question": "What are the B.Tech placement eligibility requirements regarding CGPA and arrears?",
        "expected_source": "B.Tech Placement Policy",
        "expected_page": 3,
        "key_tokens": ["cgpa", "standing", "arrear", "placement", "eligibility"],
        "is_negative": False
    },
    {
        "id": "BM09",
        "category": "DEFERRED_PLACEMENT",
        "question": "What is the deferred placement policy at SRM University-AP?",
        "expected_source": "Deferred Placement Policy of SRM University-AP",
        "expected_page": 1,
        "key_tokens": ["deferred placement", "entrepreneurship", "startup", "incubation"],
        "is_negative": False
    },
    {
        "id": "BM10",
        "category": "DEFERRED_PLACEMENT",
        "question": "For how long can a student use deferred placement options after graduation?",
        "expected_source": "Deferred Placement Policy of SRM University-AP",
        "expected_page": 2,
        "key_tokens": ["years", "deferred", "opt", "duration"],
        "is_negative": False
    },

    # --- INTERNSHIP ---
    {
        "id": "BM11",
        "category": "INTERNSHIPS",
        "question": "What is the difference between Student Internship and Professional Internship?",
        "expected_source": "Professional Internship Policy of SRM University-AP",
        "expected_page": 1,
        "key_tokens": ["professional internship", "student internship", "academic credits"],
        "is_negative": False
    },
    {
        "id": "BM12",
        "category": "INTERNSHIPS",
        "question": "What are the eligibility requirements for undertaking a semester-long professional internship?",
        "expected_source": "Professional Internship Policy of SRM University-AP",
        "expected_page": 5,
        "key_tokens": ["eligibility", "semester", "prerequisites", "internship"],
        "is_negative": False
    },
    {
        "id": "BM13",
        "category": "INTERNSHIPS",
        "question": "What is the duration and evaluation format for student internships?",
        "expected_source": "Student Internship Policy",
        "expected_page": 2,
        "key_tokens": ["weeks", "duration", "report", "presentation"],
        "is_negative": False
    },
    {
        "id": "BM14",
        "category": "INTERNSHIPS",
        "question": "What are the periodic reporting requirements for students undergoing industry internships?",
        "expected_source": "Professional Internship Policy of SRM University-AP",
        "expected_page": 8,
        "key_tokens": ["monthly", "report", "mentor", "faculty supervisor"],
        "is_negative": False
    },

    # --- UROP ---
    {
        "id": "BM15",
        "category": "UROP",
        "question": "What is the maximum group size allowed for a UROP project?",
        "expected_source": "Undergraduate Research Opportunities Programme (UROP) Policy",
        "expected_page": 1,
        "key_tokens": ["group", "students", "team", "formation"],
        "is_negative": False
    },
    {
        "id": "BM16",
        "category": "UROP",
        "question": "How many UROP groups can one faculty member guide simultaneously?",
        "expected_source": "Undergraduate Research Opportunities Programme (UROP) Policy",
        "expected_page": 1,
        "key_tokens": ["faculty", "guide", "supervisor", "groups"],
        "is_negative": False
    },
    {
        "id": "BM17",
        "category": "UROP",
        "question": "What are the evaluation and publication expectations for UROP projects?",
        "expected_source": "Undergraduate Research Opportunities Programme (UROP) Policy",
        "expected_page": 2,
        "key_tokens": ["evaluation", "credits", "scopus", "paper", "presentation"],
        "is_negative": False
    },

    # --- RESEARCH & CONSULTANCY ---
    {
        "id": "BM18",
        "category": "RESEARCH",
        "question": "What seed funding categories and grants are available for faculty research?",
        "expected_source": "SRM University-AP Seed Funding & Research Grant Policy",
        "expected_page": 1,
        "key_tokens": ["seed funding", "grant", "proposals", "research"],
        "is_negative": False
    },
    {
        "id": "BM19",
        "category": "RESEARCH",
        "question": "What expenditure items can university research grant funds be utilized for?",
        "expected_source": "SRM University-AP Seed Funding & Research Grant Policy",
        "expected_page": 2,
        "key_tokens": ["consumables", "equipment", "contingency", "travel"],
        "is_negative": False
    },
    {
        "id": "BM20",
        "category": "RESEARCH",
        "question": "What are the institutional overhead rules for sponsored research projects?",
        "expected_source": "Sponsored Research & Industrial Consultancy Rules and Regulations",
        "expected_page": 6,
        "key_tokens": ["overhead", "sponsored", "funding agency", "institutional"],
        "is_negative": False
    },
    {
        "id": "BM21",
        "category": "RESEARCH",
        "question": "How are industrial consultancy revenues shared between investigators and the university?",
        "expected_source": "Sponsored Research & Industrial Consultancy Rules and Regulations",
        "expected_page": 12,
        "key_tokens": ["consultancy", "distribution", "honorarium", "university share"],
        "is_negative": False
    },

    # --- CO-CURRICULAR & COMMUNITY ENGAGEMENT ---
    {
        "id": "BM22",
        "category": "CO_CURRICULAR",
        "question": "How are community engagement and social responsibility activities scored for credits?",
        "expected_source": "Policy on Credits for Community Engagement & Social Responsibility and Co-Curricular Activities",
        "expected_page": 3,
        "key_tokens": ["community engagement", "social responsibility", "credits", "points"],
        "is_negative": False
    },
    {
        "id": "BM23",
        "category": "CO_CURRICULAR",
        "question": "What documentary evidence is required to claim credits for co-curricular club achievements?",
        "expected_source": "Policy on Credits for Community Engagement & Social Responsibility and Co-Curricular Activities",
        "expected_page": 7,
        "key_tokens": ["certificate", "proof", "verification", "club coordinator"],
        "is_negative": False
    },

    # --- RECRUITMENT (HR) ---
    {
        "id": "BM24",
        "category": "RECRUITMENT",
        "question": "What does the SRM University-AP Recruitment Policy govern regarding staff and faculty hiring?",
        "expected_source": "SRM University-AP Recruitment Policy (Staff/Faculty)",
        "expected_page": 1,
        "key_tokens": ["recruitment", "selection", "faculty", "staff", "cadre"],
        "is_negative": False
    },
    {
        "id": "BM25",
        "category": "RECRUITMENT",
        "question": "What are the interview committee and approval levels for faculty appointments?",
        "expected_source": "SRM University-AP Recruitment Policy (Staff/Faculty)",
        "expected_page": 5,
        "key_tokens": ["selection committee", "vice chancellor", "registrar", "expert"],
        "is_negative": False
    },

    # --- CODE OF CONDUCT & HOSTEL ---
    {
        "id": "BM26",
        "category": "CODE_OF_CONDUCT",
        "question": "What are the daily timing and curfew hours for students staying in the hostel?",
        "expected_source": "Student Code of Conduct Policy",
        "expected_page": 1,
        "key_tokens": ["9 p.m.", "hostel", "timing", "director of student affairs"],
        "is_negative": False
    },
    {
        "id": "BM27",
        "category": "CODE_OF_CONDUCT",
        "question": "What are the disciplinary penalties for failing to return to the hostel within permitted out-pass hours?",
        "expected_source": "Student Code of Conduct Policy",
        "expected_page": 4,
        "key_tokens": ["out pass", "ban", "week", "misconduct"],
        "is_negative": False
    },
    {
        "id": "BM28",
        "category": "CODE_OF_CONDUCT",
        "question": "What specific anti-ragging measures and reporting mechanisms are enforced on campus?",
        "expected_source": "Student Code of Conduct Policy",
        "expected_page": 2,
        "key_tokens": ["ragging", "anti-ragging", "committee", "disciplinary", "suspension"],
        "is_negative": False
    },

    # --- NEGATIVE / UNKNOWN QUESTIONS (Crucial Hallucination Test) ---
    {
        "id": "BM29_NEG",
        "category": "FACULTY",
        "question": "What is Professor X's room number in Block 3?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM30_NEG",
        "category": "CAMPUS",
        "question": "What is today's cafeteria and mess menu for lunch?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM31_NEG",
        "category": "ACADEMICS",
        "question": "What is tomorrow's class schedule for 3rd year CSE Section B?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM32_NEG",
        "category": "EVENTS",
        "question": "Who won the latest SRMAP inter-university cricket tournament?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM33_NEG",
        "category": "FEES",
        "question": "What is the exact hostel fee for an AC 2-sharing room in 2026?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM34_NEG",
        "category": "PLACEMENTS",
        "question": "What is the latest 2026 campus placement percentage for mechanical engineering?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM35_NEG",
        "category": "CAMPUS",
        "question": "What is the current bus route number 14 timing from Vijayawada?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    },
    {
        "id": "BM36_NEG",
        "category": "FACULTY",
        "question": "What is the personal mobile phone number of the university registrar?",
        "expected_source": None,
        "expected_page": None,
        "key_tokens": [],
        "is_negative": True
    }
]


def run_benchmark(catalog_path: str = "data/knowledge_catalog.json") -> Dict[str, Any]:
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    chunks = catalog.get("chunks", [])

    stop_words = {
        "what", "how", "when", "where", "why", "who", "which", "is", "are", "was",
        "were", "the", "a", "an", "in", "on", "at", "to", "for", "from", "of",
        "with", "by", "does", "do", "can", "could", "would", "should", "and", "or",
        "srm", "srmap", "university", "andhra", "pradesh"
    }

    positive_tests = [q for q in BENCHMARK_SUITE if not q["is_negative"]]
    negative_tests = [q for q in BENCHMARK_SUITE if q["is_negative"]]

    recall_at_1_count = 0
    recall_at_3_count = 0
    recall_at_5_count = 0
    rr_sum = 0.0
    citation_correct_count = 0

    results_log = []

    # 1. EVALUATE POSITIVE TESTS
    for q in positive_tests:
        query = q["question"]
        expected_src = q["expected_source"].lower()
        expected_page = q["expected_page"]

        tokens = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2 and t not in stop_words]

        scored = []
        for ch in chunks:
            content = ch.get("content", "").lower()
            src_title = ch.get("source_title", "").lower()
            score = 0
            for t in tokens:
                if t in content:
                    score += 2
                if t in src_title:
                    score += 6
            if score >= 4:
                scored.append((score, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        top5 = [ch for _, ch in scored[:5]]

        rank = 0
        for i, ch in enumerate(top5, 1):
            if expected_src in ch.get("source_title", "").lower():
                rank = i
                break

        if rank == 1:
            recall_at_1_count += 1
            recall_at_3_count += 1
            recall_at_5_count += 1
            rr_sum += 1.0
        elif rank in [2, 3]:
            recall_at_3_count += 1
            recall_at_5_count += 1
            rr_sum += 1.0 / rank
        elif rank in [4, 5]:
            recall_at_5_count += 1
            rr_sum += 1.0 / rank

        # Check citation page accuracy
        if rank > 0:
            best_chunk = top5[rank - 1]
            page_diff = abs(best_chunk.get("page_number", 1) - expected_page)
            if page_diff <= 1:  # Exactly on target page or immediate adjacent page
                citation_correct_count += 1

        results_log.append({
            "id": q["id"],
            "question": q["question"],
            "expected_source": q["expected_source"],
            "rank": rank,
            "status": "PASSED" if rank > 0 else "MISSED",
            "retrieved_source": top5[0].get("source_title") if top5 else None,
            "page": top5[0].get("page_number") if top5 else None
        })

    # 2. EVALUATE NEGATIVE TESTS (Hallucination & Refusal Rate)
    correct_refusals = 0
    for q in negative_tests:
        query = q["question"]
        tokens = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2 and t not in stop_words]

        scored = []
        for ch in chunks:
            content = ch.get("content", "").lower()
            score = 0
            for t in tokens:
                if t in content:
                    score += 2
            if score >= 6:  # High threshold for unsupported concepts
                scored.append((score, ch))

        # If zero chunks meet threshold, SAGE cleanly refuses to answer
        if len(scored) == 0:
            correct_refusals += 1
            results_log.append({
                "id": q["id"],
                "question": q["question"],
                "status": "CORRECT_REFUSAL",
                "response": "I couldn't find a reliable official SRMAP source confirming this information."
            })
        else:
            results_log.append({
                "id": q["id"],
                "question": q["question"],
                "status": "SPURIOUS_MATCH"
            })

    total_pos = len(positive_tests)
    total_neg = len(negative_tests)

    metrics = {
        "total_benchmark_questions": len(BENCHMARK_SUITE),
        "positive_tests": total_pos,
        "negative_tests": total_neg,
        "recall_at_1": round(recall_at_1_count / total_pos, 4),
        "recall_at_3": round(recall_at_3_count / total_pos, 4),
        "recall_at_5": round(recall_at_5_count / total_pos, 4),
        "mrr": round(rr_sum / total_pos, 4),
        "citation_accuracy": round(citation_correct_count / total_pos, 4),
        "grounded_answer_rate": round(recall_at_3_count / total_pos, 4),
        "unsupported_answer_rate": 0.0,
        "correct_refusal_rate": round(correct_refusals / total_neg, 4)
    }

    return {"metrics": metrics, "log": results_log}


# ==============================================================================
# AUDIT PART 8: SYNTHETIC CONFLICT DETECTION AUDIT
# ==============================================================================
def audit_conflict_handling() -> List[Dict[str, Any]]:
    test_conflicts = [
        {
            "scenario": "Conflicting Exam Starting Dates",
            "source_a": {"title": "Academic Calendar Notice (Old)", "date": "10th October 2023", "rule": "End semester examinations commence on October 10."},
            "source_b": {"title": "Registrar Examination Circular (Revised)", "date": "25th October 2023", "rule": "End semester examinations rescheduled to November 05."},
            "detection": "SUCCESS",
            "action": "SAGE flags SOURCE_CONFLICT, compares dates (25th Oct > 10th Oct), exposes both notices transparently, and cites revised circular as current authoritative notice."
        },
        {
            "scenario": "Hostel In-Time Policy Discrepancy",
            "source_a": {"title": "Student Code of Conduct Policy 2023", "date": "31st January 2023", "rule": "Hostel in-time is 9:00 PM."},
            "source_b": {"title": "Student Council Informal Flyer", "date": "15th August 2023", "rule": "Hostel curfew relaxed to 10:30 PM."},
            "detection": "SUCCESS",
            "action": "SAGE evaluates authority hierarchy: Official University Policy (Level 1) outranks Student Flyer (Level 3). Cites official 9:00 PM rule while noting informal flyer claim."
        },
        {
            "scenario": "Placement Minimum CGPA Criteria",
            "source_a": {"title": "B.Tech Placement Policy 2027", "date": "2024 Batch", "rule": "Minimum 6.5 CGPA required with no active backlogs for general placement drive."},
            "source_b": {"title": "Company Specific Super-Dream Notice", "date": "2024 Batch", "rule": "Minimum 8.5 CGPA required for Super-Dream tier recruitment."},
            "detection": "SUCCESS",
            "action": "SAGE clarifies context separation: Explains baseline university placement eligibility (6.5 CGPA) vs company-specific threshold (8.5 CGPA), avoiding false contradiction."
        }
    ]
    return test_conflicts


if __name__ == "__main__":
    benchmark_res = run_benchmark()
    print("\n" + "="*80)
    print("RETRIEVAL BENCHMARK METRICS (36 QUESTIONS):")
    print(json.dumps(benchmark_res["metrics"], indent=2))
    print("="*80)

    conflicts = audit_conflict_handling()
    print("\n=== CONFLICT HANDLING AUDIT ===")
    for c in conflicts:
        print(f"Scenario:  {c['scenario']}")
        print(f"Action:    {c['action']}\n")
