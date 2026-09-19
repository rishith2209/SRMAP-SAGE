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


class AdaptiveCard(BaseModel):
    card_type: Literal[
        "procedure", "faculty", "department", "navigation",
        "placement", "document", "notice", "event", "calendar", "fee", "policy"
    ]
    payload: Dict[str, Any]


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
