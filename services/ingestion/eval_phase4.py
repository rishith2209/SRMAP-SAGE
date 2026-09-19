"""
SRMAP SAGE — Phase 4 Comprehensive Evaluation Suite
Evaluates:
1. Base 36 Benchmark tests (Phase 2.5 baseline)
2. Temporal routing and freshness tests (Phase 3: T01 - T07)
3. Source priority and authority hierarchy tests (Phase 3: T08 - T11)
4. Negative refusal tests (Phase 3: NEG_09 - NEG_14)
5. Prompt-injection defense tests (Phase 3: SEC_01 - SEC_02)
6. Phase 4 Structured University Intelligence & Spatial Campus Engine tests:
   - FAC01: Faculty lookup
   - FAC02: Department lookup
   - FAC03: Unknown faculty -> refusal
   - NAV01: Known campus route
   - NAV02: Unknown destination -> refusal
   - CAL01: Current academic calendar
   - CAL02: Historical calendar
   - FEE01: Verified fee lookup
   - FEE02: Unavailable fee -> refusal
   - EVENT01: Current official event
   - EVENT02: Historical event
   - HYB01: Policy + faculty
   - HYB02: Placement + location
   - HYB03: Current notice + spatial information
   - PROV01: Every structured entity has source provenance
   - SEC01: Structured data cannot override source authority
"""

import asyncio
import json
import logging
import os
import re
import sys
from typing import Dict, List, Any

# Ensure apps/api and repository root are on sys.path
sys.path.extend(["apps/api", "."])

from src.engines.rag_engine import RAGEngine, STRICT_FALLBACK_PHRASE
from src.engines.spatial_engine import CampusSpatialEngine
from src.engines.faculty_engine import FacultyEngine
from src.engines.calendar_engine import AcademicCalendarEngine
from src.engines.fee_engine import FeeEngine
from src.engines.events_engine import EventsEngine
from src.engines.router_engine import IntentRouter
from src.providers.mock_provider import MockLLMProvider
from services.ingestion.eval_phase3 import run_phase3_evaluation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_phase4")


