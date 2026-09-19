# SRMAP SAGE Architecture Deep-Dive

## Architectural Invariants
1. **Evidence-First Inference**:
   The model is strictly prohibited from hallucinating university-specific facts. It functions as a synthesis and explanation engine grounded exclusively in verified retrieved context.
2. **Provenance**:
   Every response that quotes or refers to a university policy, deadline, room, or stat must return an explicit `sources` citation payload.
3. **Poly-Source Partitioning**:
   - Documents are stored in `document_chunks` (vector embedding + tsvector full text).
   - Structured facts (Faculty, Cabins, Departments, Placements) are stored in normalized relational tables.
   - Campus navigation is represented as a directed graph in `campus_nodes` and `campus_edges`.
   - Dynamic real-time announcements are routed to the live web crawler.

## Intent Routing Mechanism
Queries are classified into intents:
- `ACADEMIC_POLICY`: e.g. "What is the attendance policy?" -> Document RAG
- `PROCEDURE_FORM`: e.g. "How to apply for medical leave?" -> Document RAG + Procedure Card
- `FACULTY_LOOKUP`: e.g. "Where is Dr. X's cabin?" -> SQL Faculty Engine + Spatial Graph
- `CAMPUS_DIRECTIONS`: e.g. "Directions from Hostel A to Library" -> Spatial Dijkstra/A* Route
- `PLACEMENT_QUERY`: e.g. "Companies recruiting CSE students" -> SQL Placement Engine + Document Reports
- `CURRENT_EVENT`: e.g. "What events are happening this week?" -> Live Web Engine

## Conflict Detection
When two sources of equal or differing authority levels present conflicting information (e.g. conflicting exam dates across two notices), SAGE:
1. Compares timestamps (`published_at`, `crawled_at`).
2. Evaluates `authority_level` (Level 1: Official University Notices vs Level 2/3: Secondary/Community).
3. If unambiguous, serves the newer authoritative source with an explanatory note.
4. If ambiguous, surfaces both sources transparently: *"Two official notices contain differing dates. The notice from [Date A] states X, while the notice from [Date B] states Y."*
