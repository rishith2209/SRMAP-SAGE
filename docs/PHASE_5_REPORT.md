# SRMAP SAGE — PHASE 5 AUDIT REPORT
## Agentic Evidence Orchestration & Self-Verifying Answer Engine

**Status:** Phase 5 COMPLETE & VERIFIED  
**Date:** September 20, 2026  
**Git Commit Baseline:** `27cafc8` (Phase 4 Baseline)  
**Execution Mode:** Autonomous Self-Verifying Agentic Evidence Orchestrator  
**Core Invariant:**
$$\text{EVIDENCE} \longrightarrow \text{REASONING} \longrightarrow \text{ANSWER}$$
$$\text{Never: } \text{LLM} \longrightarrow \text{GUESS} \longrightarrow \text{ANSWER}$$

---

## 1. Executive Summary & Verification Metrics

Phase 5 transforms SRMAP SAGE from a static multi-engine router into a bounded, self-verifying evidence orchestrator. The LLM acts strictly as a synthesizer over verified factual evidence units (`EvidenceItem`), never as an unconstrained autonomous agent or hallucinated database.

Every single metric from Phase 2.5, Phase 3, and Phase 4 has been maintained with zero regression across 70 total evaluated automated tests:

| Metric Category | Phase 3 Baseline | Phase 4 Verified | Phase 5 Current Verified | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@1** | 100.0% | 100.0% | **100.0%** | **PRESERVED** |
| **Recall@3** | 100.0% | 100.0% | **100.0%** | **PRESERVED** |
| **Recall@5** | 100.0% | 100.0% | **100.0%** | **PRESERVED** |
| **Mean Reciprocal Rank (MRR)** | 1.0000 | 1.0000 | **1.0000** | **PRESERVED** |
| **Grounded Answer Rate** | 100.0% | 100.0% | **100.0%** | **PRESERVED** |
| **Unsupported / Hallucination Rate** | 0.0% | 0.0% | **0.0%** | **ZERO TOLERANCE** |
| **Base Correct Refusal Rate** | 100.0% | 100.0% | **100.0%** | **PRESERVED** |
| **Temporal Query Accuracy (T01–T07)** | 100.0% (7/7) | 100.0% (7/7) | **100.0% (7/7)** | **PRESERVED** |
| **Source Priority Accuracy (T08–T11)** | 100.0% (4/4) | 100.0% (4/4) | **100.0% (4/4)** | **PRESERVED** |
| **Negative Out-of-Scope Refusal Rate** | 100.0% (6/6) | 100.0% (6/6) | **100.0% (6/6)** | **PRESERVED** |
| **Prompt Injection Defense Rate** | 100.0% (2/2) | 100.0% (2/2) | **100.0% (2/2)** | **PRESERVED** |
| **Phase 4 Structured Knowledge Suite** | — | 100.0% (16/16) | **100.0% (16/16)** | **PRESERVED** |
| **Phase 5 Agentic Orchestrator Suite** | — | — | **100.0% (32/32)** | **VERIFIED** |
| **Pytest Suite** | 6/6 | 6/6 | **6/6 passed** | **VERIFIED** |

---

## 2. Agent Architecture & Orchestration Flow

SAGE implements a deterministic 10-step bounded orchestration loop:

```
[1. UNDERSTAND]   Analyze user prompt, entity tokens, and temporal constraints
      ↓
[2. PLAN]         Generate typed QueryPlan (intents, engines, budgets, verification requirements)
      ↓
[3. ROUTE]        Dispatch to designated domain engines (never an unrestricted autonomous loop)
      ↓
[4. RETRIEVE]     Query domain engines bounded by MAX_ENGINE_CALLS = 8
      ↓
[5. STANDARDIZE]  Convert all engine outputs into standardized EvidenceItem instances
      ↓
[6. CONFLICT]     Semantic-aware ConflictDetector identifies contradictions vs complementary rules
      ↓
[7. SYNTHESIZE]   Draft provisional response strictly grounded in verified EvidenceItems
      ↓
[8. VERIFY]       Claim-level SelfVerificationEngine extracts factual propositions and discards unsupported claims
      ↓
[9. CONTRACT]     Assemble formal AnswerContract (answer, evidence, sources, caveats, trace)
      ↓
[10. ANSWER]      Return structured ChatQueryResponse with AdaptiveCard & verified badges
```

