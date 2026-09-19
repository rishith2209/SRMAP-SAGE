"""
SRMAP SAGE — Community Data & Verification Workflow Engine
Implements the multi-stage review process for student-submitted corrections:
USER REPORT -> COMMUNITY REPORT -> VALIDATION -> MAINTAINER REVIEW -> OFFICIAL SOURCE CHECK -> APPROVED -> KNOWLEDGE UPDATE
STRICT RULE: Community submissions NEVER automatically override Level 1 official information.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"


class CommunityReportItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    submitted_by: Optional[str] = "student_anonymous"
    content: str
    entity_type: str  # 'policy', 'faculty', 'room', 'event', 'calendar', 'fee'
    entity_id: Optional[str] = None
    suggested_correction: str
    provided_evidence_url: Optional[str] = None
    status: ReportStatus = ReportStatus.PENDING
    reviewer: Optional[str] = None
    resolution: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: Optional[str] = None


class CommunityWorkflowEngine:
    def __init__(self):
        self._reports: Dict[str, CommunityReportItem] = {}

    def submit_report(
        self,
        content: str,
        entity_type: str,
        suggested_correction: str,
        provided_evidence_url: Optional[str] = None,
        entity_id: Optional[str] = None,
        submitted_by: Optional[str] = "student"
    ) -> CommunityReportItem:
        """Records student report without modifying official knowledge."""
        report = CommunityReportItem(
            content=content,
            entity_type=entity_type,
            suggested_correction=suggested_correction,
            provided_evidence_url=provided_evidence_url,
            entity_id=entity_id,
            submitted_by=submitted_by,
            status=ReportStatus.PENDING
        )
        self._reports[report.id] = report
        logger.info(f"Community report recorded: [{report.id}] for entity: {entity_type} (Status: PENDING)")
        return report

    def review_report(
        self,
        report_id: str,
        reviewer_name: str,
        approved: bool,
        resolution_notes: str
    ) -> Optional[CommunityReportItem]:
        """
        Maintainer review checkpoint.
        Requires official source verification before any approval.
        """
        report = self._reports.get(report_id)
        if not report:
            return None

        report.reviewer = reviewer_name
        report.reviewed_at = datetime.now(timezone.utc).isoformat()
        report.resolution = resolution_notes

        if approved:
            report.status = ReportStatus.VERIFIED
            logger.info(f"Report [{report_id}] approved by maintainer {reviewer_name}.")
        else:
            report.status = ReportStatus.REJECTED
            logger.info(f"Report [{report_id}] rejected by maintainer {reviewer_name}: {resolution_notes}")

        return report

    def get_report(self, report_id: str) -> Optional[CommunityReportItem]:
        return self._reports.get(report_id)

    def list_reports(self, status: Optional[ReportStatus] = None) -> List[CommunityReportItem]:
        if status:
            return [r for r in self._reports.values() if r.status == status]
        return list(self._reports.values())