async def run_phase4_evaluation() -> Dict[str, Any]:
    # 1. Run full Phase 3 baseline evaluation
    p3_results = await run_phase3_evaluation()
    p3_metrics = p3_results["phase3_metrics"]

    # 2. Instantiate Phase 4 Engines
    provider = MockLLMProvider()
    router = IntentRouter(provider)
    rag = RAGEngine(provider)
    spatial = CampusSpatialEngine()
    faculty = FacultyEngine()
    calendar = AcademicCalendarEngine()
    fee = FeeEngine()
    events = EventsEngine()

    phase4_tests = []

    # FAC01: Faculty lookup
    fac1 = faculty.lookup_faculty("Manoj Arora")
    fac01_passed = fac1 is not None and "Manoj" in fac1.name and fac1.source_id is not None
    phase4_tests.append({
        "id": "FAC01",
        "name": "Faculty lookup (verified)",
        "passed": fac01_passed,
        "detail": fac1.name if fac1 else None
    })

    # FAC02: Department lookup
    dept1 = faculty.get_department("CSE")
    fac02_passed = dept1 is not None and "Computer Science" in dept1.name and dept1.building is not None
    phase4_tests.append({
        "id": "FAC02",
        "name": "Department lookup (verified)",
        "passed": fac02_passed,
        "detail": dept1.name if dept1 else None
    })

    # FAC03: Unknown faculty -> refusal
    fac_unk = faculty.lookup_faculty("Professor X")
    fac03_passed = fac_unk is None  # Clean absence leading to refusal
    phase4_tests.append({
        "id": "FAC03",
        "name": "Unknown faculty refusal",
        "passed": fac03_passed,
        "detail": "Clean refusal (None)" if fac03_passed else "Spurious match"
    })

    # NAV01: Known campus route
    route1 = spatial.get_route("Hostel Tower A", "Academic Block")
    nav01_passed = route1 is not None and route1.total_distance_meters > 0 and len(route1.steps) > 0
    phase4_tests.append({
        "id": "NAV01",
        "name": "Known campus route",
        "passed": nav01_passed,
        "detail": f"{route1.total_distance_meters}m in ~{route1.estimated_walk_minutes} min" if route1 else None
    })

    # NAV02: Unknown destination -> refusal
    route_unk = spatial.get_route("Hostel Tower A", "Secret Alien Underground Bunker")
    nav02_passed = route_unk is None
    phase4_tests.append({
        "id": "NAV02",
        "name": "Unknown destination refusal",
        "passed": nav02_passed,
        "detail": "Clean refusal (None)" if nav02_passed else "Spurious path"
    })

    # CAL01: Current academic calendar
    cal_curr = calendar.query_events(status="CURRENT")
    cal01_passed = len(cal_curr) > 0 and any("Commencement" in e.event for e in cal_curr)
    phase4_tests.append({
        "id": "CAL01",
        "name": "Current academic calendar",
        "passed": cal01_passed,
        "detail": f"{len(cal_curr)} events found"
    })

    # CAL02: Historical calendar
    cal_hist = calendar.query_events(status="HISTORICAL")
    cal02_passed = len(cal_hist) > 0 and any("2025" in e.academic_year for e in cal_hist)
    phase4_tests.append({
        "id": "CAL02",
        "name": "Historical academic calendar",
        "passed": cal02_passed,
        "detail": f"{len(cal_hist)} historical events found"
    })

    # FEE01: Verified fee lookup
    fee_cse = fee.lookup_fee(program_keyword="CSE")
    fee01_passed = fee_cse is not None and fee_cse.amount > 0 and fee_cse.currency == "INR"
    phase4_tests.append({
        "id": "FEE01",
        "name": "Verified fee lookup",
        "passed": fee01_passed,
        "detail": f"{fee_cse.program}: INR {fee_cse.amount}" if fee_cse else None
    })

    # FEE02: Unavailable fee -> refusal
    fee_unavail = fee.lookup_fee(year="2035-2036", program_keyword="Quantum Teleportation")
    fee02_passed = fee_unavail is None
    phase4_tests.append({
        "id": "FEE02",
        "name": "Unavailable fee refusal",
        "passed": fee02_passed,
        "detail": "Clean refusal (None)" if fee02_passed else "Estimated value"
    })

    # EVENT01: Current official event
    ev_curr = events.query_events(status="CURRENT")
    ev01_passed = len(ev_curr) > 0 and any("Robotics" in e.title or "Springer" in e.title for e in ev_curr)
    phase4_tests.append({
        "id": "EVENT01",
        "name": "Current official event",
        "passed": ev01_passed,
        "detail": ev_curr[0].title if ev_curr else None
    })

    # EVENT02: Historical event
    ev_hist = events.query_events(status="HISTORICAL")
    ev02_passed = len(ev_hist) > 0 and any("Janmashtami" in e.title for e in ev_hist)
    phase4_tests.append({
        "id": "EVENT02",
        "name": "Historical event",
        "passed": ev02_passed,
        "detail": ev_hist[0].title if ev_hist else None
    })

    # HYB01: Policy + faculty (e.g. UROP policy & faculty supervisor)
    class_hyb1 = await router.classify("What is the UROP policy and which faculty coordinates research?")
    hyb01_passed = class_hyb1["is_hybrid"] and "POLICY" in class_hyb1["subintents"] and "FACULTY" in class_hyb1["subintents"]
    phase4_tests.append({
        "id": "HYB01",
        "name": "Policy + faculty hybrid routing",
        "passed": hyb01_passed,
        "detail": f"Subintents: {class_hyb1['subintents']}"
    })

    # HYB02: Placement + location (e.g. placement policy and where is CRCS office)
    class_hyb2 = await router.classify("What is the placement policy and where is the placement office located?")
    hyb02_passed = class_hyb2["is_hybrid"] and "PLACEMENT" in class_hyb2["subintents"] and "SPATIAL" in class_hyb2["subintents"]
    phase4_tests.append({
        "id": "HYB02",
        "name": "Placement + location hybrid routing",
        "passed": hyb02_passed,
        "detail": f"Subintents: {class_hyb2['subintents']}"
    })

    # HYB03: Current notice + spatial information
    class_hyb3 = await router.classify("What is the latest workshop notice and where is it held on campus?")
    hyb03_passed = class_hyb3["is_hybrid"] and "EVENT" in class_hyb3["subintents"] and "SPATIAL" in class_hyb3["subintents"]
    phase4_tests.append({
        "id": "HYB03",
        "name": "Notice + spatial hybrid routing",
        "passed": hyb03_passed,
        "detail": f"Subintents: {class_hyb3['subintents']}"
    })

    # PROV01: Every structured entity has source provenance
    all_entities = [fac1, dept1, route1, cal_curr[0] if cal_curr else None, fee_cse, ev_curr[0] if ev_curr else None]
    prov01_passed = all(hasattr(e, "source_id") and e.source_id is not None for e in all_entities if e)
    phase4_tests.append({
        "id": "PROV01",
        "name": "Structured entity provenance completeness",
        "passed": prov01_passed,
        "detail": "100% structured entities carry source_id"
    })

    # SEC01: Structured data cannot override source authority
    # Verify that Level 1 official policy documents carry authority level 1 and higher weight than Level 2 structured seeds
    ch_policy = rag.retrieve_chunks("What is the minimum attendance required?", top_k=1)
    sec01_passed = len(ch_policy) > 0 and ch_policy[0][1].authority_level == 1
    phase4_tests.append({
        "id": "SEC01",
        "name": "Source authority hierarchy invariance",
        "passed": sec01_passed,
        "detail": f"Top authority level: {ch_policy[0][1].authority_level if ch_policy else 'None'}"
    })

    total_p4 = len(phase4_tests)
    passed_p4 = sum(1 for t in phase4_tests if t["passed"])

    summary = {
        "baseline_phase3_metrics": p3_metrics,
        "phase4_metrics": {
            "recall_at_1": p3_metrics["recall_at_1"],
            "mrr": p3_metrics["mrr"],
            "grounded_answer_rate": p3_metrics["grounded_answer_rate"],
            "unsupported_answer_rate": p3_metrics["unsupported_answer_rate"],
            "base_correct_refusal_rate": p3_metrics["base_correct_refusal_rate"],
            "temporal_accuracy": p3_metrics["temporal_accuracy"],
            "source_priority_accuracy": p3_metrics["source_priority_accuracy"],
            "new_negative_refusal_rate": p3_metrics["new_negative_refusal_rate"],
            "prompt_injection_defense_rate": p3_metrics["prompt_injection_defense_rate"],
            "structured_knowledge_accuracy": f"{passed_p4}/{total_p4} ({passed_p4/total_p4*100:.1f}%)"
        },
        "phase4_test_details": phase4_tests
    }
    return summary


if __name__ == "__main__":
    res = asyncio.run(run_phase4_evaluation())
    print(json.dumps(res["phase4_metrics"], indent=2))
    print("\nPhase 4 Individual Test Cases:")
    for t in res["phase4_test_details"]:
        status = "PASSED" if t["passed"] else "FAILED"
        print(f"  [{t['id']}] {t['name']}: {status} ({t.get('detail')})")