### Specialized Engine Specialization
Deterministic engines remain sovereign for their domain facts; the LLM never overrides their data:
- **`DOCUMENT_RAG`**: Institutional regulations, policies, student handbooks (Authority Level 1).
- **`FACULTY_ENGINE`**: Verified leadership, HODs, deans, and cabin data from official circulars (Authority Level 2).
- **`SPATIAL_ENGINE`**: Topological NetworkX graph for campus routes, distances, and walking times (Authority Level 2).
- **`CALENDAR_ENGINE`**: Current vs historical semester milestones (Authority Level 1).
- **`FEE_ENGINE`**: Official admissions and fee schedules (Authority Level 1).
- **`EVENT_ENGINE`**: Official university events, workshops, and registrations (Authority Level 1).
- **`COMMUNITY_ENGINE`**: User-submitted discrepancy reports (Authority Level 5, lead status only).
- **`LIVE_WEB_ENGINE`**: Real-time university news and notices (Authority Level 1/4).

---

## 3. Standardized Evidence Model (`EvidenceItem`)

Every factual claim in SAGE must be backed by one or more `EvidenceItem` records:

```python
class EvidenceItem(BaseModel):
    id: str
    source_id: str
    source_type: str            # official_pdf_policy, structured_dataset, web_source, community_report
    authority_level: int        # 1 (Signed Gazette/Policy) to 5 (Community Submission)
    title: str
    url: Optional[str]
    page: Optional[int]
    excerpt: str
    published_at: Optional[str]
    verified_at: Optional[str]
    freshness_status: str       # CURRENT, SUPERSEDED, HISTORICAL, UNVERIFIED
    confidence: float           # RETRIEVAL/RELEVANCE SIGNAL ONLY — never signifies truth
    engine: str                 # Engine provenance identifier
    content_hash: str           # SHA-256 integrity hash
    domain: Optional[str]
    entity_scope: Optional[str]
```

### Critical Rule on Confidence:
`EvidenceItem.confidence` is solely an algorithmic retrieval and ranking signal. It is strictly forbidden from overriding:
1. Source authority levels
2. Publication and effective dates
3. Explicit supersession relationships
4. Source provenance or verified timestamps
5. Genuine conflict status

---

## 4. Semantic Conflict Detection & Authority Resolution

The `ConflictDetector` engine avoids naive text-matching and performs semantically aware disambiguation:

1. **Complementary Domain Scopes:**
   - General placement policy baseline (e.g., *6.0 CGPA for registration*) vs company job specifications (e.g., *Google requires 8.5 CGPA*) are classified as `NO_CONFLICT`.
   - University event page and social media announcements are recognized as complementary multi-channel notices covering the same event (`NO_CONFLICT`).
2. **Authority Conflict Resolution:**
   - Level 1 official policy documents unconditionally override Level 5 community submissions or third-party web claims addressing the same topic (`AUTHORITY_CONFLICT`).
3. **Temporal Supersession:**
   - When a newer official circular explicitly revokes or updates an archived circular, the older record is marked `SUPERSEDED` and the newer record prevails (`TEMPORAL_UPDATE`).
   - A document being newer does **not** automatically grant supersession rights without verified revoking clauses or matching administrative scope (`TEMPORAL_RELATIONSHIP_UNKNOWN`).
4. **Unresolved Contradictions:**
   - If two Level 1 official documents contradict each other on numbers or rules without an established date hierarchy or revoking clause, SAGE flags `UNRESOLVED` and halts definitive claims (`CONFLICT_UNRESOLVED`).

---

## 5. Claim-Level Self-Verification Engine

The `SelfVerificationEngine` enforces granular verification at the proposition level rather than evaluating entire paragraphs:

1. **Claim Extraction:** Synthesized text is decomposed into discrete propositions.
2. **Numerical & Propositional Integrity:** Checks every percentage, date, monetary amount, and proper noun against underlying evidence excerpts.
3. **Rejection of Inferred Numbers:** If a draft mentions *"92% attendance"* while evidence specifies *"75%"*, the proposition is rejected.
4. **Unsupported Claim Pruning:** If a draft includes an unsupported assertion (*"students will receive a free laptop"*), the verifier strips that specific claim while preserving supported claims, marking status as `PARTIALLY_VERIFIED`.
5. **Clean Refusal Fallback:** If zero claims are supported by verified evidence, the answer is replaced with an official refusal message (`REFUSED`).

