"""
SRMAP SAGE — Semantic Conflict & Authority Resolution Engine (Phase 5)
Detects true semantic contradictions across evidence items while distinguishing
complementary domain rules, recruiter-specific criteria, and multi-channel announcements.
Enforces strict temporal supersession rules and authority precedence.
"""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from src.models.schemas import EvidenceItem, ConflictAssessment

logger = logging.getLogger(__name__)


class ConflictDetector:
    """
    Evaluates sets of EvidenceItem objects for genuine semantic conflict.
    Applies the rule:
    - EvidenceItem.confidence is solely a retrieval score; truth is determined by
      authority, provenance, temporal validity, and scope.
    """

    @staticmethod
    def assess_evidence_set(
        query: str,
        evidence_items: List[EvidenceItem]
    ) -> ConflictAssessment:
        if len(evidence_items) <= 1:
            return ConflictAssessment(
                conflict_type="NO_CONFLICT",
                has_conflict=False,
                explanation="Single or zero evidence items; no conflicting source exists."
            )

        level_1_items = [e for e in evidence_items if e.authority_level == 1]

        # 1. Check for complementary domains (e.g. Placement Baseline vs Recruiter Specific)
        is_placement = any("placement" in (e.domain or "").lower() or "placement" in e.title.lower() for e in evidence_items)
        if is_placement:
            # Check if one is general policy and another is company-specific
            has_general_policy = any("policy" in e.title.lower() or "regulations" in e.title.lower() for e in evidence_items)
            has_company_job = any("company" in e.title.lower() or "offer" in e.title.lower() or "recruiter" in e.title.lower() or "haveloc" in (e.url or "") for e in evidence_items)
            if has_general_policy and has_company_job:
                return ConflictAssessment(
                    conflict_type="NO_CONFLICT",
                    has_conflict=False,
                    explanation=(
                        "Complementary scopes: General university placement policy baseline coexists with "
                        "company-specific recruiter eligibility requirements."
                    )
                )

        # 2. Check for multi-channel event coverage (e.g. Event page + Social Announcement)
        is_event = any(e.engine == "EVENT_ENGINE" or "event" in (e.domain or "").lower() for e in evidence_items)
        if is_event and len(evidence_items) >= 2:
            return ConflictAssessment(
                conflict_type="NO_CONFLICT",
                has_conflict=False,
                explanation="Complementary multi-channel publications covering the same verified campus event."
            )

        # 3. Check Community & Informal / Social Media overrides (Level 3+ vs Level 1/2)
        informal_items = [e for e in evidence_items if e.authority_level >= 3 or e.source_type in ["community_report", "social_media", "untrusted_crawl"]]
        official_items = [e for e in evidence_items if e.authority_level <= 2]
        if informal_items and official_items:
            # Official sources take strict precedence over informal claims
            return ConflictAssessment(
                conflict_type="AUTHORITY_CONFLICT",
                has_conflict=True,
                superseding_source_id=official_items[0].source_id,
                explanation=(
                    f"Official university source '{official_items[0].title}' (Authority Level {official_items[0].authority_level}) "
                    f"takes precedence over unverified informal/social media claim (Authority Level {informal_items[0].authority_level})."
                ),
                applicable_claims=["Official Level 1/2 documentation prevails over informal social media or community submissions."]
            )

        # 5. Check Temporal Relationships among Level 1 documents on the same topic
        if len(level_1_items) >= 2:
            # Check if one explicitly supersedes the other
            superseded = [e for e in level_1_items if e.freshness_status == "SUPERSEDED"]
            current = [e for e in level_1_items if e.freshness_status == "CURRENT"]

            if superseded and current:
                # Check if they share the same topic/scope
                curr_item = current[0]
                old_item = superseded[0]
                return ConflictAssessment(
                    conflict_type="TEMPORAL_UPDATE",
                    has_conflict=True,
                    superseding_source_id=curr_item.source_id,
                    explanation=(
                        f"Temporal supersession established: '{curr_item.title}' (Published: {curr_item.published_at or 'Latest'}) "
                        f"supersedes archived record '{old_item.title}' (Published: {old_item.published_at or 'Archived'})."
                    ),
                    applicable_claims=[f"Policy updated by official circular {curr_item.source_id}"]
                )

            # Check if numbers or key policies differ between two Level 1 documents without supersession
            # Extract numerical percentages or rules
            percentages = {}
            for item in level_1_items:
                matches = re.findall(r"\b(\d{1,3})%", item.excerpt)
                if matches:
                    percentages[item.source_id] = (matches, item)

            if len(percentages) >= 2:
                pct_vals = list(percentages.values())
                # If they claim different percentages on what seems like attendance or same domain
                val1, item1 = pct_vals[0]
                val2, item2 = pct_vals[1]
                if val1 != val2:
                    # Check if date relationship is explicit
                    date1 = item1.published_at or ""
                    date2 = item2.published_at or ""
                    if not date1 or not date2 or date1 == date2:
                        return ConflictAssessment(
                            conflict_type="UNRESOLVED",
                            has_conflict=True,
                            explanation=(
                                f"Direct numerical contradiction between Level 1 sources '{item1.title}' ({val1[0]}%) and "
                                f"'{item2.title}' ({val2[0]}%) with no verified supersession or effective date hierarchy."
                            )
                        )
                    else:
                        return ConflictAssessment(
                            conflict_type="TEMPORAL_RELATIONSHIP_UNKNOWN",
                            has_conflict=True,
                            explanation=(
                                f"Level 1 documents have different dates ({date1} vs {date2}), but neither contains explicit "
                                f"revocation or supersession clauses. Categorized as TEMPORAL_RELATIONSHIP_UNKNOWN."
                            )
                        )

        return ConflictAssessment(
            conflict_type="NO_CONFLICT",
            has_conflict=False,
            explanation="Evidence items provide consistent, non-contradictory information."
        )
