from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# Source & Citation Schemas
class SourceCitation(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    source_type: str
    authority_level: int = Field(ge=1, le=5)
    published_at: Optional[datetime] = None
    crawled_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    snippet: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    freshness_status: Optional[str] = "CURRENT"
    publication_date_str: Optional[str] = None
    effective_date_str: Optional[str] = None


# Adaptive Card UI Schemas
class ProcedureStep(BaseModel):
    step_number: int
    title: str
    description: str
    required_forms: List[str] = []
    approving_authority: Optional[str] = None


class ProcedureCardPayload(BaseModel):
    title: str
    summary: str
    steps: List[ProcedureStep]
    official_form_urls: List[str] = []
    notes: Optional[str] = None


class FacultyCardPayload(BaseModel):
    name: str
    designation: str
    department: str
    school: Optional[str] = None
    cabin_number: Optional[str] = None
    block: Optional[str] = None
    floor: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    research_areas: List[str] = []
    profile_url: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[str] = "VERIFIED"
    verified_at: Optional[str] = None


class DepartmentCardPayload(BaseModel):
    id: str
    name: str
    code: str
    school: Optional[str] = None
    building: Optional[str] = None
    office: Optional[str] = None
    source_id: Optional[str] = None
    verified_at: Optional[str] = None


class RouteSegment(BaseModel):
    instruction: str
    distance_meters: float
    landmarks: List[str] = []


class NavigationCardPayload(BaseModel):
    origin_name: str
    destination_name: str
    total_distance_meters: float
    estimated_walk_minutes: float
    steps: List[RouteSegment]
    is_gps_verified: bool = False
    source_id: Optional[str] = "campus_spatial_topology_v1"


class PlacementStatItem(BaseModel):
    company_name: str
    academic_year: str
    ctc_lpa: Optional[float] = None
    offers_count: int
    eligible_departments: List[str] = []


class PlacementCardPayload(BaseModel):
    title: str
    records: List[PlacementStatItem]
    summary_note: Optional[str] = None


class EventCardPayload(BaseModel):
    event_id: str
    title: str
    description: Optional[str] = None
    start_datetime: str
    end_datetime: Optional[str] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    registration_url: Optional[str] = None
    source_url: Optional[str] = None
    source_id: Optional[str] = "srmap_events_registry"
    status: str = "CURRENT"


class CalendarCardPayload(BaseModel):
    academic_year: str
    semester: str
    event: str
    event_type: str
    start_date: str
    end_date: Optional[str] = None
    status: str = "CURRENT"
    source_id: Optional[str] = None


class FeeCardPayload(BaseModel):
    program: str
    academic_year: str
    fee_type: str
    amount: float
    currency: str = "INR"
    applicable_from: Optional[str] = None
    status: str = "VERIFIED"
    source_id: Optional[str] = None


class PolicyCardPayload(BaseModel):
    title: str
    policy_number: Optional[str] = None
    effective_date: Optional[str] = None
    authority_level: int = 1
    summary: str
    key_rules: List[str] = []
    source_id: str


class ClarificationOption(BaseModel):
    label: str
    sample_query: str


class ClarificationCardPayload(BaseModel):
    prompt: str
    options: List[str]
    category: str
    suggested_queries: List[str] = []


class AdaptiveCard(BaseModel):
    card_type: Literal[
        "procedure", "faculty", "department", "navigation",
        "placement", "document", "notice", "event", "calendar", "fee", "policy", "clarification"
    ]
    payload: Dict[str, Any]


# =============================================================================
# Phase 5: Agentic Evidence Orchestration Schemas
# =============================================================================

class EvidenceItem(BaseModel):
    """
    Standardized evidence unit across all specialized engines.
    NOTE: `confidence` is solely a retrieval/relevance score and NEVER overrides
    authority levels, dates, supersession relationships, or provenance.
    """
    id: str
    source_id: str
    source_type: str
    authority_level: int = Field(ge=1, le=5)
    title: str
    url: Optional[str] = None
    page: Optional[int] = None
    excerpt: str
    published_at: Optional[str] = None
    verified_at: Optional[str] = None
    freshness_status: str = "CURRENT"
    confidence: float = Field(default=1.0, description="Retrieval/relevance score ONLY, does not signify truth")
    engine: str
    content_hash: str
    domain: Optional[str] = None
    entity_scope: Optional[str] = None


class QueryPlan(BaseModel):
    query: str
    intents: List[str] = []
    engines: List[str] = []
    requires_current_data: bool = False
    requires_multiple_sources: bool = False
    verification_required: bool = True
    max_iterations: int = 3
    tool_budget: Dict[str, int] = Field(
        default_factory=lambda: {
            "max_retrieval_iterations": 3,
            "max_web_fetches": 5,
            "max_engine_calls": 8
        }
    )


class ConflictAssessment(BaseModel):
    conflict_type: Literal[
        "NO_CONFLICT",
        "TEMPORAL_UPDATE",
        "AUTHORITY_CONFLICT",
        "CONTENT_CONFLICT",
        "UNRESOLVED",
        "TEMPORAL_RELATIONSHIP_UNKNOWN"
    ] = "NO_CONFLICT"
    has_conflict: bool = False
    superseding_source_id: Optional[str] = None
    explanation: Optional[str] = None
    applicable_claims: List[str] = []


class RefusalReason(BaseModel):
    code: Literal[
        "INSUFFICIENT_EVIDENCE",
        "SOURCE_UNAVAILABLE",
        "AUTHENTICATION_REQUIRED",
        "CONFLICT_UNRESOLVED",
        "OUTDATED_INFORMATION",
        "UNKNOWN_ENTITY",
        "UNVERIFIED_CURRENT_INFORMATION"
    ]
    message: str
    required_evidence: Optional[str] = None


class ClaimVerificationResult(BaseModel):
    claim_text: str
    supported: bool
    supporting_evidence_ids: List[str] = []
    confidence_note: Optional[str] = None


class ExecutionStep(BaseModel):
    step_name: str
    timestamp: str
    details: Dict[str, Any] = {}
    duration_ms: float = 0.0


class ExecutionTrace(BaseModel):
    query: str
    steps: List[ExecutionStep] = []
    total_engine_calls: int = 0
    total_web_fetches: int = 0
    total_iterations: int = 0


class AnswerContract(BaseModel):
    answer: str
    evidence: List[EvidenceItem] = []
    sources: List[SourceCitation] = []
    freshness: str = "CURRENT"
    caveats: List[str] = []
    refusal_reason: Optional[RefusalReason] = None
    verification_status: Literal["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "REFUSED"] = "VERIFIED"
    trace: Optional[Dict[str, Any]] = None


# Chat & Query Schemas
class ChatQueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    session_id: Optional[str] = None
    history: List[Dict[str, str]] = []


class ChatQueryResponse(BaseModel):
    answer: str
    is_fallback: bool = False
    intent: str
    confidence: float
    sources: List[SourceCitation] = []
    adaptive_card: Optional[AdaptiveCard] = None
    conflict_detected: bool = False
    conflict_note: Optional[str] = None
    # Phase 5 Additions
    verification_status: Optional[str] = "VERIFIED"
    evidence: List[EvidenceItem] = []
    refusal_code: Optional[str] = None
    refusal_required_evidence: Optional[str] = None
    execution_trace: Optional[Dict[str, Any]] = None
    contract: Optional[AnswerContract] = None
    # Phase 6 Additions
    is_clarification: bool = False


# Community Feedback Schemas
class CommunityReportRequest(BaseModel):
    query_text: str
    generated_answer: str
    category: str
    report_reason: str
    suggested_correction: Optional[str] = None
    provided_evidence_url: Optional[str] = None


class CommunityReportResponse(BaseModel):
    id: str
    status: str
    github_issue_number: Optional[int] = None
    message: str


# =============================================================================
# Phase 6: Admin & Health Monitoring Schemas
# =============================================================================

class AdminHealthMetrics(BaseModel):
    status: str
    service: str = "srmap-sage-api"
    version: str = "1.0.0"
    database_connected: bool
    total_documents: int
    total_chunks: int
    total_sources: int
    total_faculty: int
    total_departments: int
    total_events: int
    total_calendar_milestones: int
    total_fee_schedules: int
    total_spatial_nodes: int
    pending_community_reports: int
    active_conflicts: int
    freshness_summary: Dict[str, int]


class AdminSourceHealthItem(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None
    source_type: str
    authority_level: int
    freshness_status: str
    last_verified_at: Optional[str] = None
    chunk_count: int = 0
    error_count: int = 0


class AdminDocumentSummary(BaseModel):
    source_id: str
    title: str
    policy_number: Optional[str] = None
    policy_date: Optional[str] = None
    authority_level: int
    chunks_count: int
    sha256: Optional[str] = None
    freshness_status: str = "CURRENT"


class AdminReportItem(BaseModel):
    id: str
    query_text: str
    generated_answer: str
    category: str
    report_reason: str
    suggested_correction: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    github_issue_number: Optional[int] = None