---

## 6. Structured Refusal Engine

When facts are missing or unverified, SAGE refuses through structured reason codes accompanied by the exact official document needed:

| Refusal Reason Code | Trigger Condition | Example User Response |
| :--- | :--- | :--- |
| `INSUFFICIENT_EVIDENCE` | No verified documents cover inquiry | *"I couldn't find a reliable official SRMAP source confirming this information."* |
| `SOURCE_UNAVAILABLE` | Specific circular exists but not indexed | *"The specific official document covering bus timetable is currently not published or indexed in SAGE."* |
| `AUTHENTICATION_REQUIRED` | Detail requires student login | *"This information requires authentication through internal SRMAP portals (ERP/HRD)."* |
| `CONFLICT_UNRESOLVED` | Two Level 1 sources contradict | *"I found conflicting official records regarding attendance rules, and no superseding circular has been established."* |
| `OUTDATED_INFORMATION` | Only archived records exist | *"The available records are archived historical notices. No verified active circular is on record."* |
| `UNKNOWN_ENTITY` | Faculty, room, or location unknown | *"The requested entity is not registered in the official university directory or campus spatial registry."* |
| `UNVERIFIED_CURRENT_INFORMATION` | Future/unverified fee or route | *"I don't have a verified official source for 2026 fee schedule. Official schedules have not yet been verified."* |

---

## 7. Tool Call Budgets & Execution Safety

To guarantee deterministic termination, hard bounds are enforced globally across each query:
- `MAX_RETRIEVAL_ITERATIONS = 3`
- `MAX_WEB_FETCHES = 5`
- `MAX_ENGINE_CALLS = 8`

Nested engine invocations share the parent query's budget counters to prevent runaway loops.

---

## 8. Security & Web Safety Model

1. **Prompt Injection Defense:** Web crawls and external text are treated strictly as inert data (`<UNTRUSTED_DOCUMENT_CONTENT>`). System prompts instruct the LLM to never follow instructions embedded in retrieved context.
2. **Execution Trace Sanitization:** The `sanitize_trace_data` filter runs recursively *before* any trace is logged or persisted. It automatically scrubs:
   - Bearer tokens (`[REDACTED]`)
   - API keys (`[REDACTED]`)
   - Database passwords (`[REDACTED]`)
   - Session cookies and auth headers (`[REDACTED]`)
   - Private credentials and environment variables

---

## 9. Adaptive UI Integration

The Next.js frontend (`apps/web/src/app/page.tsx`) renders structured answers using tailored adaptive cards:
- **`Verified Evidence Badge`**: Displays supporting evidence count and Level 1 verification mark.
- **`Refusal Badge`**: Highlights why an inquiry was declined (e.g. `UNKNOWN_ENTITY`, `UNVERIFIED_CURRENT_INFORMATION`).
- **`NavigationCard`**: Step-by-step route directions, estimated walking times, and topological distance disclaimer.
- **`FacultyCard`**: Verified cabin number, department, school, and direct action links.
- **`FeeCard`**: Currency-formatted official fees with academic year labels.
- **`CalendarCard` & `EventCard`**: Verified event milestones, venue locations, and registration URLs.

---

## 10. Phase 5 Comprehensive Evaluation Results

The Phase 5 test suite (`services/ingestion/eval_phase5.py`) executed 32 tests across 10 distinct categories:

| Category | Test ID | Description | Result |
| :--- | :---: | :--- | :---: |
| **A. Single-Engine** | `PH5-01` | Policy query verification via RAG (Level 1 Authority) | **PASSED** |
| | `PH5-02` | Faculty query verification via Faculty Engine | **PASSED** |
| | `PH5-03` | Navigation query verification via Spatial Engine | **PASSED** |
| | `PH5-04` | Fee schedule lookup via Fee Engine | **PASSED** |
| **B. Multi-Engine** | `PH5-05` | Hybrid query: Policy + Faculty coordination | **PASSED** |
| | `PH5-06` | Hybrid query: Placement rules + Placement office route | **PASSED** |
| | `PH5-07` | Hybrid query: Workshop notice + Campus venue route | **PASSED** |
| **C. Temporal** | `PH5-08` | Latest official notice freshness verification | **PASSED** |
| | `PH5-09` | Historical vs Current calendar separation | **PASSED** |
| | `PH5-10` | Publication and effective date provenance check | **PASSED** |
| **D. Conflicts** | `PH5-11` | Contradicting Level 1 sources trigger `UNRESOLVED` | **PASSED** |
| | `PH5-12` | Explicit temporal supersession resolution | **PASSED** |
| | `PH5-13` | Disambiguation: General policy baseline vs recruiter job criteria | **PASSED** |
| **E. Unknown Info** | `PH5-14` | Unknown faculty structured refusal (`UNKNOWN_ENTITY`) | **PASSED** |
| | `PH5-15` | Unknown fee structured refusal (`UNVERIFIED_CURRENT_INFORMATION`) | **PASSED** |
| | `PH5-16` | Unknown room / bunker refusal (`UNKNOWN_ENTITY`) | **PASSED** |
| **F. Injection** | `PH5-17` | Query prompt injection resistance and refusal | **PASSED** |
| | `PH5-18` | Execution trace sensitive credential scrubbing | **PASSED** |
| **G. Community** | `PH5-19` | Level 1 official policy overrides Level 5 community claim | **PASSED** |
| | `PH5-20` | Community report alone treated as unverified lead | **PASSED** |
| **H. Verification** | `PH5-21` | Claim-level granularity removes unsupported assertion | **PASSED** |
| | `PH5-22` | Rejection of unsupported inferred numbers (92% vs 75%) | **PASSED** |
| | `PH5-23` | Strict citation enforcement on factual answers | **PASSED** |
| **I. Web Discovery** | `PH5-24` | University announcement discovery | **PASSED** |
| | `PH5-25` | Web source classification and untrusted tagging | **PASSED** |
| **J. Refusal & Budget** | `PH5-26` | `INSUFFICIENT_EVIDENCE` refusal code compliance | **PASSED** |
| | `PH5-27` | `SOURCE_UNAVAILABLE` refusal code compliance | **PASSED** |
| | `PH5-28` | `AUTHENTICATION_REQUIRED` refusal code compliance | **PASSED** |
| | `PH5-29` | `CONFLICT_UNRESOLVED` refusal code compliance | **PASSED** |
| | `PH5-30` | Tool call budget constants compliance (Max calls: 8) | **PASSED** |
| | `PH5-31` | AnswerContract object structure compliance | **PASSED** |
| | `PH5-32` | Execution trace completeness across lifecycle | **PASSED** |

**Summary:** **32/32 (100.0%) Tests Passed.**

---

## 11. Missing Official Data (Stop Condition Status)

Per Phase 4 & Phase 5 rules, missing data was **never fabricated**:
1. **Faculty Cabin Directory:** Academic leadership verified from signed gazettes; unverified individual faculty cabins cleanly refuse (`UNKNOWN_ENTITY`).
2. **Campus Geodetic CAD Coordinates:** Walking times and topological distances calculated via campus graph; geodetic GPS coordinates flagged as unreleased.
3. **2026-27 Detailed Fee Circular:** Verified programs (e.g. B.Tech CSE tuition) indexed; future unreleased schedules cleanly refuse (`UNVERIFIED_CURRENT_INFORMATION`).
4. **Campus Transportation Timetables:** Bus routes refuse (`SOURCE_UNAVAILABLE`) pending official circular.
5. **Dining Hall Menus:** Daily menus refuse (`SOURCE_UNAVAILABLE`) pending caterer circular.

---

## 12. Recommendations for Phase 6

1. **Authenticated Portal Integrations:** Introduce OAuth2/SAML bridging to allow Level 2 access for authenticated students (individual attendance percentages, internal grade sheets).
2. **CAD / GIS Ingestion Interface:** Integrate official DXF/GeoJSON campus blueprints once released by Estates Directorate.
3. **Maintainer Review Dashboard:** Provide an administrative interface for approving or rejecting community correction reports.
4. **Multi-turn Contextual Memory:** Maintain verification state across extended student dialogue sessions without relaxing claim-level verification rules.

---
**Phase 5 Autonomous Execution Halted.** System is standing by for review.
